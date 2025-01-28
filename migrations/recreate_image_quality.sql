-- Create temporary table
CREATE TEMP TABLE image_quality_backup AS SELECT * FROM image_quality;

-- Drop existing table
DROP TABLE image_quality;

-- Recreate table with all columns
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

-- Restore data
INSERT INTO image_quality (
    detection_id,
    clarity_score,
    composition_score,
    behavior_tags,
    enhanced_path,
    enhanced_thumbnail_path,
    enhancement_status,
    quality_improvement,
    visibility_score,
    created_at
) SELECT 
    detection_id,
    clarity_score,
    composition_score,
    behavior_tags,
    enhanced_path,
    enhanced_thumbnail_path,
    enhancement_status,
    quality_improvement,
    visibility_score,
    created_at
FROM image_quality_backup;

-- Drop temporary table
DROP TABLE image_quality_backup;
