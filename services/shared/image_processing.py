import os
import cv2
import numpy as np
import requests
# Optional TensorFlow import
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import yaml
import logging
from pathlib import Path
import json
import sqlite3
import subprocess
from skimage import exposure, restoration
from skimage.metrics import structural_similarity as ssim

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityAssessmentModel(ABC):
    @abstractmethod
    def assess_quality(self, image: np.ndarray) -> Dict[str, float]:
        """Assess image quality and return scores."""
        pass

class BasicQualityModel(QualityAssessmentModel):
    """Basic quality assessment using OpenCV."""
    
    def assess_quality(self, image: np.ndarray) -> Dict[str, float]:
        """Assess image quality using basic metrics."""
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate clarity score using Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        clarity_score = min(np.var(laplacian) / 500.0, 1.0)  # Normalize
        
        # Calculate composition score using rule of thirds
        height, width = image.shape[:2]
        edges = cv2.Canny(gray, 100, 200)
        
        # Rule of thirds points
        third_h = height // 3
        third_w = width // 3
        
        # Check edge density around rule of thirds intersections
        thirds_score = 0
        for i in [third_h, 2*third_h]:
            for j in [third_w, 2*third_w]:
                region = edges[i-20:i+20, j-20:j+20]
                thirds_score += np.sum(region) / 255
        
        # Normalize composition score
        max_possible_score = 40 * 40 * 4
        composition_score = min(thirds_score / max_possible_score, 1.0)
        
        return {
            'clarity': clarity_score,
            'composition': composition_score,
            'overall': (clarity_score * 0.6 + composition_score * 0.4)
        }

if TENSORFLOW_AVAILABLE:
    class TFIQAModel(QualityAssessmentModel):
        def __init__(self, model_path: str):
            """Initialize TF-IQA model for image quality assessment."""
            self.model = tf.keras.models.load_model(model_path)
            self.input_size = (224, 224)
        
        def assess_quality(self, image: np.ndarray) -> Dict[str, float]:
            """Assess image quality using TF-IQA model."""
            # Preprocess image
            resized = cv2.resize(image, self.input_size)
            normalized = resized.astype(np.float32) / 255.0
            batch = np.expand_dims(normalized, axis=0)
            
            # Get model prediction
            quality_score = float(self.model.predict(batch)[0])
            
            # Calculate composition score
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            
            height, width = image.shape[:2]
            third_h = height // 3
            third_w = width // 3
            
            thirds_score = 0
            for i in [third_h, 2*third_h]:
                for j in [third_w, 2*third_w]:
                    region = edges[i-20:i+20, j-20:j+20]
                    thirds_score += np.sum(region) / 255
            
            composition_score = min(thirds_score / (40 * 40 * 4), 1.0)
            
            return {
                'clarity': quality_score,
                'composition': composition_score,
                'overall': (quality_score * 0.6 + composition_score * 0.4)
            }

class ImageEnhancer(ABC):
    @abstractmethod
    def enhance(self, image: np.ndarray) -> np.ndarray:
        """Enhance the input image."""
        pass

class RealESRGANEnhancer(ImageEnhancer):
    def __init__(self):
        """Initialize RealESRGAN enhancer."""
        # Ensure input/output directories exist
        os.makedirs('input', exist_ok=True)
        os.makedirs('output', exist_ok=True)
    
    def enhance(self, image: np.ndarray) -> np.ndarray:
        """Enhance image using RealESRGAN."""
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_filename = f"image_{timestamp}.png"
        output_filename = f"image_{timestamp}_out.png"
        input_path = os.path.join('input', input_filename)
        output_path = os.path.join('output', output_filename)
        
        try:
            # Save input image
            cv2.imwrite(input_path, image)
            logger.info(f"Saved input image to: {input_path}")
            
            # Run RealESRGAN docker command
            cmd = [
                'docker', 'run', '--rm',
                '-v', f"{os.path.abspath('input')}:/app/input",
                '-v', f"{os.path.abspath('output')}:/app/output",
                'docker.io/kociolek/real-esrgan'  # GPU not required
            ]
            
            logger.info("Running RealESRGAN command...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                logger.info(f"RealESRGAN output: {result.stdout}")
            if result.stderr:
                logger.warning(f"RealESRGAN stderr: {result.stderr}")
                
            if result.returncode != 0:
                logger.error(f"RealESRGAN failed with return code: {result.returncode}")
                return image
            
            # Read enhanced image
            if not os.path.exists(output_path):
                logger.error(f"Enhanced image not found at: {output_path}")
                return image
                
            enhanced = cv2.imread(output_path)
            if enhanced is None:
                logger.error("Failed to read enhanced image")
                return image
            
            logger.info("Enhancement completed successfully")
            return enhanced
            
        except Exception as e:
            logger.error(f"Error using RealESRGAN: {str(e)}")
            return image
            
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.remove(input_path)
                logger.debug(f"Cleaned up input file: {input_path}")
            if os.path.exists(output_path):
                os.remove(output_path)
                logger.debug(f"Cleaned up output file: {output_path}")

class ImageProcessingService:
    def __init__(self, config_path: str = 'config/config.yml'):
        """Initialize the image processing service."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['image_processing']
        
        # Initialize models
        self.quality_model = self._init_quality_model()
        self.enhancer = self._init_enhancer()
        
        # Create storage directories
        os.makedirs(self.config['storage']['enhanced_images_path'], exist_ok=True)
        os.makedirs(self.config['storage']['cache_path'], exist_ok=True)
    
    def _init_quality_model(self) -> QualityAssessmentModel:
        """Initialize quality assessment model based on config."""
        try:
            model_config = self.config['local_models']['quality_assessment']
            if model_config['type'] == 'tf-iqa' and TENSORFLOW_AVAILABLE:
                model_path = model_config['model_path']
                if os.path.exists(model_path):
                    return TFIQAModel(model_path)
                else:
                    logger.warning(f"TF-IQA model not found at {model_path}, falling back to basic model")
            else:
                logger.info("Using basic quality assessment model")
        except Exception as e:
            logger.warning(f"Error initializing TF-IQA model: {e}, falling back to basic model")
        
        return BasicQualityModel()
    
    def _init_enhancer(self) -> ImageEnhancer:
        """Initialize image enhancement model based on config."""
        enhancer_config = self.config['local_models']['enhancement']
        if enhancer_config['type'] == 'real-esrgan':
            return RealESRGANEnhancer()
        else:
            raise ValueError(f"Unsupported enhancer type: {enhancer_config['type']}")
    
    def _get_enhanced_path(self, original_path: str, is_thumbnail: bool = False) -> str:
        """Generate path for enhanced image."""
        # Extract event ID from path - handle both URL and local paths
        if 'http' in original_path:
            # URL path like http://frigate/api/events/event123/snapshot.jpg
            event_id = original_path.split('/events/')[-1].split('/')[0]
        else:
            # Local path
            event_id = original_path.split('/')[-2]
            
        logger.info(f"Extracted event ID: {event_id} from path: {original_path}")
        
        # Create event directory
        event_dir = os.path.join(
            self.config['storage']['enhanced_images_path'],
            event_id
        )
        os.makedirs(event_dir, exist_ok=True)
        
        # Return appropriate path
        if is_thumbnail:
            return os.path.join(event_dir, 'thumbnail_enhanced.jpg')
        return os.path.join(event_dir, 'snapshot_enhanced.jpg')
    
    def process_image(self, image_path: str) -> Dict:
        """Process an image through the quality assessment and enhancement pipeline."""
        logger.info(f"Processing image: {image_path}")
        
        # Read image from URL
        try:
            response = requests.get(image_path, stream=True)
            response.raise_for_status()
            
            # Convert response content to numpy array
            nparr = np.frombuffer(response.content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError(f"Could not decode image from: {image_path}")
        except Exception as e:
            raise ValueError(f"Could not read image from {image_path}: {str(e)}")
        
        # Assess quality
        quality_scores = self.quality_model.assess_quality(image)
        logger.info(f"Quality scores: {quality_scores}")
        
        result = {
            'original_path': image_path,
            'quality_scores': quality_scores,
            'enhanced': False,
            'enhanced_path': None
        }
        
        # Enhance if needed
        if quality_scores['clarity'] < self.config['local_models']['quality_assessment']['threshold']:
            logger.info("Image quality below threshold, enhancing...")
            enhanced_image = self.enhancer.enhance(image)
            # Save enhanced snapshot
            enhanced_path = self._get_enhanced_path(image_path)
            cv2.imwrite(enhanced_path, enhanced_image)
            
            # Create and save enhanced thumbnail
            thumbnail_size = (320, 240)
            enhanced_thumbnail = cv2.resize(enhanced_image, thumbnail_size)
            thumbnail_path = self._get_enhanced_path(image_path, is_thumbnail=True)
            cv2.imwrite(thumbnail_path, enhanced_thumbnail)
            
            # Assess enhanced image quality
            enhanced_scores = self.quality_model.assess_quality(enhanced_image)
            logger.info(f"Enhanced quality scores: {enhanced_scores}")
            
            result.update({
                'enhanced': True,
                'enhanced_path': enhanced_path,
                'enhanced_quality_scores': enhanced_scores
            })
        
        # Cache results
        self._cache_results(image_path, result)
        
        return result
    
    def _cache_results(self, image_path: str, result: Dict) -> None:
        """Cache processing results."""
        cache_path = os.path.join(
            self.config['storage']['cache_path'],
            f"{Path(image_path).stem}_analysis.json"
        )
        
        with open(cache_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    def get_cached_results(self, image_path: str) -> Optional[Dict]:
        """Retrieve cached results if available."""
        cache_path = os.path.join(
            self.config['storage']['cache_path'],
            f"{Path(image_path).stem}_analysis.json"
        )
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
        
        return None

# Database integration
def update_image_quality_table(db_path: str, detection_id: int, quality_data: Dict) -> None:
    """Update image quality metrics in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get the frigate_event for this detection
        cursor.execute("""
            SELECT frigate_event
            FROM detections
            WHERE id = ?
        """, (detection_id,))
        result = cursor.fetchone()
        if not result:
            logger.error(f"No detection found for ID {detection_id}")
            return
            
        frigate_event = result[0]
        enhanced_path = os.path.join(
            quality_data.get('enhanced_path', '').split('data/')[-1]
            if quality_data.get('enhanced_path')
            else ''
        )
        enhanced_thumbnail_path = os.path.join(
            'data/enhanced_images',
            frigate_event,
            'thumbnail_enhanced.jpg'
        )
        
        cursor.execute("""
            INSERT OR REPLACE INTO image_quality (
                detection_id,
                clarity_score,
                composition_score,
                behavior_tags,
                visibility_score,
                enhanced_path,
                enhanced_thumbnail_path,
                enhancement_status,
                quality_improvement,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            detection_id,
            quality_data['quality_scores']['clarity'],
            quality_data['quality_scores']['composition'],
            json.dumps([]),  # Empty behavior tags for now
            quality_data['quality_scores']['overall'],
            enhanced_path if quality_data.get('enhanced') else None,
            enhanced_thumbnail_path if quality_data.get('enhanced') else None,
            'completed' if quality_data.get('enhanced') else None,
            (quality_data.get('enhanced_quality_scores', {}).get('overall', 0) - 
             quality_data['quality_scores']['overall']) if quality_data.get('enhanced') else None
        ))
        
        conn.commit()
    finally:
        conn.close()
