from flask import Flask, render_template, request, redirect, url_for, send_file, abort, send_from_directory, jsonify
import sqlite3
import base64
from datetime import datetime, date
import yaml
import requests
from io import BytesIO
from flask_cors import CORS
from shared.queries import recent_detections, get_daily_summary, get_common_name, get_records_for_date_hour
from shared.queries import get_records_for_scientific_name_and_date, get_earliest_detection_date
from shared.weather_service import WeatherService
from shared.special_detection_service import SpecialDetectionService
from shared.image_processing import ImageProcessingService
import os
import json

app = Flask(__name__, static_folder='static/dist', static_url_path='')
CORS(app)
config = None
DBPATH = '/data/speciesid.db'
weather_service = None
special_detection_service = None
image_processing_service = None

# Custom JSON encoder to handle SQLite Row objects
class SQLiteJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, sqlite3.Row):
            return {k: obj[k] for k in obj.keys()}
        return super().default(obj)

app.json_encoder = SQLiteJSONEncoder

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
    global config, weather_service, special_detection_service, image_processing_service
    file_path = './config/config.yml'
    with open(file_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    weather_service = WeatherService(file_path, DBPATH)
    special_detection_service = SpecialDetectionService(DBPATH)
    image_processing_service = ImageProcessingService(file_path)

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
        date = request.args.get('date', type=str)
        hour = request.args.get('hour', type=str)
        metric = request.args.get('metric', type=str, default='temperature')
        
        if not date or hour is None:
            abort(400, description="date and hour are required")
        
        # Convert hour-based request to a time range
        try:
            dt = datetime.strptime(f"{date} {hour}:00:00", "%Y-%m-%d %H:%M:%S")
            start_date = dt.strftime("%Y-%m-%d %H:00:00")
            end_date = dt.strftime("%Y-%m-%d %H:59:59")
        except ValueError:
            abort(400, description="Invalid date or hour format")
            
        data = weather_service.get_weather_correlation(start_date, end_date)
        
        # Format response for the chart
        correlations = []
        for result in data['results']:
            correlations.append({
                'timestamp': dt.strftime("%Y-%m-%d %H:%M:%S"),
                'metric_value': result.get(metric, 0),
                'detection_count': result['detection_count'],
                'weather_condition': result.get('weather_condition', '')
            })
            
        # Generate insight based on the correlation
        total_detections = sum(r['detection_count'] for r in correlations)
        if total_detections > 0:
            max_period = max(correlations, key=lambda x: x['detection_count'])
            insight = f"Peak activity occurred when {metric} was {max_period['metric_value']}"
            if metric == 'temperature':
                insight += f"°{'F' if data['units'] == 'imperial' else 'C'}"
            elif metric == 'wind_speed':
                insight += f" {'mph' if data['units'] == 'imperial' else 'm/s'}"
            elif metric in ['humidity', 'cloud_cover']:
                insight += "%"
        else:
            insight = "No bird activity detected during this period"
            
        return jsonify({
            'correlations': correlations,
            'insight': insight,
            'units': data['units']
        })
    except Exception as e:
        abort(500, description=str(e))

@app.route('/api/weather/patterns')
def api_weather_patterns():
    try:
        species = request.args.get('species', type=str)
        days = request.args.get('days', default=30, type=int)
        
        result = weather_service.get_weather_patterns(species, days)
        return jsonify(result)
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
        if highlight_type not in ['rare', 'quality', 'behavior']:
            abort(400, description="Invalid highlight type")
            
        conn = sqlite3.connect(DBPATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                sd.*,
                d.detection_time,
                d.display_name,
                d.score as detection_score,
                d.frigate_event,
                b.common_name,
                iq.clarity_score,
                iq.composition_score,
                iq.behavior_tags
            FROM special_detections sd
            JOIN detections d ON sd.detection_id = d.id
            JOIN birdnames b ON d.display_name = b.scientific_name
            LEFT JOIN image_quality iq ON d.id = iq.detection_id
            WHERE sd.highlight_type = ?
            ORDER BY sd.score DESC
            LIMIT 50
        """, (highlight_type,))
        
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(results)
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
    except Exception as e:
        print(f"Error toggling featured status: {e}", flush=True)
        abort(500, description=str(e))

# Image Processing API endpoints
@app.route('/api/image/quality/<int:detection_id>')
def api_image_quality(detection_id):
    """Get image quality assessment for a detection."""
    try:
        # Get image path from detection
        conn = sqlite3.connect(DBPATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT frigate_event
            FROM detections
            WHERE id = ?
        """, (detection_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            abort(404, description="Detection not found")
            
        # Construct image path
        frigate_url = config['frigate']['frigate_url']
        image_path = f"{frigate_url}/api/events/{result[0]}/snapshot.jpg"
        
        # Process image quality
        quality_result = image_processing_service.process_image(image_path)
        return jsonify(quality_result)
    except Exception as e:
        print(f"Error assessing image quality: {e}", flush=True)
        abort(500, description=str(e))

@app.route('/api/enhanced/<frigate_event>/snapshot.jpg')
def enhanced_snapshot(frigate_event):
    """Serve enhanced snapshot image."""
    try:
        # Get the enhanced image path from the database
        conn = sqlite3.connect(DBPATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT enhanced_path
            FROM image_quality
            JOIN detections ON image_quality.detection_id = detections.id
            WHERE detections.frigate_event = ? AND enhancement_status = 'completed'
        """, (frigate_event,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            enhanced_path = result[0]
            if os.path.exists(enhanced_path):
                return send_file(enhanced_path, mimetype='image/jpeg')

        # If enhanced image not found, fall back to original
        return frigate_snapshot(frigate_event)
    except Exception as e:
        print(f"Error serving enhanced snapshot: {e}", flush=True)
        abort(500)

@app.route('/api/enhanced/<frigate_event>/thumbnail.jpg')
def enhanced_thumbnail(frigate_event):
    """Serve enhanced thumbnail image."""
    try:
        # Get the enhanced thumbnail path from the database
        conn = sqlite3.connect(DBPATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT enhanced_thumbnail_path
            FROM image_quality
            JOIN detections ON image_quality.detection_id = detections.id
            WHERE detections.frigate_event = ? AND enhancement_status = 'completed'
        """, (frigate_event,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            enhanced_path = result[0]
            if os.path.exists(enhanced_path):
                return send_file(enhanced_path, mimetype='image/jpeg')

        # If enhanced thumbnail not found, fall back to original
        return frigate_thumbnail(frigate_event)
    except Exception as e:
        print(f"Error serving enhanced thumbnail: {e}", flush=True)
        abort(500)

@app.route('/api/image/enhance/<int:detection_id>')
def api_enhance_image(detection_id):
    """Enhance image for a detection if needed."""
    try:
        # Get image path from detection
        conn = sqlite3.connect(DBPATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT frigate_event
            FROM detections
            WHERE id = ?
        """, (detection_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            abort(404, description="Detection not found")
            
        # Construct image path
        frigate_url = config['frigate']['frigate_url']
        image_path = f"{frigate_url}/api/events/{result[0]}/snapshot.jpg"
        
        # Process and enhance image
        enhancement_result = image_processing_service.process_image(image_path)
        
        # Return enhanced image path if enhancement was performed
        if enhancement_result['enhanced']:
            return jsonify({
                "enhanced": True,
                "original_path": f"/frigate/{result[0]}/snapshot.jpg",
                "enhanced_path": enhancement_result['enhanced_path'],
                "quality_scores": enhancement_result['quality_scores'],
                "enhanced_quality_scores": enhancement_result.get('enhanced_quality_scores')
            })
        else:
            return jsonify({
                "enhanced": False,
                "message": "Image quality above threshold, no enhancement needed",
                "quality_scores": enhancement_result['quality_scores']
            })
    except Exception as e:
        print(f"Error enhancing image: {e}", flush=True)
        abort(500, description=str(e))

@app.route('/api/image/batch-process', methods=['POST'])
def api_batch_process_images():
    """Process multiple images for quality assessment and enhancement."""
    try:
        data = request.get_json()
        if not isinstance(data, dict) or 'detection_ids' not in data:
            abort(400, description="Missing detection_ids parameter")
            
        detection_ids = data['detection_ids']
        results = []
        
        for detection_id in detection_ids:
            try:
                # Get image path
                conn = sqlite3.connect(DBPATH)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT frigate_event
                    FROM detections
                    WHERE id = ?
                """, (detection_id,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    frigate_url = config['frigate']['frigate_url']
                    image_path = f"{frigate_url}/api/events/{result[0]}/snapshot.jpg"
                    
                    # Process image
                    process_result = image_processing_service.process_image(image_path)
                    results.append({
                        "detection_id": detection_id,
                        "success": True,
                        "result": process_result
                    })
                else:
                    results.append({
                        "detection_id": detection_id,
                        "success": False,
                        "error": "Detection not found"
                    })
            except Exception as e:
                results.append({
                    "detection_id": detection_id,
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "processed": len(results),
            "results": results
        })
    except Exception as e:
        print(f"Error in batch processing: {e}", flush=True)
        abort(500, description=str(e))

if __name__ == '__main__':
    # Only run Flask directly when this file is run directly (not when imported)
    app.run(host='0.0.0.0', port=7766, debug=False)
