-- First drop the indexes
DROP INDEX IF EXISTS idx_image_quality_detection_id;
DROP INDEX IF EXISTS idx_image_quality_clarity_score;
DROP INDEX IF EXISTS idx_image_quality_visibility_score;

-- Drop and recreate image_quality table with correct schema
DROP TABLE IF EXISTS image_quality;

CREATE TABLE image_quality (
    detection_id INTEGER PRIMARY KEY,
    clarity_score REAL,
    composition_score REAL,
    behavior_tags TEXT,
    enhanced_path TEXT,
    enhanced_thumbnail_path TEXT,
    enhancement_status TEXT CHECK(enhancement_status IN ('pending', 'completed', 'failed')),
    quality_improvement REAL,
    visibility_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);

-- Recreate indexes
CREATE INDEX idx_image_quality_detection_id ON image_quality(detection_id);
CREATE INDEX idx_image_quality_clarity_score ON image_quality(clarity_score);
CREATE INDEX idx_image_quality_visibility_score ON image_quality(visibility_score);
