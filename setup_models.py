#!/usr/bin/env python3
"""
Setup script for local ML models (TF-IQA and RealESRGAN).
Downloads and verifies model files, tests functionality.
"""
import os
import sys
from pathlib import Path
import requests
import tensorflow as tf
import torch
from basicsr.utils.download_util import load_file_from_url
import cv2
import numpy as np
from tqdm import tqdm
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_file(url: str, dest_path: str, desc: str = "Downloading") -> None:
    """Download file with progress bar."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    with open(dest_path, 'wb') as f, tqdm(
        desc=desc,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)

def setup_tf_iqa():
    """Setup TF-IQA model."""
    print("\nSetting up TF-IQA model...")
    
    models_dir = Path('models')
    tf_iqa_dir = models_dir / 'quality' / 'tf-iqa-model'
    tf_iqa_dir.mkdir(parents=True, exist_ok=True)
    
    # For now, create a simple CNN model since the actual TF-IQA weights aren't publicly available
    print("Creating basic quality assessment model...")
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(224, 224, 3)),
        tf.keras.layers.Conv2D(32, 3, activation='relu'),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(64, 3, activation='relu'),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(64, 3, activation='relu'),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    model_path = tf_iqa_dir / 'model.h5'
    model.save(model_path)
    print(f"Basic quality model saved to: {model_path}")
    
    return model_path

def setup_real_esrgan():
    """Setup RealESRGAN model."""
    print("\nSetting up RealESRGAN model...")
    
    models_dir = Path('models')
    esrgan_dir = models_dir / 'enhancement' / 'RealESRGAN_x4plus'
    esrgan_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = esrgan_dir / 'RealESRGAN_x4plus.pth'
    if not model_path.exists():
        print("Downloading RealESRGAN weights...")
        load_file_from_url(
            'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
            str(model_path)
        )
    
    return model_path

def test_models(test_image_path: str = None):
    """Test both models with a sample image."""
    print("\nTesting models...")
    
    # Get test image
    if test_image_path is None or not os.path.exists(test_image_path):
        print("No test image provided, downloading sample...")
        test_dir = Path('test_data')
        test_dir.mkdir(exist_ok=True)
        test_image_path = test_dir / 'test_bird.jpg'
        if not test_image_path.exists():
            # Download a sample bird image
            url = "https://raw.githubusercontent.com/mmcc-xx/WhosAtMyFeeder/master/example_images/cardinal.jpg"
            download_file(url, str(test_image_path), "Downloading test image")
    
    # Load and preprocess image
    image = cv2.imread(str(test_image_path))
    if image is None:
        print("Error: Could not load test image")
        return False
    
    try:
        # Test TF-IQA
        print("\nTesting TF-IQA model...")
        from image_processing import TFIQAModel
        tf_iqa = TFIQAModel('models/quality/tf-iqa-model/model.h5')
        quality_scores = tf_iqa.assess_quality(image)
        print(f"Quality scores: {quality_scores}")
        
        # Test RealESRGAN
        print("\nTesting RealESRGAN...")
        from image_processing import RealESRGANEnhancer
        enhancer = RealESRGANEnhancer('models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth')
        enhanced = enhancer.enhance(image)
        
        # Save enhanced image
        output_path = Path('test_data') / 'enhanced_test_bird.jpg'
        cv2.imwrite(str(output_path), enhanced)
        print(f"Enhanced image saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error testing models: {e}")
        return False

def update_config():
    """Update config.yml with correct model paths."""
    config_dir = Path('config')
    config_path = config_dir / 'config.yml'
    
    if not config_path.exists():
        print("No config.yml found, copying from example...")
        example_path = config_dir / 'example.config.yml'
        if not example_path.exists():
            print("Error: example.config.yml not found")
            return
        
        with open(example_path) as f:
            config = yaml.safe_load(f)
    else:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    
    # Update model paths
    config['image_processing']['local_models']['quality_assessment']['model_path'] = \
        'models/quality/tf-iqa-model/model.h5'
    config['image_processing']['local_models']['enhancement']['model_path'] = \
        'models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth'
    
    with open(config_path, 'w') as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    
    print(f"\nUpdated model paths in: {config_path}")

if __name__ == "__main__":
    print("Setting up ML models for image processing")
    print("=" * 50)
    
    # Setup models
    tf_iqa_path = setup_tf_iqa()
    esrgan_path = setup_real_esrgan()
    
    # Update config
    update_config()
    
    # Test models
    if test_models():
        print("\nModel setup and testing completed successfully!")
        print("\nYou can now use the image processing features.")
    else:
        print("\nError: Model testing failed")
        print("Please check the error messages above")
