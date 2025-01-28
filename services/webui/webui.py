from flask import Flask, request, send_file, abort, send_from_directory, jsonify
import sqlite3
import yaml
import requests
import os
from flask_cors import CORS
from shared.special_detection_service import SpecialDetectionService
from shared.weather_service import WeatherService
from shared.image_processing_service import ImageProcessingService

app = Flask(__name__, static_folder='static/dist', static_url_path='')
CORS(app)
config = None
DBPATH = '/data/speciesid.db'

# Initialize services
special_detection_service = None
weather_service = None
image_processing_service = None

def load_config():
    global config, weather_service, special_detection_service, image_processing_service
    file_path = './config/config.yml'
    with open(file_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    special_detection_service = SpecialDetectionService(DBPATH)
    weather_service = WeatherService(file_path, DBPATH)
    image_processing_service = ImageProcessingService(file_path)

load_config()

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"})

# Special Detection API endpoints
@app.route('/api/special-detections/recent')
def api_recent_special_detections():
    """Get recent special detections."""
    try:
        limit = request.args.get('limit', default=10, type=int)
        detections = special_detection_service.get_recent_special_detections(limit)
        return jsonify(detections)
    except Exception as e:
        print(f"Error fetching recent special detections: {e}", flush=True)
        abort(500, description=str(e))

@app.route('/api/special-detections/by-type/<highlight_type>')
def api_special_detections_by_type(highlight_type):
    """Get special detections by type (rare/quality/behavior)."""
    try:
        detections = special_detection_service.get_special_detections_by_type(highlight_type)
        return jsonify(detections)
    except ValueError as e:
        abort(400, description=str(e))
    except Exception as e:
        print(f"Error fetching special detections by type: {e}", flush=True)
        abort(500, description=str(e))

@app.route('/api/special-detections/<int:special_detection_id>/vote', methods=['POST'])
def api_vote_special_detection(special_detection_id):
    """Update community votes for a special detection."""
    try:
        data = request.get_json()
        if not isinstance(data, dict) or 'increment' not in data:
            abort(400, description="Missing increment parameter")
            
        special_detection_service.update_community_votes(
            special_detection_id,
            increment=data['increment']
        )
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating votes: {e}", flush=True)
        abort(500, description=str(e))

@app.route('/api/special-detections/<int:special_detection_id>/featured', methods=['POST'])
def api_toggle_featured_status(special_detection_id):
    """Toggle featured status of a special detection."""
    try:
        new_status = special_detection_service.toggle_featured_status(special_detection_id)
        return jsonify({"featured": new_status})
    except ValueError as e:
        abort(404, description=str(e))
    except Exception as e:
        print(f"Error toggling featured status: {e}", flush=True)
        abort(500, description=str(e))

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

# Enhanced image routes
@app.route('/api/enhanced/<frigate_event>/snapshot.jpg')
def enhanced_snapshot(frigate_event):
    """Serve enhanced snapshot image."""
    try:
        enhanced_path = f"/data/images/enhanced/{frigate_event}/snapshot.jpg"
        if os.path.exists(enhanced_path):
            return send_file(enhanced_path, mimetype='image/jpeg')
        return frigate_snapshot(frigate_event)
    except Exception as e:
        print(f"Error serving enhanced snapshot: {e}", flush=True)
        abort(500)

@app.route('/api/enhanced/<frigate_event>/thumbnail.jpg')
def enhanced_thumbnail(frigate_event):
    """Serve enhanced thumbnail image."""
    try:
        enhanced_path = f"/data/images/enhanced/{frigate_event}/thumbnail.jpg"
        if os.path.exists(enhanced_path):
            return send_file(enhanced_path, mimetype='image/jpeg')
        return frigate_thumbnail(frigate_event)
    except Exception as e:
        print(f"Error serving enhanced thumbnail: {e}", flush=True)
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

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=7766, debug=debug, use_reloader=debug)
