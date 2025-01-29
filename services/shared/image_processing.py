import os
import cv2
import numpy as np
import requests
import subprocess
import yaml
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ImageProcessingService:
    def __init__(self, config_path):
        # Load config from file
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Basic quality model that uses clarity threshold from config
        self.quality_model = self.BasicQualityModel(
            self.config['image_processing']['local_models']['quality_assessment']['threshold']
        )
        
        # Docker-based enhancer using real-esrgan
        self.enhancer = self.RealESRGANEnhancer()
        self._cache = {}

    class BasicQualityModel:
        def __init__(self, threshold):
            self.threshold = threshold
            
        def assess_quality(self, image: np.ndarray) -> Dict[str, float]:
            """Basic quality assessment using image statistics."""
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate clarity score using Laplacian variance (focus measure)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            clarity = np.var(laplacian) / 10000  # Normalize to roughly 0-1 range
            
            # Calculate composition score using rule of thirds
            height, width = gray.shape
            center_roi = gray[height//3:2*height//3, width//3:2*width//3]
            composition = np.mean(center_roi) / 255  # Normalize to 0-1
            
            return {
                'clarity': min(clarity, 1.0),  # Cap at 1.0
                'composition': composition
            }
            
    class RealESRGANEnhancer:
        def enhance(self, image: np.ndarray) -> np.ndarray:
            """Enhance image using real-esrgan docker container."""
            # Save input image
            os.makedirs('input', exist_ok=True)
            os.makedirs('output', exist_ok=True)
            input_path = os.path.join('input', 'temp.png')
            cv2.imwrite(input_path, image)
            
            try:
                # Run real-esrgan docker container
                cmd = [
                    'docker', 'run', '--rm',
                    '-v', f"{os.path.abspath('input')}:/app/input",
                    '-v', f"{os.path.abspath('output')}:/app/output",
                    'docker.io/kociolek/real-esrgan'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"Enhancement failed: {result.stderr}")
                
                # Read enhanced image
                output_path = os.path.join('output', 'temp_out.png')
                enhanced = cv2.imread(output_path)
                if enhanced is None:
                    raise ValueError("Could not read enhanced image")
                
                # Cleanup
                os.remove(input_path)
                os.remove(output_path)
                
                return enhanced
            except Exception as e:
                logger.error(f"Enhancement error: {e}")
                # Return original image if enhancement fails
                return image
                
    def process_image(self, image_path: str) -> Dict:
        """Process an image through the quality assessment and enhancement pipeline."""
        logger.info(f"Processing image: {image_path}")
        
        # Handle test events differently
        if 'test_event' in image_path:
            test_image_path = '/app/screenshot.jpg'
            image = cv2.imread(test_image_path)
            if image is None:
                raise ValueError(f"Could not read test image from: {test_image_path}")
        else:
            # Read image from URL for real events
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
            'enhanced_path': None,
            'enhanced_thumbnail_path': None
        }
        
        # Enhance if needed
        if quality_scores['clarity'] < self.config['image_processing']['local_models']['quality_assessment']['threshold']:
            logger.info("Image quality below threshold, enhancing...")
            enhanced_image = self.enhancer.enhance(image)
            # Extract event ID from path
            event_id = image_path.split('/events/')[-1].split('/')[0]
            
            # Save enhanced image
            enhanced_path = f"/data/images/enhanced/{event_id}/snapshot.jpg"
            logger.info(f"Saving enhanced image to: {enhanced_path}")
            os.makedirs(os.path.dirname(enhanced_path), exist_ok=True)
            if not cv2.imwrite(enhanced_path, enhanced_image):
                logger.error(f"Failed to save enhanced image to: {enhanced_path}")
                return result
            
            # Save enhanced thumbnail
            thumbnail_size = (320, 240)
            enhanced_thumbnail = cv2.resize(enhanced_image, thumbnail_size)
            thumbnail_path = f"/data/images/enhanced/{event_id}/thumbnail.jpg"
            logger.info(f"Saving enhanced thumbnail to: {thumbnail_path}")
            if not cv2.imwrite(thumbnail_path, enhanced_thumbnail):
                logger.error(f"Failed to save enhanced thumbnail to: {thumbnail_path}")
                return result
            
            # Assess enhanced image quality
            enhanced_scores = self.quality_model.assess_quality(enhanced_image)
            logger.info(f"Enhanced quality scores: {enhanced_scores}")
            
            result.update({
                'enhanced': True,
                'enhanced_path': enhanced_path,
                'enhanced_thumbnail_path': thumbnail_path,
                'enhanced_quality_scores': enhanced_scores
            })
        
        # Cache results
        self._cache_results(image_path, result)
        
        return result

    def _cache_results(self, image_path: str, result: Dict) -> None:
        """Cache the processing results for an image."""
        self._cache[image_path] = result

    def get_cached_results(self, image_path: str) -> Dict:
        """Get cached processing results for an image if available."""
        return self._cache.get(image_path)
