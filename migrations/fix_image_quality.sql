-- Drop and recreate the table with all columns
DROP TABLE IF EXISTS image_quality;

CREATE TABLE image_quality (
    detection_id INTEGER PRIMARY KEY REFERENCES detections(id),
    clarity_score REAL,
    composition_score REAL,
    behavior_tags TEXT,
    enhanced_path TEXT,
    enhanced_thumbnail_path TEXT,
    enhancement_status TEXT CHECK(enhancement_status IN ('pending', 'completed', 'failed')),
    quality_improvement REAL,
    visibility_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_image_quality_detection_id ON image_quality(detection_id);
CREATE INDEX IF NOT EXISTS idx_image_quality_clarity_score ON image_quality(clarity_score);
CREATE INDEX IF NOT EXISTS idx_image_quality_visibility_score ON image_quality(visibility_score);
