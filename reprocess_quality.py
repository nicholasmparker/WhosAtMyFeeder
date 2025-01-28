import sqlite3
import traceback
import sys
from services.shared.image_processing import ImageProcessingService, update_image_quality_table

def reprocess_detections():
    print("Starting reprocess_detections...", flush=True)
    
    try:
        # Initialize image processing service
        print("Initializing ImageProcessingService...", flush=True)
        image_processor = ImageProcessingService()
        
        # Connect to database
        print("Connecting to database...", flush=True)
        conn = sqlite3.connect('/data/speciesid.db')
        cursor = conn.cursor()
        
        try:
            # Get all detections that need quality assessment
            print("Querying for detections...", flush=True)
            cursor.execute("""
                SELECT d.id, d.frigate_event
                FROM detections d
                LEFT JOIN image_quality q ON d.id = q.detection_id
                WHERE q.clarity_score IS NULL
                AND d.frigate_event NOT LIKE 'test_event%'
            """)
            detections = cursor.fetchall()
            
            print(f"Found {len(detections)} detections to process", flush=True)
            
            for detection_id, frigate_event in detections:
                try:
                    print(f"\nProcessing detection {detection_id}...", flush=True)
                    
                    # Get image URL
                    image_url = f"http://dagon.chickenmilkbomb.com:5000/api/events/{frigate_event}/snapshot.jpg"
                    print(f"Image URL: {image_url}", flush=True)
                    
                    # Process image
                    result = image_processor.process_image(image_url)
                    
                    # Update database using the shared function
                    update_image_quality_table('/data/speciesid.db', detection_id, result)
                    
                    print(f"Processed detection {detection_id}: clarity={result['quality_scores']['clarity']:.2f}, composition={result['quality_scores']['composition']:.2f}, overall={result['quality_scores']['overall']:.2f}", flush=True)
                    
                except Exception as e:
                    print(f"Error processing detection {detection_id}:", flush=True)
                    print(traceback.format_exc(), flush=True)
                    continue
                    
        finally:
            print("Closing database connection...", flush=True)
            conn.close()
            
    except Exception as e:
        print("Error in reprocess_detections:", flush=True)
        print(traceback.format_exc(), flush=True)
        sys.exit(1)

if __name__ == "__main__":
    reprocess_detections()
