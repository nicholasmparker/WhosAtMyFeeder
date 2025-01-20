import os
import cv2
from image_processing import ImageProcessingService

def main():
    """Test the full image processing service."""
    print("Testing Image Processing Service...")
    
    # Create storage directories
    os.makedirs('data/enhanced_images', exist_ok=True)
    os.makedirs('data/analysis_cache', exist_ok=True)
    
    # Initialize service with test config
    service = ImageProcessingService('config/test_config.yml')
    
    # Use screenshot.jpg as test image
    test_image = 'screenshot.jpg'
    if not os.path.exists(test_image):
        print(f"✗ Test image not found: {test_image}")
        return
    
    try:
        # Process image
        print(f"\nProcessing image: {test_image}")
        result = service.process_image(test_image)
        
        # Print results
        print("\nQuality Assessment Results:")
        print(f"Clarity Score: {result['quality_scores']['clarity']:.3f}")
        print(f"Composition Score: {result['quality_scores']['composition']:.3f}")
        print(f"Overall Score: {result['quality_scores']['overall']:.3f}")
        
        if result['enhanced']:
            print("\nImage was enhanced:")
            print(f"Enhanced image saved to: {result['enhanced_path']}")
            print("\nEnhanced Quality Scores:")
            print(f"Clarity Score: {result['enhanced_quality_scores']['clarity']:.3f}")
            print(f"Composition Score: {result['enhanced_quality_scores']['composition']:.3f}")
            print(f"Overall Score: {result['enhanced_quality_scores']['overall']:.3f}")
            
            # Load and compare image sizes
            original = cv2.imread(test_image)
            enhanced = cv2.imread(result['enhanced_path'])
            print("\nImage Size Comparison:")
            print(f"Original: {original.shape}")
            print(f"Enhanced: {enhanced.shape}")
            
            # Keep the enhanced image for inspection
            print("\nEnhanced image has been kept for inspection")
        else:
            print("\nImage quality above threshold, no enhancement needed")
        
        print("\n✓ Processing completed successfully")
        
    except Exception as e:
        print(f"\n✗ Processing failed: {str(e)}")
        raise  # Re-raise to see full traceback

if __name__ == "__main__":
    main()
