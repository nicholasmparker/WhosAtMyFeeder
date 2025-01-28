# Database Schema Improvements Change Order

## Problem Statement
The image quality table schema was getting corrupted due to:
1. Multiple places defining/creating the table (init_db.sql, migrations)
2. No tracking of which migrations had been applied
3. Migrations potentially running multiple times
4. Inconsistent schema definitions across files

## Solution
We've implemented a proper migration system with the following components:

### 1. Migration Tracking
- Created migrations table to track applied migrations
- Each migration is recorded with timestamp
- Prevents duplicate application of migrations

### 2. Organized Migrations
Current migration state:
1. `001_create_migrations_table.sql`: Creates migrations tracking system
2. `002_fix_image_quality.sql`: Fixes image_quality table with all columns and constraints
3. `003_add_detection_metadata.sql`: Adds detection metadata columns

### 3. Clean Database Initialization
- Removed image_quality table creation from init_db.sql
- All schema changes now happen through versioned migrations
- Entrypoint script handles migrations in order

### 4. Consolidated Changes
- Combined multiple image_quality related migrations into one
- Removed redundant migration files
- Clear, linear migration history

## Implementation Details

### Database Schema
The image_quality table now has a consistent schema:
```sql
CREATE TABLE image_quality (
    detection_id INTEGER PRIMARY KEY,
    clarity_score REAL,
    composition_score REAL,
    behavior_tags TEXT,
    enhanced_path TEXT,
    enhanced_thumbnail_path TEXT,
    enhancement_status TEXT CHECK(enhancement_status IN ('pending', 'completed', 'failed')),
    quality_improvement REAL,
    visibility_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id)
);
```

### Migration System
The entrypoint script now:
1. Runs init_db.sql for base tables
2. Checks migrations table for applied migrations
3. Runs pending migrations in order
4. Records each successful migration

## Testing
To verify these changes:
1. Rebuild the container
2. Check migrations table to confirm proper tracking
3. Verify image_quality table has correct schema
4. Confirm no duplicate migrations run

## Benefits
1. Reliable schema management
2. Clear migration history
3. No more schema corruption
4. Easier to add future migrations
