-- Base tables for bird detection and identification
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_time DATETIME NOT NULL,
    display_name TEXT,  -- Scientific name
    score REAL,
    frigate_event TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS birdnames (
    scientific_name TEXT PRIMARY KEY,
    common_name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Special detection system tables
CREATE TABLE IF NOT EXISTS rarity_scores (
    species_id TEXT PRIMARY KEY,  -- Scientific name
    frequency_score REAL,  -- 0-1 score based on visit frequency
    seasonal_score REAL,   -- 0-1 score based on seasonal patterns
    last_seen DATETIME,
    first_seen_this_season DATETIME,
    total_visits INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (species_id) REFERENCES birdnames(scientific_name)
);

CREATE TABLE IF NOT EXISTS image_quality (
    detection_id INTEGER PRIMARY KEY,
    clarity_score REAL,        -- 0-1 score for image clarity/focus
    composition_score REAL,    -- 0-1 score for composition/framing
    behavior_tags TEXT,        -- JSON array of behavior tags
    visibility_score REAL,     -- 0-1 score for bird visibility
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);

CREATE TABLE IF NOT EXISTS special_detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_id INTEGER UNIQUE,
    highlight_type TEXT CHECK(highlight_type IN ('rare', 'quality', 'behavior')),
    score REAL,  -- Combined score determining significance
    community_votes INTEGER DEFAULT 0,
    featured_status BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);

-- Vision analysis cache and cost tracking
CREATE TABLE IF NOT EXISTS vision_analysis_cache (
    detection_id INTEGER PRIMARY KEY,
    analysis_data TEXT,        -- JSON string of OpenAI response
    clarity_score REAL,        -- 0-1 score from vision analysis
    composition_score REAL,    -- 0-1 score from vision analysis
    behavior_tags TEXT,        -- JSON array of behaviors
    cost_tokens INTEGER,       -- Number of tokens used
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);

CREATE TABLE IF NOT EXISTS vision_api_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE,          -- Track costs per day
    total_tokens INTEGER,      -- Total tokens used
    total_cost REAL,          -- Total cost in USD
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Weather tracking tables
CREATE TABLE IF NOT EXISTS weather_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    temperature REAL,
    humidity REAL,
    wind_speed REAL,
    wind_direction TEXT,
    weather_condition TEXT,
    cloud_cover INTEGER,
    precipitation REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detection_weather (
    detection_id INTEGER PRIMARY KEY,
    weather_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id),
    FOREIGN KEY (weather_id) REFERENCES weather_conditions(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_detections_time ON detections(detection_time);
CREATE INDEX IF NOT EXISTS idx_detections_species ON detections(display_name);
CREATE INDEX IF NOT EXISTS idx_special_type ON special_detections(highlight_type);
CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_conditions(timestamp);
CREATE INDEX IF NOT EXISTS idx_vision_cache_time ON vision_analysis_cache(created_at);
CREATE INDEX IF NOT EXISTS idx_vision_costs_date ON vision_api_costs(date);
