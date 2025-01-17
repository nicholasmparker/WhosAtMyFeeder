import sqlite3
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
from webui import app
import sys
import json
import requests
import aiohttp
import asyncio
from PIL import Image, ImageOps
from io import BytesIO
from queries import get_common_name
from concurrent.futures import ThreadPoolExecutor

classifier = None
config = None
firstmessage = True

DBPATH = './data/speciesid.db'


def classify(image):
    tensor_image = vision.TensorImage.create_from_array(image)
    categories = classifier.classify(tensor_image)
    return categories.classifications[0].categories


def on_connect(client, userdata, flags, rc):
    rc_codes = {
        0: "Connection successful",
        1: "Connection refused - incorrect protocol version",
        2: "Connection refused - invalid client identifier",
        3: "Connection refused - server unavailable",
        4: "Connection refused - bad username or password",
        5: "Connection refused - not authorized"
    }
    status = rc_codes.get(rc, f"Unknown error code: {rc}")
    print(f"MQTT Connection status: {status}", flush=True)
    
    if rc == 0:
        topic = config['frigate']['main_topic'] + "/events"
        print(f"Subscribing to MQTT topic: {topic}", flush=True)
        client.subscribe(topic)
        print(f"Successfully subscribed to {topic}", flush=True)


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"Unexpected MQTT disconnection (code {rc}), attempting to reconnect...", flush=True)
        while True:
            try:
                print("Attempting MQTT reconnection...", flush=True)
                client.reconnect()
                print("MQTT reconnection successful!", flush=True)
                break
            except Exception as e:
                print(f"MQTT reconnection failed: {str(e)}", flush=True)
                print("Retrying in 60 seconds...", flush=True)
                time.sleep(60)
    else:
        print("Clean MQTT disconnection", flush=True)


def set_sublabel(frigate_url, frigate_event, sublabel):
    post_url = frigate_url + "/api/events/" + frigate_event + "/sub_label"
    print(f"Setting Frigate sublabel at URL: {post_url}", flush=True)

    # frigate limits sublabels to 20 characters currently
    if len(sublabel) > 20:
        sublabel = sublabel[:20]
        print(f"Truncated sublabel to 20 chars: {sublabel}", flush=True)

    payload = {
        "subLabel": sublabel
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"Sending POST request to Frigate API: {post_url}", flush=True)
        response = requests.post(post_url, data=json.dumps(payload), headers=headers)
        print(f"Frigate API response status: {response.status_code}", flush=True)
        
        if response.status_code == 200:
            print(f"Successfully set sublabel to: {sublabel}", flush=True)
        else:
            print(f"Failed to set sublabel. Status: {response.status_code}, Response: {response.text}", flush=True)
    except Exception as e:
        print(f"Error communicating with Frigate API: {str(e)}", flush=True)


async def notify_websocket(detection_data):
    """Send detection to WebSocket server"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8765/notify', json=detection_data) as response:
                if response.status != 200:
                    print(f"Failed to notify WebSocket server: {response.status}", flush=True)
    except Exception as e:
        print(f"Error notifying WebSocket server: {str(e)}", flush=True)

def on_message(client, userdata, message):
    loop = asyncio.new_event_loop()
    conn = sqlite3.connect(DBPATH)

    global firstmessage
    if not firstmessage:
        try:
            print("\n=== New MQTT Message ===", flush=True)
            print(f"Topic: {message.topic}", flush=True)
            
            payload_dict = json.loads(message.payload)
            after_data = payload_dict.get('after', {})
            
            print(f"Camera: {after_data.get('camera')}", flush=True)
            print(f"Label: {after_data.get('label')}", flush=True)

            if (after_data['camera'] in config['frigate']['camera'] and
                    after_data['label'] == 'bird'):

                frigate_event = after_data['id']
                frigate_url = config['frigate']['frigate_url']
                snapshot_url = frigate_url + "/api/events/" + frigate_event + "/snapshot.jpg"

                print(f"\nProcessing bird detection:", flush=True)
                print(f"Event ID: {frigate_event}", flush=True)
                print(f"Snapshot URL: {snapshot_url}", flush=True)

                params = {
                    "crop": 1,
                    "quality": 95
                }
                print("Fetching snapshot from Frigate...", flush=True)
                response = requests.get(snapshot_url, params=params)

                if response.status_code == 200:
                    print("Successfully retrieved snapshot", flush=True)
                    image = Image.open(BytesIO(response.content))

                    file_path = "fullsized.jpg"
                    image.save(file_path, format="JPEG")
                    print("Saved full-size image", flush=True)

                    max_size = (224, 224)
                    image.thumbnail(max_size)
                    padded_image = ImageOps.expand(image, border=((max_size[0] - image.size[0]) // 2,
                                                                  (max_size[1] - image.size[1]) // 2),
                                                   fill='black')

                    file_path = "shrunk.jpg"
                    padded_image.save(file_path, format="JPEG")
                    print("Saved processed image for classification", flush=True)

                    np_arr = np.array(padded_image)
                    print("Running classification...", flush=True)
                    categories = classify(np_arr)
                    category = categories[0]
                    index = category.index
                    score = category.score
                    display_name = category.display_name
                    category_name = category.category_name

                    print(f"\nClassification results:", flush=True)
                    print(f"Species: {display_name}", flush=True)
                    print(f"Confidence: {score:.2f}", flush=True)

                    start_time = datetime.fromtimestamp(after_data['start_time'])
                    formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

                    if index != 964 and score > config['classification']['threshold']:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM detections WHERE frigate_event = ?", (frigate_event,))
                        result = cursor.fetchone()

                        if result is None:
                            print("\nStoring new detection in database...", flush=True)
                            cursor.execute("""  
                                INSERT INTO detections (detection_time, detection_index, score,  
                                display_name, category_name, frigate_event, camera_name) VALUES (?, ?, ?, ?, ?, ?, ?)  
                                """, (formatted_start_time, index, score, display_name, category_name, frigate_event, after_data['camera']))
                            set_sublabel(frigate_url, frigate_event, get_common_name(display_name))
                            print("Successfully stored new detection", flush=True)
                            
                            # Prepare detection data for WebSocket
                            detection_data = {
                                "common_name": get_common_name(display_name),
                                "scientific_name": display_name,
                                "score": score,
                                "frigate_event": frigate_event,
                                "timestamp": formatted_start_time
                            }
                            
                            # Send to WebSocket server asynchronously
                            loop.run_until_complete(notify_websocket(detection_data))
                        else:
                            print("\nChecking existing detection...", flush=True)
                            existing_score = result[3]
                            if score > existing_score:
                                print(f"Updating record (new score {score:.2f} > old score {existing_score:.2f})", flush=True)
                                cursor.execute("""  
                                    UPDATE detections  
                                    SET detection_time = ?, detection_index = ?, score = ?, display_name = ?, category_name = ?  
                                    WHERE frigate_event = ?  
                                    """, (formatted_start_time, index, score, display_name, category_name, frigate_event))
                                set_sublabel(frigate_url, frigate_event, get_common_name(display_name))
                            else:
                                print(f"Keeping existing record (new score {score:.2f} <= old score {existing_score:.2f})", flush=True)
                            
                            loop.close()

                        conn.commit()
                        print("Database transaction complete", flush=True)

                else:
                    print(f"Failed to retrieve snapshot. Status: {response.status_code}, Response: {response.text}", flush=True)

        except Exception as e:
            print(f"Error processing message: {str(e)}", flush=True)
            import traceback
            print(traceback.format_exc(), flush=True)

    else:
        firstmessage = False
        print("Skipping first MQTT message (connection message)", flush=True)

    conn.close()


def setupdb():
    print("\nSetting up database...", flush=True)
    conn = sqlite3.connect(DBPATH)
    cursor = conn.cursor()
    cursor.execute("""    
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
    """)
    conn.commit()
    print("Database setup complete", flush=True)
    conn.close()


def load_config():
    global config
    file_path = './config/config.yml'
    print(f"\nLoading configuration from {file_path}...", flush=True)
    with open(file_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    print("Configuration loaded successfully", flush=True)


def run_webui():
    print("\nStarting Flask web application...", flush=True)
    print(f"Host: {config['webui']['host']}", flush=True)
    print(f"Port: {config['webui']['port']}", flush=True)
    app.run(debug=False, host=config['webui']['host'], port=config['webui']['port'])


def run_mqtt_client():
    print("\nInitializing MQTT client...", flush=True)
    print(f"MQTT Server: {config['frigate']['mqtt_server']}", flush=True)
    
    now = datetime.now()
    current_time = now.strftime("%Y%m%d%H%M%S")
    client_id = "birdspeciesid" + current_time
    print(f"Client ID: {client_id}", flush=True)
    
    client = mqtt.Client(client_id)
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect

    if config['frigate']['mqtt_auth']:
        username = config['frigate']['mqtt_username']
        print(f"Using MQTT authentication with username: {username}", flush=True)
        client.username_pw_set(username, config['frigate']['mqtt_password'])

    try:
        print(f"Connecting to MQTT server: {config['frigate']['mqtt_server']}", flush=True)
        client.connect(config['frigate']['mqtt_server'])
        print("Starting MQTT loop...", flush=True)
        client.loop_forever()
    except Exception as e:
        print(f"Error in MQTT client: {str(e)}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)


def main():
    print("\n=== Starting Bird Species Identification System ===", flush=True)
    now = datetime.now()
    current_time = now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(f"Start Time: {current_time}", flush=True)
    print(f"Python Version: {sys.version}", flush=True)

    load_config()

    print("\nInitializing TFLite model...", flush=True)
    base_options = core.BaseOptions(
        file_name=config['classification']['model'], use_coral=False, num_threads=4)
    classification_options = processor.ClassificationOptions(
        max_results=1, score_threshold=0)
    options = vision.ImageClassifierOptions(
        base_options=base_options, classification_options=classification_options)

    global classifier
    classifier = vision.ImageClassifier.create_from_options(options)
    print("TFLite model initialized successfully", flush=True)

    setupdb()
    
    print("\nStarting multiprocessing...", flush=True)
    flask_process = multiprocessing.Process(target=run_webui)
    mqtt_process = multiprocessing.Process(target=run_mqtt_client)

    flask_process.start()
    print("Flask process started", flush=True)
    mqtt_process.start()
    print("MQTT process started", flush=True)

    flask_process.join()
    mqtt_process.join()


if __name__ == '__main__':
    print("Starting main process", flush=True)
    main()
