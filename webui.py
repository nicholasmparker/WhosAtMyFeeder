from flask import Flask, render_template, request, redirect, url_for, send_file, abort, send_from_directory, jsonify
import sqlite3
import base64
from datetime import datetime, date
import yaml
import requests
from io import BytesIO
from queries import recent_detections, get_daily_summary, get_common_name, get_records_for_date_hour
from queries import get_records_for_scientific_name_and_date, get_earliest_detection_date
import os

app = Flask(__name__, static_folder='static/dist', static_url_path='')
config = None
DBPATH = './data/speciesid.db'
NAMEDBPATH = './birdnames.db'

# API Routes
@app.route('/api/detections/recent')
def api_recent_detections():
    limit = request.args.get('limit', default=5, type=int)
    records = recent_detections(limit)
    return jsonify([dict(record) for record in records])

@app.route('/api/detections/daily-summary/<date>')
def api_daily_summary(date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        summary = get_daily_summary(date_obj)
        return jsonify(summary)
    except ValueError:
        abort(400, description="Invalid date format")

@app.route('/api/detections/by-hour/<date>/<int:hour>')
def api_detections_by_hour(date, hour):
    try:
        records = get_records_for_date_hour(date, hour)
        return jsonify([dict(record) for record in records])
    except ValueError:
        abort(400, description="Invalid date format")

@app.route('/api/detections/by-species/<scientific_name>/<date>')
def api_detections_by_species(scientific_name, date):
    try:
        records = get_records_for_scientific_name_and_date(scientific_name, date)
        return jsonify([dict(record) for record in records])
    except ValueError:
        abort(400, description="Invalid date format")

@app.route('/api/species/<scientific_name>/common-name')
def api_get_common_name(scientific_name):
    common_name = get_common_name(scientific_name)
    if common_name:
        return jsonify({"common_name": common_name})
    abort(404, description="Species not found")

@app.route('/api/earliest-detection-date')
def api_earliest_detection_date():
    date = get_earliest_detection_date()
    return jsonify({"date": date})

# Frigate routes
@app.route('/frigate/<frigate_event>/thumbnail.jpg')
def frigate_thumbnail(frigate_event):
    frigate_url = config['frigate']['frigate_url']
    try:
        response = requests.get(f'{frigate_url}/api/events/{frigate_event}/thumbnail.jpg', stream=True)
        if response.status_code == 200:
            return send_file(response.raw, mimetype=response.headers['Content-Type'])
        else:
            return send_from_directory('static/images', '1x1.png', mimetype='image/png')
    except Exception as e:
        print(f"Error fetching image from frigate: {e}", flush=True)
        abort(500)

@app.route('/frigate/<frigate_event>/snapshot.jpg')
def frigate_snapshot(frigate_event):
    frigate_url = config['frigate']['frigate_url']
    try:
        response = requests.get(f'{frigate_url}/api/events/{frigate_event}/snapshot.jpg', stream=True)
        if response.status_code == 200:
            return send_file(response.raw, mimetype=response.headers['Content-Type'])
        else:
            return send_from_directory('static/images', '1x1.png', mimetype='image/png')
    except Exception as e:
        print(f"Error fetching image from frigate: {e}", flush=True)
        abort(500)

@app.route('/frigate/<frigate_event>/clip.mp4')
def frigate_clip(frigate_event):
    frigate_url = config['frigate']['frigate_url']
    try:
        response = requests.get(f'{frigate_url}/api/events/{frigate_event}/clip.mp4', stream=True)
        if response.status_code == 200:
            return send_file(response.raw, mimetype=response.headers['Content-Type'])
        else:
            return send_from_directory('static/images', '1x1.png', mimetype='image/png')
    except Exception as e:
        print(f"Error fetching clip from frigate: {e}", flush=True)
        abort(500)

# Serve Vue.js frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue_app(path):
    if path and (path.startswith('api/') or path.startswith('frigate/')):
        abort(404)
    
    dist_dir = os.path.join(app.static_folder)
    if path and os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)
    
    return send_from_directory(dist_dir, 'index.html')

def load_config():
    global config
    file_path = './config/config.yml'
    with open(file_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

load_config()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7766)
