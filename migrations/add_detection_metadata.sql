-- Add new columns to detections table
ALTER TABLE detections ADD COLUMN category_name TEXT;
ALTER TABLE detections ADD COLUMN camera_name TEXT;
ALTER TABLE detections ADD COLUMN detection_index INTEGER;

-- Update existing rows with default values where needed
UPDATE detections SET category_name = 'bird' WHERE category_name IS NULL;
UPDATE detections SET detection_index = 0 WHERE detection_index IS NULL;
