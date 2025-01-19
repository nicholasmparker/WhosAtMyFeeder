# ML Models for Image Processing

## Overview
The system uses two local ML models for image quality assessment and enhancement:
1. TF-IQA: Quality assessment model
2. RealESRGAN: Image enhancement model

## First-Time Setup

1. Download the models:
```bash
# Make script executable if needed
chmod +x download_models.sh

# Run the download script
./download_models.sh
```

This will:
- Create Docker volumes for models and test data
- Download RealESRGAN model
- Create TF-IQA model
- Download test images
- Set up proper permissions

2. Start the application:
```bash
# Start the container
docker-compose up -d

# Verify models
docker exec whosatmyfeeder python setup_models.py
```

## Model Details

### TF-IQA (Quality Assessment)
- Purpose: Assess image quality metrics
- Metrics:
  * Clarity (focus, resolution)
  * Composition (framing, rule of thirds)
  * Overall quality score
- Location: Docker volume: whosatmyfeeder_ml_models/quality/tf-iqa-model/model.h5

### RealESRGAN (Enhancement)
- Purpose: Enhance low-quality images
- Features:
  * 4x upscaling
  * Noise reduction
  * Detail enhancement
- Location: Docker volume: whosatmyfeeder_ml_models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth

## Docker Integration

Models are stored in persistent volumes:
```yaml
volumes:
  ml_models:
    name: whosatmyfeeder_ml_models
  test_data:
    name: whosatmyfeeder_test_data
```

Volume mounts:
```yaml
volumes:
  - ml_models:/app/models
  - test_data:/app/test_data
```

## Testing

1. Manual Testing:
```bash
docker exec whosatmyfeeder python setup_models.py
```
This will test both models with the downloaded test image.

2. Integration Testing:
```bash
docker exec whosatmyfeeder python debug_vision_analysis.py
```
Tests the models with actual detection images.

## Model Usage

### Quality Assessment
```python
from image_processing import TFIQAModel

model = TFIQAModel('models/quality/tf-iqa-model/model.h5')
scores = model.assess_quality(image)
print(scores)  # {'clarity': 0.85, 'composition': 0.75, 'overall': 0.80}
```

### Image Enhancement
```python
from image_processing import RealESRGANEnhancer

enhancer = RealESRGANEnhancer('models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth')
enhanced_image = enhancer.enhance(image)
```

## Configuration

Settings in config.yml:
```yaml
image_processing:
  local_models:
    quality_assessment:
      type: "tf-iqa"
      model_path: "models/quality/tf-iqa-model/model.h5"
      threshold: 0.7
    enhancement:
      type: "real-esrgan"
      model_path: "models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth"
      scale: 4
```

## Troubleshooting

1. Model Loading Issues
   - Run download_models.sh again
   - Check volume mounts: `docker volume ls`
   - Verify model files: `docker exec whosatmyfeeder ls -R /app/models`

2. Memory Issues
   - Check Docker memory limits
   - Monitor container resources
   - Use CPU fallback if needed

3. Volume Issues
   - Inspect volumes: `docker volume inspect whosatmyfeeder_ml_models`
   - Check permissions
   - Verify mount points

## Performance Notes

1. GPU Acceleration
   - RealESRGAN uses GPU if available
   - Falls back to CPU if needed
   - CUDA toolkit recommended

2. Memory Usage
   - TF-IQA: ~500MB RAM
   - RealESRGAN: ~2GB RAM/VRAM
   - Batch processing available

3. Processing Times
   - Quality Assessment: ~100ms/image
   - Enhancement: ~1-2s/image (CPU), ~200ms/image (GPU)

## Data Persistence

1. Model Storage
   - Models stored in Docker volume
   - Survives container restarts/rebuilds
   - Shared between container instances

2. Test Data
   - Sample images in separate volume
   - Results persist between runs
   - Easy to share test cases

3. Backup
   ```bash
   # Backup volumes
   docker run --rm -v whosatmyfeeder_ml_models:/models \
     -v $(pwd):/backup alpine tar czf /backup/models.tar.gz /models

   # Restore volumes
   docker run --rm -v whosatmyfeeder_ml_models:/models \
     -v $(pwd):/backup alpine tar xzf /backup/models.tar.gz -C /
   ```

## Updating Models

1. To update models:
```bash
# Remove existing volumes
docker volume rm whosatmyfeeder_ml_models whosatmyfeeder_test_data

# Re-run download script
./download_models.sh
```

2. Or update individual models:
```bash
# Copy new model file to volume
docker cp new_model.pth whosatmyfeeder:/app/models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth

# Test new model
docker exec whosatmyfeeder python setup_models.py
