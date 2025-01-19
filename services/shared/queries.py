import sqlite3
from collections import defaultdict
from datetime import datetime

DBPATH = '/data/speciesid.db'  # Use absolute path to match Docker configuration

def get_common_name(scientific_name):
    conn = sqlite3.connect(DBPATH)
    cursor = conn.cursor()

    cursor.execute("SELECT common_name FROM birdnames WHERE scientific_name = ?", (scientific_name,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    else:
        print(f"\nMissing bird in local database: {scientific_name}", flush=True)
        print("Consider adding this bird to birdnames table if it's common in your area", flush=True)
        return f"Unknown Bird ({scientific_name})"


def recent_detections(num_detections):
    conn = sqlite3.connect(DBPATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM detections ORDER BY detection_time DESC LIMIT ?", (num_detections,))
    results = cursor.fetchall()

    conn.close()

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
            'common_name': get_common_name(result[4])
        }
        formatted_results.append(detection)

    return formatted_results


def get_daily_summary(date):
    date_str = date.strftime('%Y-%m-%d')
    print(f"\nGetting daily summary for date: {date_str}", flush=True)
    
    conn = sqlite3.connect(DBPATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # First check if we have any data for this date
    check_query = "SELECT COUNT(*) FROM detections WHERE DATE(detection_time) = ?"
    cursor.execute(check_query, (date_str,))
    count = cursor.fetchone()[0]
    print(f"Found {count} detections for date {date_str}", flush=True)

    query = '''  
        SELECT display_name,  
               COUNT(*) AS total_detections,  
               STRFTIME('%H', detection_time) AS hour,  
               COUNT(*) AS hourly_detections  
        FROM (  
            SELECT *  
            FROM detections  
            WHERE DATE(detection_time) = ?  
        ) AS subquery  
        GROUP BY display_name, hour  
        ORDER BY total_detections DESC, display_name, hour  
    '''

    cursor.execute(query, (date_str,))
    rows = cursor.fetchall()
    print(f"Query returned {len(rows)} rows", flush=True)

    summary = defaultdict(lambda: {
        'scientific_name': '',
        'common_name': '',
        'total_detections': 0,
        'hourly_detections': [0] * 24
    })

    for row in rows:
        display_name = row['display_name']
        summary[display_name]['scientific_name'] = display_name
        summary[display_name]['common_name'] = get_common_name(display_name)
        summary[display_name]['total_detections'] += row['hourly_detections']
        summary[display_name]['hourly_detections'][int(row['hour'])] = row['hourly_detections']

    result = dict(summary)
    print(f"Returning summary with {len(result)} species", flush=True)
    conn.close()
    return result


def get_records_for_date_hour(date, hour):
    conn = sqlite3.connect(DBPATH)
    conn.row_factory = sqlite3.Row  # Set the row factory to sqlite3.Row
    cursor = conn.cursor()

    # The SQL query to fetch records for the given date and hour, sorted by detection_time
    query = '''    
        SELECT *    
        FROM detections    
        WHERE strftime('%Y-%m-%d', detection_time) = ? AND strftime('%H', detection_time) = ?    
        ORDER BY detection_time    
    '''

    cursor.execute(query, (date, str(hour).zfill(2)))
    records = cursor.fetchall()

    # Append the common name for each record
    result = []
    for record in records:
        common_name = get_common_name(record['display_name'])  # Access the field by name
        record_dict = dict(record)  # Convert the record to a dictionary
        record_dict['common_name'] = common_name  # Add the 'common_name' key to the record dictionary
        result.append(record_dict)

    conn.close()

    return result


def get_records_for_scientific_name_and_date(scientific_name, date):
    conn = sqlite3.connect(DBPATH)
    conn.row_factory = sqlite3.Row  # Set the row factory to sqlite3.Row
    cursor = conn.cursor()

    # The SQL query to fetch records for the given display_name and date, sorted by detection_time
    query = '''    
        SELECT *    
        FROM detections    
        WHERE display_name = ? AND strftime('%Y-%m-%d', detection_time) = ?    
        ORDER BY detection_time    
    '''

    cursor.execute(query, (scientific_name, date))
    records = cursor.fetchall()

    # Append the common name for each record
    result = []
    for record in records:
        common_name = get_common_name(record['display_name'])  # Access the field by name
        record_dict = dict(record)  # Convert the record to a dictionary
        record_dict['common_name'] = common_name  # Add the 'common_name' key to the record dictionary
        result.append(record_dict)

    conn.close()

    return result


def get_earliest_detection_date():
    conn = sqlite3.connect(DBPATH)
    cursor = conn.cursor()
    # Get the most recent date instead of the earliest
    cursor.execute("SELECT MAX(date(detection_time)) FROM detections")
    latest_date = cursor.fetchone()[0]
    conn.close()
    if latest_date:
        return latest_date
    else:
        return None
