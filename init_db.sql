-- Create birdnames table
CREATE TABLE IF NOT EXISTS birdnames (
    scientific_name TEXT PRIMARY KEY,
    common_name TEXT NOT NULL
);

-- Create detections table
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_time DATETIME,
    detection_index INTEGER,
    score REAL,
    display_name TEXT,
    category_name TEXT,
    frigate_event TEXT,
    camera_name TEXT,
    FOREIGN KEY (display_name) REFERENCES birdnames(scientific_name)
);

-- Create weather_data table
CREATE TABLE IF NOT EXISTS weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    temperature REAL,
    feels_like REAL,
    humidity INTEGER,
    pressure INTEGER,
    wind_speed REAL,
    wind_direction INTEGER,
    precipitation REAL,
    cloud_cover INTEGER,
    visibility INTEGER,
    weather_condition TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index on weather timestamp
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp);

-- Create detection_weather join table
CREATE TABLE IF NOT EXISTS detection_weather (
    detection_id INTEGER,
    weather_id INTEGER,
    FOREIGN KEY (detection_id) REFERENCES detections(id),
    FOREIGN KEY (weather_id) REFERENCES weather_data(id)
);

-- Insert bird names
INSERT OR REPLACE INTO birdnames (scientific_name, common_name) VALUES 
    ('Cardinalis cardinalis', 'Northern Cardinal'),
    ('Cyanocitta cristata', 'Blue Jay'),
    ('Poecile atricapillus', 'Black-capped Chickadee'),
    ('Sitta carolinensis', 'White-breasted Nuthatch');

-- Insert sample detections
INSERT INTO detections (detection_time, detection_index, score, display_name, category_name, frigate_event, camera_name)
VALUES 
    ('2025-01-17 10:00:00', 1, 0.95, 'Cardinalis cardinalis', 'bird', 'event1', 'Griffin'),
    ('2025-01-17 10:15:00', 2, 0.92, 'Cyanocitta cristata', 'bird', 'event2', 'Griffin'),
    ('2025-01-17 11:00:00', 3, 0.88, 'Cardinalis cardinalis', 'bird', 'event3', 'Griffin'),
    ('2025-01-17 14:30:00', 4, 0.91, 'Poecile atricapillus', 'bird', 'event4', 'Griffin'),
    ('2025-01-17 14:45:00', 5, 0.89, 'Sitta carolinensis', 'bird', 'event5', 'Griffin'),
    ('2025-01-17 15:00:00', 6, 0.94, 'Cardinalis cardinalis', 'bird', 'event6', 'Griffin'),
    ('2025-01-17 15:15:00', 7, 0.87, 'Cyanocitta cristata', 'bird', 'event7', 'Griffin');

-- Insert sample weather data
INSERT INTO weather_data (timestamp, temperature, feels_like, humidity, pressure, wind_speed, wind_direction, precipitation, cloud_cover, visibility, weather_condition)
VALUES 
    ('2025-01-17 10:00:00', 15.5, 14.2, 65, 1013, 3.5, 180, 0.0, 25, 10000, 'partly cloudy'),
    ('2025-01-17 11:00:00', 16.8, 15.5, 62, 1013, 4.0, 185, 0.0, 30, 10000, 'partly cloudy'),
    ('2025-01-17 14:00:00', 19.2, 18.5, 58, 1012, 4.5, 190, 0.0, 45, 10000, 'partly cloudy'),
    ('2025-01-17 15:00:00', 19.5, 18.8, 57, 1012, 4.2, 195, 0.0, 40, 10000, 'partly cloudy');

-- Link detections with weather data
INSERT INTO detection_weather (detection_id, weather_id)
SELECT d.id, w.id
FROM detections d
JOIN weather_data w ON strftime('%Y-%m-%d %H:00:00', d.detection_time) = strftime('%Y-%m-%d %H:00:00', w.timestamp);
