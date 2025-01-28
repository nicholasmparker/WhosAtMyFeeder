#!/bin/bash
set -e

# Initialize the database
echo "Initializing database..."

# Drop and recreate image_quality table to ensure correct schema
sqlite3 /data/speciesid.db << 'EOF'
DROP TABLE IF EXISTS image_quality;
CREATE TABLE image_quality (
    detection_id INTEGER PRIMARY KEY,
    clarity_score REAL,
    composition_score REAL,
    behavior_tags TEXT,
    enhanced_path TEXT,
    enhanced_thumbnail_path TEXT,
    enhancement_status TEXT CHECK(enhancement_status IN ("pending", "completed", "failed")),
    quality_improvement REAL,
    visibility_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);
CREATE INDEX IF NOT EXISTS idx_image_quality_detection_id ON image_quality(detection_id);
CREATE INDEX IF NOT EXISTS idx_image_quality_clarity_score ON image_quality(clarity_score);
CREATE INDEX IF NOT EXISTS idx_image_quality_visibility_score ON image_quality(visibility_score);
EOF

# Run the rest of init_db.sql for other tables
sqlite3 /data/speciesid.db < init_db.sql

# Start the application
echo "Starting application..."
exec "$@"
