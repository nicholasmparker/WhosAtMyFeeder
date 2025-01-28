import requests
import sqlite3
from datetime import datetime, timedelta
import json
from services.shared.image_processing import ImageProcessingService
from services.shared.special_detection_service import SpecialDetectionService
import time
import sys
import cv2
import numpy as np
from PIL import Image, ImageOps
from io import BytesIO
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision

def get_frigate_events(start_date=None, end_date=None):
    """Get all bird events from Frigate API within date range."""
    print("Fetching events from Frigate API...", flush=True)
    
    # Default to last 30 days if no date range provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    url = "http://dagon.chickenmilkbomb.com:5000/api/events"
    # Convert dates to epoch timestamps
    before_ts = int(datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S").timestamp())
    after_ts = int(datetime.strptime(f"{start_date} 00:00:00", "%Y-%m-%d %H:%M:%S").timestamp())
    
    params = {
        'before': before_ts,
        'after': after_ts,
        'has_snapshot': 1,  # Filter to events with snapshots
        'labels': 'bird'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        events = response.json()
        print(f"Found {len(events)} bird events", flush=True)
        return events
    except Exception as e:
        print(f"Error fetching events: {str(e)}", flush=True)
        return []

def event_exists(cursor, frigate_event):
    """Check if event already exists in our database."""
    cursor.execute("""
        SELECT id FROM detections 
        WHERE frigate_event = ?
    """, (frigate_event,))
    return cursor.fetchone() is not None

def insert_detection(cursor, event, quality_data):
    """Insert detection and quality data into database."""
    try:
        # Insert detection
        cursor.execute("""
            INSERT INTO detections (
                detection_time,
                display_name,
                score,
                frigate_event,
                category_name,
                camera_name,
                detection_index,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            event['start_time'],
            event['display_name'],  # Now using the identified species name
            event['score'],
            event['id'],
            'bird',
            event['camera'],
            0,
        ))
        detection_id = cursor.lastrowid
        
        # Insert quality data
        cursor.execute("""
            INSERT INTO image_quality (
                detection_id,
                clarity_score,
                composition_score,
                visibility_score,
                enhanced_path,
                enhanced_thumbnail_path,
                enhancement_status,
                quality_improvement,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            detection_id,
            quality_data['quality_scores']['clarity'],
            quality_data['quality_scores']['composition'],
            quality_data['quality_scores']['overall'],
            quality_data.get('enhanced_path'),
            quality_data.get('enhanced_thumbnail_path'),
            'completed' if quality_data.get('enhanced') else 'pending',  # Set pending as default status
            (quality_data.get('enhanced_quality_scores', {}).get('overall', 0) - 
             quality_data['quality_scores']['overall']) if quality_data.get('enhanced') else None
        ))
        
        return detection_id
    except Exception as e:
        print(f"Error inserting detection: {str(e)}", flush=True)
        return None

def process_image(image):
    """Process image for species identification."""
    max_size = (224, 224)
    image.thumbnail(max_size)
    return ImageOps.expand(image, 
        border=((max_size[0] - image.size[0]) // 2,
                (max_size[1] - image.size[1]) // 2),
        fill='black')

def identify_species(image_url, classifier):
    """Identify bird species in image."""
    try:
        # Get image from URL
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Convert to PIL Image and process
        image = Image.open(BytesIO(response.content))
        padded_image = process_image(image)
        np_arr = np.array(padded_image)
        
        # Classify
        tensor_image = vision.TensorImage.create_from_array(np_arr)
        categories = classifier.classify(tensor_image)
        
        # Debug logging
        print("Classification results:", flush=True)
        for classification in categories.classifications:
            for category in classification.categories:
                print(f"  Category: {category.category_name}", flush=True)
                print(f"  Display name: {category.display_name}", flush=True)
                print(f"  Score: {category.score}", flush=True)
                print(f"  Index: {category.index}", flush=True)
        
        # Get first category
        category = categories.classifications[0].categories[0]
        
        # Skip if it's background (index 964) or score too low
        if category.index == 964 or category.score < 0.7:  # Using threshold from config
            print(f"Skipping detection - index: {category.index}, score: {category.score}", flush=True)
            return None, 0
            
        return category.display_name, category.score
    except Exception as e:
        print(f"Error identifying species: {str(e)}", flush=True)
        return None, 0

def import_detections(start_date=None, end_date=None):
    """Import bird detections from Frigate into our database."""
    print("Starting detection import...", flush=True)
    
    # Initialize services
    image_processor = ImageProcessingService()
    special_detection_service = SpecialDetectionService()
    
    # Initialize TFLite model
    base_options = core.BaseOptions(
        file_name='/app/models/model.tflite',  # Updated path
        use_coral=False, 
        num_threads=4)
    classification_options = processor.ClassificationOptions(
        max_results=1, 
        score_threshold=0)
    options = vision.ImageClassifierOptions(
        base_options=base_options, 
        classification_options=classification_options)
    classifier = vision.ImageClassifier.create_from_options(options)
    
    # Connect to database
    conn = sqlite3.connect('/data/speciesid.db')
    cursor = conn.cursor()
    
    try:
        # Get events from Frigate
        events = get_frigate_events(start_date, end_date)
        if not events:
            print("No events found to import", flush=True)
            return
            
        # Process each event
        for i, event in enumerate(events, 1):
            print(f"\nProcessing event {i}/{len(events)}: {event['id']}", flush=True)
            
            # Skip if already imported
            if event_exists(cursor, event['id']):
                print(f"Event {event['id']} already exists, skipping", flush=True)
                continue
            
            try:
                # Process image
                image_url = f"http://dagon.chickenmilkbomb.com:5000/api/events/{event['id']}/snapshot.jpg"
                quality_data = image_processor.process_image(image_url)
                
                # Identify species
                image_url = f"http://dagon.chickenmilkbomb.com:5000/api/events/{event['id']}/snapshot.jpg"
                species_name, species_score = identify_species(image_url, classifier)
                
                # Insert into database
                event['display_name'] = species_name if species_name else 'Unknown Bird'
                event['score'] = species_score
                
                detection_id = insert_detection(cursor, event, quality_data)
                if detection_id:
                    print(f"Successfully imported event {event['id']} as detection {detection_id}", flush=True)
                    conn.commit()
                    
                    # Update rarity scores and create special detection
                    special_detection_service.update_rarity_scores()
                    special_detection_service.create_special_detection(detection_id)
                
                # Add small delay to avoid overwhelming services
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing event {event['id']}: {str(e)}", flush=True)
                continue
    
    except Exception as e:
        print(f"Error during import: {str(e)}", flush=True)
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    # Allow command line arguments for date range
    if len(sys.argv) > 2:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        start_date = None
        end_date = None
    
    import_detections(start_date, end_date)
