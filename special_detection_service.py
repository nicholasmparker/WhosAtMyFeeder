import sqlite3
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple

class SpecialDetectionService:
    def __init__(self, db_path: str = "/data/speciesid.db"):
        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Create a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def update_rarity_scores(self) -> None:
        """Update rarity scores for all species based on detection history."""
        conn = self._get_db_connection()
        try:
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
            
            conn.commit()
        finally:
            conn.close()

    def evaluate_image_quality(self, detection_id: int, image_data: Dict) -> None:
        """
        Evaluate and store image quality metrics for a detection.
        
        Args:
            detection_id: The ID of the detection
            image_data: Dictionary containing image analysis results
        """
        # For now, use basic metrics
        clarity_score = image_data.get('clarity', 0.8)  # Default to good quality
        composition_score = image_data.get('composition', 0.8)
        visibility_score = image_data.get('visibility', 0.8)
        behavior_tags = json.dumps(image_data.get('behaviors', []))

        conn = self._get_db_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO image_quality 
                (detection_id, clarity_score, composition_score, behavior_tags, visibility_score)
                VALUES (?, ?, ?, ?, ?)
            """, (detection_id, clarity_score, composition_score, behavior_tags, visibility_score))
            conn.commit()
        finally:
            conn.close()

    def create_special_detection(self, detection_id: int) -> Optional[int]:
        """
        Evaluate a detection and create a special detection entry if it qualifies.
        """
        conn = self._get_db_connection()
        try:
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
                    conn.commit()
                    return cursor.lastrowid
                except sqlite3.Error as e:
                    print(f"Database error: {e}")
                    return None
            
            return None
        finally:
            conn.close()

    def get_recent_special_detections(self, limit: int = 10) -> List[Dict]:
        """Get recent special detections with their details."""
        conn = self._get_db_connection()
        try:
            cursor = conn.execute("""
                SELECT 
                    sd.*,
                    d.detection_time,
                    d.display_name,
                    d.score as detection_score,
                    d.frigate_event,  -- Add frigate_event to the query
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
        finally:
            conn.close()

    def update_community_votes(self, special_detection_id: int, increment: bool = True) -> None:
        """Update the community vote count for a special detection."""
        conn = self._get_db_connection()
        try:
            conn.execute("""
                UPDATE special_detections
                SET community_votes = community_votes + ?
                WHERE id = ?
            """, (1 if increment else -1, special_detection_id))
            conn.commit()
        finally:
            conn.close()

    def toggle_featured_status(self, special_detection_id: int) -> bool:
        """Toggle the featured status of a special detection."""
        conn = self._get_db_connection()
        try:
            cursor = conn.execute("""
                UPDATE special_detections
                SET featured_status = NOT featured_status
                WHERE id = ?
                RETURNING featured_status
            """, (special_detection_id,))
            result = cursor.fetchone()
            conn.commit()
            return bool(result['featured_status']) if result else False
        finally:
            conn.close()
