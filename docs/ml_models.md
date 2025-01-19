# ML Models for Image Processing

## Overview
The system uses two local ML models for image quality assessment and enhancement:
1. TF-IQA: Quality assessment model
2. RealESRGAN: Image enhancement model

## Setup Process

1. Run the setup script:
```bash
python setup_models.py
```

This will:
- Download/create necessary model files
- Test models with sample images
- Update configuration paths

## Model Details

### TF-IQA (Quality Assessment)
- Purpose: Assess image quality metrics
- Metrics:
  * Clarity (focus, resolution)
  * Composition (framing, rule of thirds)
  * Overall quality score
- Location: models/quality/tf-iqa-model/model.h5

### RealESRGAN (Enhancement)
- Purpose: Enhance low-quality images
- Features:
  * 4x upscaling
  * Noise reduction
  * Detail enhancement
- Location: models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth

## Docker Integration

The models are automatically set up in the Docker container:
```dockerfile
RUN mkdir -p \
    /app/models/quality/tf-iqa-model \
    /app/models/enhancement/RealESRGAN_x4plus
RUN python setup_models.py
```

## Testing

1. Manual Testing:
```bash
python setup_models.py
```
This will download a sample bird image and test both models.

2. Integration Testing:
```bash
python debug_vision_analysis.py
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
   - Check model files exist
   - Verify paths in config.yml
   - Check GPU/CUDA availability

2. Memory Issues
   - Adjust batch sizes
   - Monitor GPU memory
   - Use CPU fallback if needed

3. Image Processing Errors
   - Check image format/size
   - Verify OpenCV installation
   - Check system dependencies

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
