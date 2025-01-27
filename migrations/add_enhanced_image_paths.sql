-- Create image_quality table with all columns if it doesn't exist
CREATE TABLE IF NOT EXISTS image_quality (
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

-- Create temporary table with all columns
CREATE TEMP TABLE image_quality_backup (
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

-- Copy data
INSERT OR IGNORE INTO image_quality_backup 
SELECT 
    detection_id,
    clarity_score,
    composition_score,
    behavior_tags,
    enhanced_path,
    enhanced_thumbnail_path,
    enhancement_status,
    quality_improvement
FROM image_quality;

-- Drop original table
DROP TABLE IF EXISTS image_quality;

-- Create new table with all columns
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
INSERT OR IGNORE INTO image_quality 
SELECT 
    detection_id,
    clarity_score,
    composition_score,
    behavior_tags,
    enhanced_path,
    enhanced_thumbnail_path,
    enhancement_status,
    quality_improvement
FROM image_quality_backup;

-- Drop temporary table
DROP TABLE image_quality_backup;
