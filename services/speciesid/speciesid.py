import os
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

import numpy as np
from datetime import datetime
import time
import multiprocessing
import cv2
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
import paho.mqtt.client as mqtt
import hashlib
import yaml
import sys
import json
import requests
import aiohttp
import asyncio
from PIL import Image, ImageOps
from io import BytesIO
from sqlalchemy import text
from shared.queries import get_common_name
from concurrent.futures import ThreadPoolExecutor
from shared.special_detection_service import SpecialDetectionService
from shared.database import db

classifier = None
config = None
firstmessage = True
special_detection_service = None

def classify(image):
    try:
        # Convert to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        tensor_image = vision.TensorImage.create_from_array(image)
        result = classifier.classify(tensor_image)
        
        if not result.classifications:
            return []
        
        return result.classifications[0].categories
    except Exception as e:
        print(f"Error in classify function: {str(e)}", flush=True)
        return []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        topic = config['frigate']['main_topic'] + "/events"
        client.subscribe(topic)
    else:
        print(f"MQTT Connection failed with code {rc}", flush=True)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"Unexpected MQTT disconnection (code {rc})", flush=True)
        while True:
            try:
                client.reconnect()
                break
            except Exception as e:
                print(f"MQTT reconnection failed: {str(e)}", flush=True)
                time.sleep(60)
    else:
        print("Clean MQTT disconnection", flush=True)

def set_sublabel(frigate_url, frigate_event, sublabel):
    if len(sublabel) > 20:
        sublabel = sublabel[:20]

    payload = {"subLabel": sublabel}
    headers = {"Content-Type": "application/json"}
    post_url = frigate_url + "/api/events/" + frigate_event + "/sub_label"

    try:
        response = requests.post(post_url, data=json.dumps(payload), headers=headers)
        if response.status_code != 200:
            print(f"Failed to set sublabel: {response.status_code}", flush=True)
    except Exception as e:
        print(f"Error setting sublabel: {str(e)}", flush=True)

async def process_special_detection(detection_id, score):
    """Process special detection asynchronously"""
    try:
        special_detection_service.update_rarity_scores()
        image_data = {
            'clarity': score,
            'composition': 0.8,
            'visibility': 0.8,
            'behaviors': []
        }
        special_detection_service.evaluate_image_quality(detection_id, image_data)
        special_detection_service.create_special_detection(detection_id)
    except Exception as e:
        print(f"Error in special detection processing: {str(e)}", flush=True)

async def notify_websocket(detection_data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://websocket:8765/notify', json=detection_data) as response:
                if response.status != 200:
                    print(f"WebSocket notification failed: {response.status}", flush=True)
    except Exception as e:
        print(f"WebSocket error: {str(e)}", flush=True)

def process_image(image):
    max_size = (224, 224)
    image.thumbnail(max_size)
    return ImageOps.expand(image, 
        border=((max_size[0] - image.size[0]) // 2,
                (max_size[1] - image.size[1]) // 2),
        fill='black')

def handle_detection(session, frigate_event, formatted_start_time, index, score, display_name, category_name, camera_name):
    """Handle database operations for a detection within a transaction"""
    # Check if detection exists
    result = session.execute(
        text("SELECT * FROM detections WHERE frigate_event = :event"),
        {"event": frigate_event}
    ).fetchone()

    if result is None:
        # Insert new detection
        stmt = text("""
            INSERT INTO detections (detection_time, detection_index, score,
            display_name, category_name, frigate_event, camera_name)
            VALUES (:time, :index, :score, :display, :category, :event, :camera)
        """)
        result = session.execute(stmt, {
            "time": formatted_start_time,
            "index": index,
            "score": score,
            "display": display_name,
            "category": category_name,
            "event": frigate_event,
            "camera": camera_name
        })
        detection_id = result.lastrowid
        return detection_id, True
    else:
        existing_score = result[3]
        if score > existing_score:
            # Update existing detection
            stmt = text("""
                UPDATE detections
                SET detection_time = :time, detection_index = :index,
                    score = :score, display_name = :display, category_name = :category
                WHERE frigate_event = :event
            """)
            session.execute(stmt, {
                "time": formatted_start_time,
                "index": index,
                "score": score,
                "display": display_name,
                "category": category_name,
                "event": frigate_event
            })
            return result[0], True
    return None, False

def on_message(client, userdata, message):
    loop = None
    global firstmessage

    if not firstmessage:
        try:
            payload_dict = json.loads(message.payload)
            after_data = payload_dict.get('after', {})

            if (after_data['camera'] in config['frigate']['camera'] and
                    after_data['label'] == 'bird'):

                frigate_event = after_data['id']
                frigate_url = config['frigate']['frigate_url']
                snapshot_url = frigate_url + "/api/events/" + frigate_event + "/snapshot.jpg"

                params = {"crop": 1, "quality": 95}
                response = requests.get(snapshot_url, params=params)

                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    padded_image = process_image(image)
                    np_arr = np.array(padded_image)

                    categories = classify(np_arr)
                    if not categories:
                        return

                    category = categories[0]
                    index = category.index
                    score = category.score
                    display_name = category.display_name
                    category_name = category.category_name

                    start_time = datetime.fromtimestamp(after_data['start_time'])
                    formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

                    if index == 964 or score <= config['classification']['threshold']:
                        return

                    def process_db(session):
                        detection_id, should_process = handle_detection(
                            session, frigate_event, formatted_start_time,
                            index, score, display_name, category_name,
                            after_data['camera']
                        )
                        return detection_id, should_process

                    try:
                        detection_id, should_process = db.execute_write(process_db)
                        
                        if should_process:
                            common_name = get_common_name(display_name)
                            set_sublabel(frigate_url, frigate_event, common_name)

                            # Process special detection and WebSocket notification asynchronously
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                                detection_data = {
                                    "common_name": common_name,
                                    "scientific_name": display_name,
                                    "score": score,
                                    "frigate_event": frigate_event,
                                    "timestamp": formatted_start_time
                                }
                                
                                tasks = [
                                    process_special_detection(detection_id, score),
                                    notify_websocket(detection_data)
                                ]
                                loop.run_until_complete(asyncio.gather(*tasks))
                            except Exception as e:
                                print(f"Async processing error: {str(e)}", flush=True)
                            finally:
                                if loop:
                                    loop.close()

                    except Exception as e:
                        print(f"Database operation error: {str(e)}", flush=True)

        except Exception as e:
            print(f"Message processing error: {str(e)}", flush=True)

    else:
        firstmessage = False

def setupdb():
    """Initialize the database schema"""
    def do_setup(session):
        session.execute(text("""    
            CREATE TABLE IF NOT EXISTS detections (    
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                detection_time TIMESTAMP NOT NULL,  
                detection_index INTEGER NOT NULL,  
                score REAL NOT NULL,  
                display_name TEXT NOT NULL,  
                category_name TEXT NOT NULL,  
                frigate_event TEXT NOT NULL UNIQUE,
                camera_name TEXT NOT NULL 
            )    
        """))
    
    db.execute_write(do_setup)

def load_config():
    global config
    with open('./config/config.yml', 'r') as config_file:
        config = yaml.safe_load(config_file)

def run_mqtt_client():
    now = datetime.now()
    client = mqtt.Client("birdspeciesid" + now.strftime("%Y%m%d%H%M%S"))
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect

    if config['frigate']['mqtt_auth']:
        client.username_pw_set(config['frigate']['mqtt_username'], 
                             config['frigate']['mqtt_password'])

    client.connect(config['frigate']['mqtt_server'])
    client.loop_forever()

def main():
    try:
        print("Starting Bird Species Identification System", flush=True)
        load_config()
        
        global special_detection_service
        special_detection_service = SpecialDetectionService('/data/speciesid.db')

        # Initialize TFLite model
        base_options = core.BaseOptions(
            file_name=config['classification']['model'], 
            use_coral=False, 
            num_threads=4)
        classification_options = processor.ClassificationOptions(
            max_results=1, 
            score_threshold=0)
        options = vision.ImageClassifierOptions(
            base_options=base_options, 
            classification_options=classification_options)

        global classifier
        classifier = vision.ImageClassifier.create_from_options(options)
        print("TFLite model initialized successfully", flush=True)

        setupdb()
        
        # Start MQTT client
        run_mqtt_client()
                
    except Exception as e:
        print(f"Error in main: {str(e)}", flush=True)
        raise

if __name__ == '__main__':
    if os.environ.get('FLASK_DEBUG') == '1':
        import importlib
        import sys
        
        def reload_handler():
            importlib.reload(sys.modules[__name__])
            main()
        
        def watch_module():
            import time
            last_mtime = os.path.getmtime(__file__)
            while True:
                try:
                    current_mtime = os.path.getmtime(__file__)
                    if current_mtime > last_mtime:
                        print("Detected change, reloading...", flush=True)
                        reload_handler()
                        last_mtime = current_mtime
                    time.sleep(1)
                except Exception as e:
                    print(f"Reload error: {e}", flush=True)
                    time.sleep(1)
        
        import threading
        watcher = threading.Thread(target=watch_module, daemon=True)
        watcher.start()
        
    main()
