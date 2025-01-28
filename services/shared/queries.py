from collections import defaultdict
from datetime import datetime
from sqlalchemy import text
from .database import db

def get_common_name(scientific_name):
    """Get common name for a scientific name, with fallback for unknown birds."""
    def do_query(session):
        result = session.execute(
            text("SELECT common_name FROM birdnames WHERE scientific_name = :name"),
            {"name": scientific_name}
        ).fetchone()
        
        if result:
            return result[0]
        else:
            print(f"\nMissing bird in local database: {scientific_name}", flush=True)
            print("Consider adding this bird to birdnames table if it's common in your area", flush=True)
            return f"Unknown Bird ({scientific_name})"
    
    return db.execute_read(do_query)

def _base_detection_query():
    """Base query for getting detection data with quality metrics and special detections."""
    return """
        SELECT 
            d.id,
            datetime(d.detection_time, 'localtime') as detection_time,
            d.display_name,
            d.score,
            d.frigate_event,
            d.category_name,
            d.camera_name,
            d.detection_index,
            b.common_name,
            COALESCE(iq.visibility_score, 0) as visibility_score,
            COALESCE(iq.clarity_score, 0) as clarity_score,
            COALESCE(iq.composition_score, 0) as composition_score,
            iq.enhancement_status,
            COALESCE(iq.quality_improvement, 0) as quality_improvement,
            iq.enhanced_path,
            iq.enhanced_thumbnail_path,
            CASE WHEN sd.id IS NOT NULL THEN 1 ELSE 0 END as is_special,
            sd.highlight_type,
            sd.score as special_score,
            sd.community_votes,
            sd.featured_status
        FROM detections d
        LEFT JOIN image_quality iq ON d.id = iq.detection_id
        LEFT JOIN birdnames b ON d.display_name = b.scientific_name
        LEFT JOIN special_detections sd ON d.id = sd.detection_id
    """

def _format_detection(record):
    """Format a detection record into a consistent dictionary structure."""
    return {
        'id': record[0],
        'detection_time': record[1],
        'display_name': record[2],
        'score': record[3],
        'frigate_event': record[4],
        'category_name': record[5],
        'camera_name': record[6],
        'detection_index': record[7],
        'common_name': record[8] or f"Unknown Bird ({record[2]})",
        'visibility_score': record[9],
        'clarity_score': record[10],
        'composition_score': record[11],
        'enhancement_status': record[12],
        'quality_improvement': record[13],
        'enhanced_path': record[14],
        'enhanced_thumbnail_path': record[15],
        'scientific_name': record[2],  # display_name is the scientific name
        'is_special': bool(record[16]),
        'highlight_type': record[17],
        'special_score': record[18],
        'community_votes': record[19],
        'featured_status': record[20]
    }

def recent_detections(num_detections):
    """Get most recent detections with quality metrics."""
    def do_query(session):
        # First try to get enhanced images
        query = f"""
            {_base_detection_query()}
            WHERE iq.enhancement_status = 'completed'
            ORDER BY d.detection_time DESC
            LIMIT :limit
        """
        results = session.execute(text(query), {"limit": num_detections}).fetchall()
        
        # If we don't have enough enhanced images, get more recent detections
        if len(results) < num_detections:
            remaining = num_detections - len(results)
            query = f"""
                {_base_detection_query()}
                WHERE d.id NOT IN (SELECT detection_id FROM image_quality WHERE enhancement_status = 'completed')
                ORDER BY d.detection_time DESC
                LIMIT :limit
            """
            more_results = session.execute(text(query), {"limit": remaining}).fetchall()
            results.extend(more_results)
        
        return [_format_detection(result) for result in results]
    
    return db.execute_read(do_query)

def get_daily_summary(date):
    """Get detection summary for a specific date."""
    def do_query(session):
        date_str = date.strftime('%Y-%m-%d')
        print(f"\nGetting daily summary for date: {date_str}", flush=True)
        
        # First check if we have any data for this date
        count = session.execute(
            text("SELECT COUNT(*) FROM detections WHERE DATE(detection_time) = :date"),
            {"date": date_str}
        ).scalar()
        print(f"Found {count} detections for date {date_str}", flush=True)
        
        # More efficient query without subquery
        query = '''
            SELECT 
                d.display_name,
                b.common_name,
                STRFTIME('%H', d.detection_time) AS hour,
                COUNT(*) AS hourly_detections
            FROM detections d
            LEFT JOIN birdnames b ON d.display_name = b.scientific_name
            WHERE DATE(d.detection_time) = :date
            GROUP BY d.display_name, hour
            ORDER BY hourly_detections DESC, d.display_name, hour
        '''
        
        rows = session.execute(text(query), {"date": date_str}).fetchall()
        print(f"Query returned {len(rows)} rows", flush=True)
        
        summary = defaultdict(lambda: {
            'scientific_name': '',
            'common_name': '',
            'total_detections': 0,
            'hourly_detections': [0] * 24
        })
        
        for row in rows:
            display_name = row[0]
            summary[display_name]['scientific_name'] = display_name
            summary[display_name]['common_name'] = row[1] or f"Unknown Bird ({display_name})"
            summary[display_name]['total_detections'] += row[3]
            summary[display_name]['hourly_detections'][int(row[2])] = row[3]
        
        result = dict(summary)
        print(f"Returning summary with {len(result)} species", flush=True)
        return result
    
    return db.execute_read(do_query)

def get_records_for_date_hour(date, hour):
    """Get detailed detection records for a specific date and hour."""
    def do_query(session):
        query = f"""
            {_base_detection_query()}
            WHERE strftime('%Y-%m-%d', d.detection_time) = :date 
            AND strftime('%H', d.detection_time) = :hour    
            ORDER BY d.detection_time    
        """
        
        records = session.execute(
            text(query),
            {"date": date, "hour": str(hour).zfill(2)}
        ).fetchall()
        
        return [_format_detection(record) for record in records]
    
    return db.execute_read(do_query)

def get_records_for_scientific_name_and_date(scientific_name, date):
    """Get detailed detection records for a specific species and date."""
    def do_query(session):
        query = f"""
            {_base_detection_query()}
            WHERE d.display_name = :name 
            AND strftime('%Y-%m-%d', d.detection_time) = :date    
            ORDER BY d.detection_time    
        """
        
        records = session.execute(
            text(query),
            {"name": scientific_name, "date": date}
        ).fetchall()
        
        return [_format_detection(record) for record in records]
    
    return db.execute_read(do_query)

def get_earliest_detection_date():
    """Get the earliest date in the detections table."""
    def do_query(session):
        latest_date = session.execute(
            text("SELECT MAX(date(detection_time)) FROM detections")
        ).scalar()
        return latest_date if latest_date else None
    
    return db.execute_read(do_query)
