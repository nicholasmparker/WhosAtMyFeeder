-- Add foreign key constraint between detections and birdnames
CREATE TABLE IF NOT EXISTS detections_new (
    id INTEGER PRIMARY KEY,
    detection_time DATETIME NOT NULL,
    display_name TEXT NOT NULL REFERENCES birdnames(scientific_name),
    score REAL NOT NULL CHECK (score >= 0 AND score <= 1),
    frigate_event TEXT,
    category_name TEXT,
    camera_name TEXT,
    detection_index INTEGER,
    enhancement_status TEXT CHECK (enhancement_status IN ('pending', 'completed', 'failed')),
    FOREIGN KEY (display_name) REFERENCES birdnames(scientific_name)
);

INSERT INTO detections_new SELECT * FROM detections;
DROP TABLE detections;
ALTER TABLE detections_new RENAME TO detections;

-- Add CHECK constraints for score ranges (0-1)
CREATE TABLE IF NOT EXISTS rarity_scores_new (
    id INTEGER PRIMARY KEY,
    detection_id INTEGER,
    frequency_score REAL CHECK (frequency_score >= 0 AND frequency_score <= 1),
    seasonal_score REAL CHECK (seasonal_score >= 0 AND seasonal_score <= 1),
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);

INSERT INTO rarity_scores_new SELECT * FROM rarity_scores;
DROP TABLE rarity_scores;
ALTER TABLE rarity_scores_new RENAME TO rarity_scores;

CREATE TABLE IF NOT EXISTS vision_analysis_cache_new (
    id INTEGER PRIMARY KEY,
    detection_id INTEGER,
    clarity_score REAL CHECK (clarity_score >= 0 AND clarity_score <= 1),
    composition_score REAL CHECK (composition_score >= 0 AND composition_score <= 1),
    behavior_tags TEXT CHECK (json_valid(behavior_tags) OR behavior_tags IS NULL),
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);

INSERT INTO vision_analysis_cache_new SELECT * FROM vision_analysis_cache;
DROP TABLE vision_analysis_cache;
ALTER TABLE vision_analysis_cache_new RENAME TO vision_analysis_cache;

-- Add JSON validation for behavior_tags
CREATE TABLE IF NOT EXISTS image_quality_new (
    detection_id INTEGER PRIMARY KEY,
    clarity_score REAL CHECK (clarity_score >= 0 AND clarity_score <= 1),
    composition_score REAL CHECK (composition_score >= 0 AND composition_score <= 1),
    behavior_tags TEXT CHECK (json_valid(behavior_tags) OR behavior_tags IS NULL),
    enhanced_path TEXT,
    enhanced_thumbnail_path TEXT,
    enhancement_status TEXT CHECK (enhancement_status IN ('pending', 'completed', 'failed')),
    quality_improvement REAL,
    visibility_score REAL GENERATED ALWAYS AS (COALESCE(clarity_score * 0.6 + composition_score * 0.4, 0)) STORED,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);

INSERT INTO image_quality_new SELECT * FROM image_quality;
DROP TABLE image_quality;
ALTER TABLE image_quality_new RENAME TO image_quality;

-- Add missing indexes for performance
CREATE INDEX IF NOT EXISTS idx_detection_weather_weather_id
ON detection_weather(weather_id);

CREATE INDEX IF NOT EXISTS idx_image_quality_detection_time
ON image_quality(created_at);

-- Add weather condition enumeration constraint
CREATE TABLE IF NOT EXISTS weather_data_new (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    temperature REAL,
    humidity REAL,
    wind_speed REAL,
    wind_direction TEXT,
    pressure REAL,
    precipitation REAL,
    cloud_cover INTEGER,
    weather_condition TEXT CHECK (weather_condition IN (
        'clear',
        'clouds',
        'rain',
        'snow',
        'thunderstorm',
        'drizzle',
        'mist',
        'fog',
        'haze'
    )),
    units TEXT NOT NULL DEFAULT 'metric' CHECK (units IN ('metric', 'imperial'))
);

INSERT INTO weather_data_new SELECT *, 'metric' FROM weather_data;
DROP TABLE weather_data;
ALTER TABLE weather_data_new RENAME TO weather_data;

-- Create indexes for timestamp columns
CREATE INDEX IF NOT EXISTS idx_detections_detection_time
ON detections(detection_time);

CREATE INDEX IF NOT EXISTS idx_weather_data_timestamp
ON weather_data(timestamp);

CREATE INDEX IF NOT EXISTS idx_image_quality_created_at
ON image_quality(created_at);
