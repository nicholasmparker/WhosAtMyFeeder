from collections import defaultdict
from datetime import datetime
from sqlalchemy import text
from .database import db

def get_common_name(scientific_name):
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


def recent_detections(num_detections):
    def do_query(session):
        query = """
            WITH local_time AS (
                SELECT 
                    d.*,
                    iq.clarity_score,
                    iq.composition_score,
                    iq.enhancement_status,
                    iq.quality_improvement,
                    datetime(d.detection_time, 'localtime') as local_detection_time,
                    b.common_name as common_name,
                    b.scientific_name as scientific_name
                FROM detections d
                LEFT JOIN image_quality iq ON d.id = iq.detection_id
                LEFT JOIN birdnames b ON d.display_name = b.scientific_name
            )
            SELECT *
            FROM local_time
            ORDER BY local_detection_time DESC
            LIMIT :limit
        """
        results = session.execute(text(query), {"limit": num_detections}).fetchall()
        
        formatted_results = []
        for result in results:
            detection = {
                'id': result[0],
                'detection_time': result[1],
                'detection_index': result[2],
                'score': result[3],
                'display_name': result[4],
                'category_name': result[5],
                'frigate_event': result[6],
                'camera_name': result[7],
                'common_name': result[12] or get_common_name(result[4]),
                'scientific_name': result[13] or result[4],
                'quality_score': result[8] if result[8] is not None else None,
                'composition_score': result[9] if result[9] is not None else None,
                'enhancement_status': result[10],
                'quality_improvement': result[11] if result[11] is not None else None
            }
            formatted_results.append(detection)
        
        return formatted_results
    
    return db.execute_read(do_query)


def get_daily_summary(date):
    def do_query(session):
        date_str = date.strftime('%Y-%m-%d')
        print(f"\nGetting daily summary for date: {date_str}", flush=True)
        
        # First check if we have any data for this date
        count = session.execute(
            text("SELECT COUNT(*) FROM detections WHERE DATE(detection_time) = :date"),
            {"date": date_str}
        ).scalar()
        print(f"Found {count} detections for date {date_str}", flush=True)
        
        query = '''  
            SELECT display_name,  
                   COUNT(*) AS total_detections,  
                   STRFTIME('%H', detection_time) AS hour,  
                   COUNT(*) AS hourly_detections  
            FROM (  
                SELECT *  
                FROM detections  
                WHERE DATE(detection_time) = :date  
            ) AS subquery  
            GROUP BY display_name, hour  
            ORDER BY total_detections DESC, display_name, hour  
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
            display_name = row[0]  # Using index since we're not using sqlite.Row
            summary[display_name]['scientific_name'] = display_name
            summary[display_name]['common_name'] = get_common_name(display_name)
            summary[display_name]['total_detections'] += row[3]  # hourly_detections
            summary[display_name]['hourly_detections'][int(row[2])] = row[3]  # hour and hourly_detections
        
        result = dict(summary)
        print(f"Returning summary with {len(result)} species", flush=True)
        return result
    
    return db.execute_read(do_query)


def get_records_for_date_hour(date, hour):
    def do_query(session):
        query = '''    
            SELECT *    
            FROM detections    
            WHERE strftime('%Y-%m-%d', detection_time) = :date 
            AND strftime('%H', detection_time) = :hour    
            ORDER BY detection_time    
        '''
        
        records = session.execute(
            text(query),
            {"date": date, "hour": str(hour).zfill(2)}
        ).fetchall()
        
        # Convert records to dictionaries and add common names
        result = []
        for record in records:
            record_dict = {
                'id': record[0],
                'detection_time': record[1],
                'detection_index': record[2],
                'score': record[3],
                'display_name': record[4],
                'category_name': record[5],
                'frigate_event': record[6],
                'camera_name': record[7],
                'common_name': get_common_name(record[4])
            }
            result.append(record_dict)
        
        return result
    
    return db.execute_read(do_query)


def get_records_for_scientific_name_and_date(scientific_name, date):
    def do_query(session):
        query = '''    
            SELECT *    
            FROM detections    
            WHERE display_name = :name 
            AND strftime('%Y-%m-%d', detection_time) = :date    
            ORDER BY detection_time    
        '''
        
        records = session.execute(
            text(query),
            {"name": scientific_name, "date": date}
        ).fetchall()
        
        # Convert records to dictionaries and add common names
        result = []
        for record in records:
            record_dict = {
                'id': record[0],
                'detection_time': record[1],
                'detection_index': record[2],
                'score': record[3],
                'display_name': record[4],
                'category_name': record[5],
                'frigate_event': record[6],
                'camera_name': record[7],
                'common_name': get_common_name(record[4])
            }
            result.append(record_dict)
        
        return result
    
    return db.execute_read(do_query)


def get_earliest_detection_date():
    def do_query(session):
        latest_date = session.execute(
            text("SELECT MAX(date(detection_time)) FROM detections")
        ).scalar()
        return latest_date if latest_date else None
    
    return db.execute_read(do_query)
