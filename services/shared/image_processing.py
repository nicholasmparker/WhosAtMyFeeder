# [Previous imports and class definitions remain the same until the process_image method]

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
            'enhanced_path': None,
            'enhanced_thumbnail_path': None
        }
        
        # Enhance if needed
        if quality_scores['clarity'] < self.config['local_models']['quality_assessment']['threshold']:
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

# [Rest of the file remains the same]
