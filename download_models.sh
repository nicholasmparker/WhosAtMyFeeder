#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Who's At My Feeder - ML Model Download${NC}"
echo "======================================="

# Create Docker volumes if they don't exist
echo -e "\n${YELLOW}Creating Docker volumes...${NC}"
docker volume create whosatmyfeeder_ml_models
docker volume create whosatmyfeeder_test_data

# Create temporary container to manage volumes
echo -e "\n${YELLOW}Creating temporary container to manage volumes...${NC}"
docker run -d --name wamf_model_setup \
    -v whosatmyfeeder_ml_models:/models \
    -v whosatmyfeeder_test_data:/test_data \
    python:3.11-slim sleep infinity

# Install dependencies in temporary container
echo -e "\n${YELLOW}Installing dependencies...${NC}"
docker exec wamf_model_setup apt-get update
docker exec wamf_model_setup apt-get install -y wget curl

# Create directories
echo -e "\n${YELLOW}Creating directories...${NC}"
docker exec wamf_model_setup mkdir -p \
    /models/quality/tf-iqa-model \
    /models/enhancement/RealESRGAN_x4plus \
    /test_data

# Download RealESRGAN model
echo -e "\n${YELLOW}Downloading RealESRGAN model...${NC}"
docker exec wamf_model_setup wget \
    -O /models/enhancement/RealESRGAN_x4plus/RealESRGAN_x4plus.pth \
    https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth

# Create basic TF-IQA model (since actual weights aren't publicly available)
echo -e "\n${YELLOW}Setting up TF-IQA model...${NC}"
docker cp setup_models.py wamf_model_setup:/setup_models.py
docker exec wamf_model_setup pip install tensorflow
docker exec wamf_model_setup python -c "
import tensorflow as tf
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
model.compile(optimizer='adam', loss='binary_crossentropy')
model.save('/models/quality/tf-iqa-model/model.h5')
"

# Download test image
echo -e "\n${YELLOW}Downloading test image...${NC}"
docker exec wamf_model_setup wget \
    -O /test_data/test_bird.jpg \
    https://raw.githubusercontent.com/mmcc-xx/WhosAtMyFeeder/master/example_images/cardinal.jpg

# Clean up
echo -e "\n${YELLOW}Cleaning up...${NC}"
docker stop wamf_model_setup
docker rm wamf_model_setup

echo -e "\n${GREEN}Model download complete!${NC}"
echo -e "Models are stored in Docker volumes:"
echo -e "- whosatmyfeeder_ml_models"
echo -e "- whosatmyfeeder_test_data"
echo -e "\nTo use the models:"
echo -e "1. Start the container: ${YELLOW}docker-compose up -d${NC}"
echo -e "2. Test the models: ${YELLOW}docker exec whosatmyfeeder python setup_models.py${NC}"
