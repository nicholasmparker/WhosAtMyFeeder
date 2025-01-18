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
