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

-- Insert sample weather data (temperatures in Fahrenheit for imperial units)
INSERT INTO weather_data (timestamp, temperature, feels_like, humidity, pressure, wind_speed, wind_direction, precipitation, cloud_cover, visibility, weather_condition)
VALUES 
    ('2025-01-17 10:00:00', 60.0, 58.0, 65, 1013, 8.0, 180, 0.0, 25, 10000, 'partly cloudy'),
    ('2025-01-17 10:15:00', 61.0, 59.0, 64, 1013, 7.5, 182, 0.0, 28, 10000, 'partly cloudy'),
    ('2025-01-17 11:00:00', 63.0, 61.0, 62, 1013, 9.0, 185, 0.0, 30, 10000, 'partly cloudy'),
    ('2025-01-17 14:30:00', 68.0, 66.0, 58, 1012, 10.0, 190, 0.0, 45, 10000, 'clear sky'),
    ('2025-01-17 14:45:00', 69.0, 67.0, 57, 1012, 9.5, 192, 0.0, 42, 10000, 'clear sky'),
    ('2025-01-17 15:00:00', 70.0, 68.0, 57, 1012, 9.0, 195, 0.0, 40, 10000, 'clear sky'),
    ('2025-01-17 15:15:00', 70.5, 68.5, 56, 1012, 8.5, 198, 0.0, 38, 10000, 'clear sky');

-- Link detections with weather data (using 15-minute intervals for more precise correlation)
INSERT INTO detection_weather (detection_id, weather_id)
SELECT d.id, w.id
FROM detections d
JOIN weather_data w 
WHERE strftime('%Y-%m-%d %H:%M', d.detection_time) = strftime('%Y-%m-%d %H:%M', w.timestamp)
   OR (strftime('%Y-%m-%d %H', d.detection_time) = strftime('%Y-%m-%d %H', w.timestamp)
       AND abs(strftime('%M', d.detection_time) - strftime('%M', w.timestamp)) <= 15);
