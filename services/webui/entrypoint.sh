#!/bin/sh
set -e

# Create required directories
mkdir -p /data /app/input /app/output

# Initialize database if it doesn't exist
if [ ! -f /data/speciesid.db ]; then
    echo "Initializing database..."
    sqlite3 /data/speciesid.db < init_db.sql
    
    echo "Populating bird names..."
    python populate_birdnames.py
    
    echo "Adding test detection data..."
    sqlite3 /data/speciesid.db << 'EOF'
    INSERT INTO detections (detection_time, display_name, score, frigate_event)
    VALUES 
        (datetime('now', '-1 hour'), 'Cardinalis cardinalis', 0.95, 'test_event_1'),
        (datetime('now', '-2 hours'), 'Cyanocitta cristata', 0.92, 'test_event_2'),
        (datetime('now', '-3 hours'), 'Haemorhous mexicanus', 0.88, 'test_event_3'),
        (datetime('now', '-4 hours'), 'Melospiza melodia', 0.91, 'test_event_4'),
        (datetime('now', '-5 hours'), 'Junco hyemalis', 0.89, 'test_event_5');
EOF
fi

# Apply migrations
echo "Applying migrations..."
sqlite3 /data/speciesid.db < migrations/add_enhanced_image_paths.sql

# Execute the main command
exec "$@"
