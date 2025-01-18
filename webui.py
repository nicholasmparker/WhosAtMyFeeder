from flask import Flask, render_template, request, redirect, url_for, send_file, abort, send_from_directory, jsonify
import sqlite3
import base64
from datetime import datetime, date
import yaml
import requests
from io import BytesIO
from flask_cors import CORS
from queries import recent_detections, get_daily_summary, get_common_name, get_records_for_date_hour
from queries import get_records_for_scientific_name_and_date, get_earliest_detection_date
from weather_service import WeatherService
import os

app = Flask(__name__, static_folder='static/dist', static_url_path='')
CORS(app)
config = None
DBPATH = './data/speciesid.db'
weather_service = None

# API Routes
@app.route('/api/detections/recent')
def api_recent_detections():
    limit = request.args.get('limit', default=5, type=int)
    records = recent_detections(limit)
    return jsonify([dict(record) for record in records])

@app.route('/api/detections/daily-summary/<date>')
def api_daily_summary(date):
    try:
        print(f"\nFetching daily summary for date: {date}", flush=True)
        
        # Check if we have any data in the database
        conn = sqlite3.connect(DBPATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM detections")
        total_count = cursor.fetchone()[0]
        print(f"Total records in database: {total_count}", flush=True)
        
        # Check if we have data for this specific date
        cursor.execute("SELECT COUNT(*) FROM detections WHERE DATE(detection_time) = ?", (date,))
        date_count = cursor.fetchone()[0]
        print(f"Records for {date}: {date_count}", flush=True)
        
        # Get some sample records if they exist
        cursor.execute("SELECT * FROM detections WHERE DATE(detection_time) = ? LIMIT 3", (date,))
        samples = cursor.fetchall()
        if samples:
            print(f"Sample records for {date}:", flush=True)
            for sample in samples:
                print(f"  {sample}", flush=True)
        
        conn.close()
        
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        summary = get_daily_summary(date_obj)
        print(f"Summary data: {summary}", flush=True)
        return jsonify(summary)
    except ValueError as e:
        print(f"Error processing date: {e}", flush=True)
        abort(400, description="Invalid date format")
    except Exception as e:
        print(f"Error getting daily summary: {e}", flush=True)
        abort(500, description="Internal server error")

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

@app.route('/api/species')
def api_species():
    """Get list of all species with their common names."""
    conn = sqlite3.connect(DBPATH)
    cursor = conn.cursor()
    cursor.execute("SELECT scientific_name, common_name FROM birdnames")
    species = [{"scientific_name": row[0], "common_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(species)

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
    global config, weather_service
    file_path = './config/config.yml'
    with open(file_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    weather_service = WeatherService(file_path, DBPATH)

load_config()

# Weather API endpoints
@app.route('/api/weather/current')
def api_current_weather():
    try:
        data = weather_service.fetch_current_weather()
        if data:
            return jsonify(data)
        abort(500, description="Failed to fetch weather data")
    except Exception as e:
        abort(500, description=str(e))

@app.route('/api/weather/correlation')
def api_weather_correlation():
    try:
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        species = request.args.get('species', type=str)
        
        if not start_date or not end_date:
            abort(400, description="start_date and end_date are required")
            
        data = weather_service.get_weather_correlation(start_date, end_date, species)
        return jsonify(data)
    except Exception as e:
        abort(500, description=str(e))

@app.route('/api/weather/patterns')
def api_weather_patterns():
    try:
        species = request.args.get('species', type=str)
        days = request.args.get('days', default=30, type=int)
        
        patterns = weather_service.get_weather_patterns(species, days)
        insights = weather_service.generate_insights(species)
        
        return jsonify({
            'patterns': patterns,
            'insights': insights
        })
    except Exception as e:
        abort(500, description=str(e))

@app.route('/api/weather/detection/<int:detection_id>')
def api_detection_weather(detection_id):
    try:
        data = weather_service.get_weather_for_detection(detection_id)
        if data:
            return jsonify(data)
        abort(404, description="Weather data not found for this detection")
    except Exception as e:
        abort(500, description=str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7766)
