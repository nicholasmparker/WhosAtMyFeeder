#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Who's At My Feeder - ML Model Download${NC}"
echo "======================================="

# Create model directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p \
    models/quality/tf-iqa-model \
    models/enhancement/RealESRGAN_x4plus \
    test_data

# Download RealESRGAN model
echo -e "\n${YELLOW}Downloading RealESRGAN model...${NC}"
curl -L \
    https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth \
    -o models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth

# Create basic TF-IQA model
echo -e "\n${YELLOW}Setting up TF-IQA model...${NC}"
python3 setup_models.py

# Download test image
echo -e "\n${YELLOW}Downloading test image...${NC}"
curl -L \
    https://raw.githubusercontent.com/mmcc-xx/WhosAtMyFeeder/master/example_images/cardinal.jpg \
    -o test_data/test_bird.jpg

echo -e "\n${GREEN}Model download complete!${NC}"
echo -e "Models are stored in:"
echo -e "- ./models/quality/tf-iqa-model"
echo -e "- ./models/enhancement/RealESRGAN_x4plus"
echo -e "\nTo use the models:"
echo -e "1. Start the container: ${YELLOW}docker-compose up -d${NC}"
