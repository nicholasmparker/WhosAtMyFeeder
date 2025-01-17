-- Create detections table
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_time DATETIME,
    detection_index INTEGER,
    score REAL,
    display_name TEXT,
    category_name TEXT,
    frigate_event TEXT,
    camera_name TEXT
);

-- Create some sample data
INSERT INTO detections (detection_time, detection_index, score, display_name, category_name, frigate_event, camera_name)
VALUES 
    ('2025-01-17 10:00:00', 1, 0.95, 'Cardinalis cardinalis', 'bird', 'event1', 'cam1'),
    ('2025-01-17 10:15:00', 2, 0.92, 'Cyanocitta cristata', 'bird', 'event2', 'cam1'),
    ('2025-01-17 11:00:00', 3, 0.88, 'Cardinalis cardinalis', 'bird', 'event3', 'cam1');
