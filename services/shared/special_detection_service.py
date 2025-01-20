import sqlite3
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

class SpecialDetectionService:
    def __init__(self, db_path: str = "/data/speciesid.db"):
        self.db_path = db_path

    @contextmanager
    def _get_db_connection(self) -> sqlite3.Connection:
        """Create a database connection using context manager."""
        conn = sqlite3.connect(self.db_path, timeout=20)  # Add timeout to prevent immediate lock errors
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()  # Auto-commit if no exceptions
        except Exception as e:
            conn.rollback()  # Rollback on error
            raise e
        finally:
            conn.close()

    def update_rarity_scores(self) -> None:
        """Update rarity scores for all species based on detection history."""
        with self._get_db_connection() as conn:
            # Get total detection counts for each species
            cursor = conn.execute("""
                SELECT 
                    display_name,
                    COUNT(*) as visit_count,
                    MAX(detection_time) as last_seen
                FROM detections
                WHERE display_name IS NOT NULL
                GROUP BY display_name
            """)
            species_counts = cursor.fetchall()
            
            # Calculate the maximum count for normalization
            max_count = max(row['visit_count'] for row in species_counts) if species_counts else 1
            
            # Update rarity scores for each species
            for species in species_counts:
                # Calculate frequency score (inverse of normalized visits)
                frequency_score = 1 - (species['visit_count'] / max_count)
                
                # Calculate seasonal score based on recent activity
                three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                cursor = conn.execute("""
                    SELECT COUNT(*) as recent_count
                    FROM detections
                    WHERE display_name = ? AND detection_time >= ?
                """, (species['display_name'], three_months_ago))
                recent_count = cursor.fetchone()['recent_count']
                seasonal_score = 1 - (recent_count / species['visit_count']) if species['visit_count'] > 0 else 1
                
                # Update or insert rarity scores
                conn.execute("""
                    INSERT OR REPLACE INTO rarity_scores 
                    (species_id, frequency_score, seasonal_score, last_seen, total_visits)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    species['display_name'],
                    frequency_score,
                    seasonal_score,
                    species['last_seen'],
                    species['visit_count']
                ))

    def evaluate_image_quality(self, detection_id: int, image_data: Dict = None) -> None:
        """
        Evaluate and store image quality metrics for a detection using both local and OpenAI Vision analysis.
        """
        with self._get_db_connection() as conn:
            # Get image path
            cursor = conn.execute("""
                SELECT frigate_event
                FROM detections
                WHERE id = ?
            """, (detection_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"No detection found for ID {detection_id}")
                return
                
            # Get quality scores from both systems
            clarity_score = 0.0
            composition_score = 0.0
            behavior_tags = []
            
            # 1. OpenAI Vision scores (if provided)
            if image_data:
                clarity_score = image_data.get('clarity', 0.0)
                composition_score = image_data.get('composition', 0.0)
                behavior_tags.extend(image_data.get('behaviors', []))
            
            # 2. Local processing scores (from vision_analysis_cache)
            cursor = conn.execute("""
                SELECT clarity_score, composition_score, behavior_tags
                FROM vision_analysis_cache
                WHERE detection_id = ?
            """, (detection_id,))
            local_result = cursor.fetchone()
            
            if local_result:
                # Average with OpenAI scores if available, otherwise use local scores
                if image_data:
                    clarity_score = (clarity_score + local_result['clarity_score']) / 2
                    composition_score = (composition_score + local_result['composition_score']) / 2
                else:
                    clarity_score = local_result['clarity_score']
                    composition_score = local_result['composition_score']
                
                # Combine behavior tags
                if local_result['behavior_tags']:
                    local_behaviors = json.loads(local_result['behavior_tags'])
                    behavior_tags.extend(local_behaviors)
            
            # Calculate visibility score as average of clarity and composition
            visibility_score = (clarity_score + composition_score) / 2
            
            # Remove duplicate behavior tags and convert to JSON
            behavior_tags = list(set(behavior_tags))
            behavior_tags_json = json.dumps(behavior_tags)
            
            # Update image_quality table
            conn.execute("""
                INSERT OR REPLACE INTO image_quality 
                (detection_id, clarity_score, composition_score, behavior_tags, visibility_score)
                VALUES (?, ?, ?, ?, ?)
            """, (detection_id, clarity_score, composition_score, behavior_tags_json, visibility_score))
            
            print(f"Updated quality scores for detection {detection_id}: clarity={clarity_score:.2f}, composition={composition_score:.2f}")

    def create_special_detection(self, detection_id: int) -> Optional[int]:
        """
        Evaluate a detection and create a special detection entry if it qualifies.
        """
        with self._get_db_connection() as conn:
            # Get detection details including rarity and quality scores
            cursor = conn.execute("""
                SELECT 
                    d.*,
                    r.frequency_score,
                    r.seasonal_score,
                    iq.clarity_score,
                    iq.composition_score,
                    iq.visibility_score
                FROM detections d
                LEFT JOIN rarity_scores r ON d.display_name = r.species_id
                LEFT JOIN image_quality iq ON d.id = iq.detection_id
                WHERE d.id = ?
            """, (detection_id,))
            detection = cursor.fetchone()
            
            if not detection:
                print(f"No detection found for ID {detection_id}")
                return None

            # Add image quality if not present
            if not detection['clarity_score']:
                self.evaluate_image_quality(detection_id, {})

            # Determine highlight type based on frequency score
            frequency_score = detection['frequency_score'] or 0
            highlight_type = 'rare' if frequency_score > 0.6 else 'quality'

            # Use raw frequency score for rare birds, detection score for quality birds
            final_score = frequency_score if highlight_type == 'rare' else detection['score']

            # Only create special detection if score is significant
            if final_score > 0.7:  # Threshold for special detection
                try:
                    cursor = conn.execute("""
                        INSERT INTO special_detections 
                        (detection_id, highlight_type, score, created_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (detection_id, highlight_type, final_score))
                    return cursor.lastrowid
                except sqlite3.Error as e:
                    print(f"Database error: {e}")
                    return None
            
            return None

    def get_recent_special_detections(self, limit: int = 10) -> List[Dict]:
        """Get recent special detections with their details."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("""
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
                ORDER BY sd.created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]

    def update_community_votes(self, special_detection_id: int, increment: bool = True) -> None:
        """Update the community vote count for a special detection."""
        with self._get_db_connection() as conn:
            conn.execute("""
                UPDATE special_detections
                SET community_votes = community_votes + ?
                WHERE id = ?
            """, (1 if increment else -1, special_detection_id))

    def toggle_featured_status(self, special_detection_id: int) -> bool:
        """Toggle the featured status of a special detection."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("""
                UPDATE special_detections
                SET featured_status = NOT featured_status
                WHERE id = ?
                RETURNING featured_status
            """, (special_detection_id,))
            result = cursor.fetchone()
            return bool(result['featured_status']) if result else False
