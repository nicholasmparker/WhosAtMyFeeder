import os
import cv2
import subprocess
from pathlib import Path

def test_directories():
    """Test creation and access of input/output directories."""
    print("\n1. Testing directories...")
    
    try:
        os.makedirs('input', exist_ok=True)
        os.makedirs('output', exist_ok=True)
        print("✓ Directories created successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create directories: {e}")
        return False

def test_docker_available():
    """Test if docker is available."""
    print("\n2. Testing docker setup...")
    
    try:
        # Test basic docker
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("✗ Docker not available")
            return False
        print("✓ Docker is available")
        
        # Try to pull the RealESRGAN image
        print("Pulling RealESRGAN image...")
        result = subprocess.run(['docker', 'pull', 'docker.io/kociolek/real-esrgan'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ Failed to pull RealESRGAN image: {result.stderr}")
            return False
        print("✓ RealESRGAN image pulled successfully")
        
        return True
    except Exception as e:
        print(f"✗ Docker test failed: {e}")
        return False

def test_image_processing(image_path):
    """Test basic image operations."""
    print("\n3. Testing image processing...")
    
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            print(f"✗ Failed to read image: {image_path}")
            return False
        print("✓ Image read successfully")
        
        # Save to input directory
        input_path = os.path.join('input', 'test.png')
        cv2.imwrite(input_path, image)
        if not os.path.exists(input_path):
            print("✗ Failed to save image to input directory")
            return False
        print("✓ Image saved to input directory")
        
        return True
    except Exception as e:
        print(f"✗ Image processing test failed: {e}")
        return False

def test_enhancement(image_path):
    """Test the full enhancement pipeline."""
    print("\n4. Testing enhancement pipeline...")
    
    try:
        # Prepare paths
        input_filename = Path(image_path).name
        output_filename = Path(image_path).stem + '_out' + Path(image_path).suffix
        input_path = os.path.join('input', input_filename)
        output_path = os.path.join('output', output_filename)
        
        # Copy test image to input
        image = cv2.imread(image_path)
        cv2.imwrite(input_path, image)
        print("✓ Test image copied to input directory")
        
        # Run RealESRGAN (try without GPU first)
        cmd = [
            'docker', 'run', '--rm',
            '-v', f"{os.path.abspath('input')}:/app/input",
            '-v', f"{os.path.abspath('output')}:/app/output",
            'docker.io/kociolek/real-esrgan'
        ]
        
        print("Running RealESRGAN command:")
        print(" ".join(cmd))
        
        # List input directory contents
        print("\nInput directory contents:")
        print(os.listdir('input'))
        
        print("\nRunning enhancement...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("\nCommand output:")
        if result.stdout:
            print("stdout:", result.stdout)
        if result.stderr:
            print("stderr:", result.stderr)
        
        if result.returncode != 0:
            print(f"✗ Enhancement failed with return code: {result.returncode}")
            return False
        
        # List output directory contents
        print("\nOutput directory contents:")
        print(os.listdir('output'))
        
        # Check if output was created
        if not os.path.exists(output_path):
            print(f"✗ No output image found at: {output_path}")
            return False
        
        # Load and verify output image
        enhanced = cv2.imread(output_path)
        if enhanced is None:
            print("✗ Failed to read enhanced image")
            return False
        
        print("✓ Enhancement pipeline completed successfully")
        print(f"✓ Enhanced image saved to: {output_path}")
        
        # Cleanup
        os.remove(input_path)
        os.remove(output_path)
        print("✓ Cleanup completed")
        
        return True
    except Exception as e:
        print(f"✗ Enhancement test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Starting enhancement tests...")
    
    # Use screenshot.jpg as test image if it exists
    test_image = 'screenshot.jpg'
    if not os.path.exists(test_image):
        print(f"✗ Test image not found: {test_image}")
        return
    
    tests = [
        test_directories(),
        test_docker_available(),
        test_image_processing(test_image),
        test_enhancement(test_image)
    ]
    
    print("\nTest Summary:")
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {sum(tests)}")
    print(f"Failed: {len(tests) - sum(tests)}")

if __name__ == "__main__":
    main()
