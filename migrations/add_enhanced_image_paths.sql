-- Add enhanced image paths and status to image_quality table
ALTER TABLE image_quality ADD COLUMN enhanced_path TEXT;
ALTER TABLE image_quality ADD COLUMN enhanced_thumbnail_path TEXT;
ALTER TABLE image_quality ADD COLUMN enhancement_status TEXT CHECK(enhancement_status IN ('pending', 'completed', 'failed'));
ALTER TABLE image_quality ADD COLUMN quality_improvement REAL;
