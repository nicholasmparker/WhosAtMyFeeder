import sqlite3
from datetime import datetime, timedelta
import yaml
from pyowm import OWM
from pyowm.utils import timestamps
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self, config_path='config/config.yml', db_path='data/speciesid.db'):
        self.db_path = db_path
        self.config = self._load_config(config_path)
        self.owm = OWM(self.config['weather']['api_key'])
        self.mgr = self.owm.weather_manager()
        self.lat = self.config['weather']['location']['lat']
        self.lon = self.config['weather']['location']['lon']
        self.units = self.config['weather'].get('units', 'metric')  # Default to metric if not specified
        self._verify_database()

    def _verify_database(self):
        """Verify that the database exists and has the required tables, creating them if needed."""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check and create weather_data table if needed
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weather_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        temperature REAL,
                        feels_like REAL,
                        humidity INTEGER,
                        pressure INTEGER,
                        wind_speed REAL,
                        wind_direction INTEGER,
                        precipitation REAL,
                        cloud_cover INTEGER,
                        visibility INTEGER,
                        weather_condition TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index on weather timestamp
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_weather_timestamp 
                    ON weather_data(timestamp)
                """)
                
                # Check and create detection_weather table if needed
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detection_weather (
                        detection_id INTEGER,
                        weather_id INTEGER,
                        FOREIGN KEY (detection_id) REFERENCES detections(id),
                        FOREIGN KEY (weather_id) REFERENCES weather_data(id)
                    )
                """)
                
                conn.commit()
                logger.info("Database verification successful - all required tables exist or were created")
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            raise

    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _get_db_connection(self):
        """Create a database connection."""
        try:
            logger.info(f"Attempting to connect to database at: {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            logger.info("Database connection successful")
            return conn
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Database connection error: {str(e)}\nTraceback:\n{error_details}")
            raise

    def fetch_current_weather(self):
        """Fetch current weather data and store it in the database."""
        try:
            observation = self.mgr.weather_at_coords(self.lat, self.lon)
            weather = observation.weather
            
            # Extract weather data
            temp_unit = 'fahrenheit' if self.units == 'imperial' else 'celsius'
            data = {
                'timestamp': datetime.utcnow(),
                'temperature': weather.temperature(temp_unit).get('temp'),
                'feels_like': weather.temperature(temp_unit).get('feels_like'),
                'units': self.units,  # Include units in response
                'humidity': weather.humidity,
                'pressure': weather.pressure['press'],
                'wind_speed': weather.wind()['speed'],
                'wind_direction': weather.wind().get('deg', 0),
                'precipitation': weather.rain.get('1h', 0.0),
                'cloud_cover': weather.clouds,
                'visibility': weather.visibility_distance,
                'weather_condition': weather.status.lower()
            }
            
            # Store in database
            self._store_weather_data(data)
            logger.info(f"Stored weather data: {data}")
            return {
                **data,
                'units': self.units  # Include units in response
            }
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return None

    def _store_weather_data(self, data):
        """Store weather data in the database."""
        query = """
        INSERT INTO weather_data (
            timestamp, temperature, feels_like, humidity, pressure,
            wind_speed, wind_direction, precipitation, cloud_cover,
            visibility, weather_condition
        ) VALUES (
            :timestamp, :temperature, :feels_like, :humidity, :pressure,
            :wind_speed, :wind_direction, :precipitation, :cloud_cover,
            :visibility, :weather_condition
        )
        """
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, data)
            weather_id = cursor.lastrowid
            
            # Link to any detections in the same hour
            self._link_weather_to_detections(cursor, weather_id, data['timestamp'])
            conn.commit()

    def _link_weather_to_detections(self, cursor, weather_id, timestamp):
        """Link weather data to detections in the same hour."""
        query = """
        INSERT INTO detection_weather (detection_id, weather_id)
        SELECT id, ?
        FROM detections
        WHERE strftime('%Y-%m-%d %H', detection_time) = strftime('%Y-%m-%d %H', ?)
        AND id NOT IN (SELECT detection_id FROM detection_weather)
        """
        cursor.execute(query, (weather_id, timestamp))

    def get_weather_for_detection(self, detection_id):
        """Get weather data for a specific detection."""
        query = """
        SELECT w.*
        FROM weather_data w
        JOIN detection_weather dw ON w.id = dw.weather_id
        WHERE dw.detection_id = ?
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (detection_id,))
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
        return None

    def get_weather_correlation(self, start_date, end_date, species=None):
        """Get correlation between weather conditions and bird activity."""
        species_clause = "AND d.display_name = ?" if species else ""
        params = [start_date, end_date]
        if species:
            params.append(species)

        query = f"""
        SELECT 
            w.temperature,
            w.wind_speed,
            w.precipitation,
            w.cloud_cover,
            COUNT(d.id) as detection_count,
            strftime('%H', w.timestamp) as hour
        FROM weather_data w
        LEFT JOIN detection_weather dw ON w.id = dw.weather_id
        LEFT JOIN detections d ON dw.detection_id = d.id
        WHERE w.timestamp BETWEEN ? AND ?
        {species_clause}
        GROUP BY 
            strftime('%Y-%m-%d %H', w.timestamp),
            w.temperature,
            w.wind_speed,
            w.precipitation,
            w.cloud_cover
        ORDER BY w.timestamp
        """

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return {
                'results': results,
                'units': self.units
            }

    def get_weather_patterns(self, species=None, days=30):
        """Analyze weather patterns during bird activity."""
        with self._get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                species_clause = "AND d.display_name = ?" if species else ""
                params = [days]
                if species:
                    params.append(species)

                # First check if we have any weather data
                check_query = """
                SELECT COUNT(*) FROM weather_data w
                WHERE datetime(w.timestamp) >= datetime('now', '-' || ? || ' days')
                """
                cursor.execute(check_query, [days])
                weather_count = cursor.fetchone()[0]
                
                if weather_count == 0:
                    logger.info("No weather data found for the specified period")
                    return {
                        'patterns': [],
                        'insights': ["No weather data available for the specified period."],
                        'units': self.units
                    }

                # Then check if we have any detections
                check_query = """
                SELECT COUNT(*) FROM detections d
                JOIN detection_weather dw ON d.id = dw.detection_id
                JOIN weather_data w ON dw.weather_id = w.id
                WHERE datetime(w.timestamp) >= datetime('now', '-' || ? || ' days')
                """
                params = [days]
                if species:
                    check_query += " AND d.display_name = ?"
                    params.append(species)
                    
                cursor.execute(check_query, params)
                detection_count = cursor.fetchone()[0]
                
                if detection_count == 0:
                    logger.info("No detections found for the specified period")
                    return {
                        'patterns': [],
                        'insights': ["No bird activity detected during this period."],
                        'units': self.units
                    }

                # If we have both weather data and detections, proceed with the main query
                query = f"""
                SELECT 
                    w.weather_condition,
                    ROUND(AVG(w.temperature), 1) as avg_temp,
                    ROUND(AVG(w.wind_speed), 1) as avg_wind,
                    COUNT(d.id) as total_detections,
                    ROUND(COUNT(d.id) * 100.0 / SUM(COUNT(d.id)) OVER (), 1) as activity_percentage
                FROM weather_data w
                LEFT JOIN detection_weather dw ON w.id = dw.weather_id
                LEFT JOIN detections d ON dw.detection_id = d.id
                WHERE datetime(w.timestamp) >= datetime('now', '-' || ? || ' days')
                {species_clause}
                GROUP BY w.weather_condition
                HAVING total_detections > 0
                ORDER BY total_detections DESC
                """

                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                if not results:
                    return {
                        'patterns': [],
                        'insights': ["Not enough data to generate insights."],
                        'units': self.units
                    }

                insights = []
                
                # Most active conditions
                top_condition = results[0]
                insights.append(
                    f"Birds are most active during {top_condition['weather_condition']} conditions "
                    f"({top_condition['activity_percentage']}% of activity)"
                )

                # Temperature insights
                temp_range = self._analyze_temperature_range(species)
                if temp_range:
                    unit = '°F' if self.units == 'imperial' else '°C'
                    insights.append(
                        f"Preferred temperature range: {temp_range['min_temp']}{unit} to {temp_range['max_temp']}{unit} "
                        f"({temp_range['activity_percentage']}% of activity)"
                    )

                # Wind insights
                wind_impact = self._analyze_wind_impact(species)
                if wind_impact:
                    speed_unit = 'mph' if self.units == 'imperial' else 'm/s'
                    insights.append(
                        f"Activity {wind_impact['trend']} when wind speeds are "
                        f"{wind_impact['threshold']} {speed_unit}"
                    )

                return {
                    'patterns': results,
                    'insights': insights,
                    'units': self.units
                }

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Error getting weather patterns: {str(e)}\nTraceback:\n{error_details}")
                # Log the query and parameters for debugging
                logger.error(f"Failed query: {query}")
                logger.error(f"Query parameters: {params}")
                return {
                    'patterns': [],
                    'insights': [f"Error analyzing weather patterns: {str(e)}"],
                    'units': self.units
                }

    def _analyze_temperature_range(self, species=None):
        """Analyze preferred temperature ranges."""
        species_clause = "AND d.display_name = ?" if species else ""
        params = [30]  # Last 30 days
        if species:
            params.append(species)

        query = f"""
        SELECT 
            MIN(temperature) as min_temp,
            MAX(temperature) as max_temp,
            COUNT(d.id) as detection_count,
            COUNT(d.id) * 100.0 / SUM(COUNT(d.id)) OVER () as percentage
        FROM weather_data w
        JOIN detection_weather dw ON w.id = dw.weather_id
        JOIN detections d ON dw.detection_id = d.id
        WHERE datetime(w.timestamp) >= datetime('now', '-' || ? || ' days')
        {species_clause}
        GROUP BY 
            ROUND((temperature - 5) / 10) * 10
        ORDER BY detection_count DESC
        LIMIT 1
        """

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            if result:
                return {
                    'min_temp': round(result[0], 1),
                    'max_temp': round(result[1], 1),
                    'activity_percentage': round(result[3], 1)
                }
        return None

    def _analyze_wind_impact(self, species=None):
        """Analyze impact of wind speed on activity."""
        species_clause = "AND d.display_name = ?" if species else ""
        params = [30]  # Last 30 days
        if species:
            params.append(species)

        # Wind speed thresholds (m/s for metric, mph for imperial)
        low_threshold = 11 if self.units == 'imperial' else 5
        moderate_threshold = 22 if self.units == 'imperial' else 10

        query = f"""
        WITH wind_activity AS (
            SELECT 
                CASE 
                    WHEN wind_speed <= {low_threshold} THEN 'low'
                    WHEN wind_speed <= {moderate_threshold} THEN 'moderate'
                    ELSE 'high'
                END as wind_category,
                COUNT(d.id) as detection_count
            FROM weather_data w
            JOIN detection_weather dw ON w.id = dw.weather_id
            JOIN detections d ON dw.detection_id = d.id
            WHERE datetime(w.timestamp) >= datetime('now', '-' || ? || ' days')
            {species_clause}
            GROUP BY wind_category
        )
        SELECT 
            wind_category,
            detection_count,
            detection_count * 100.0 / SUM(detection_count) OVER () as percentage
        FROM wind_activity
        ORDER BY detection_count DESC
        """

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            if results:
                top_category = results[0]
                speed_unit = 'mph' if self.units == 'imperial' else 'm/s'
                if top_category[0] == 'low':
                    return {'trend': 'peaks', 'threshold': f'below {low_threshold} {speed_unit}'}
                elif top_category[0] == 'moderate':
                    return {'trend': 'is optimal', 'threshold': f'between {low_threshold} and {moderate_threshold} {speed_unit}'}
                else:
                    return {'trend': 'continues', 'threshold': f'above {moderate_threshold} {speed_unit}'}
        return None
