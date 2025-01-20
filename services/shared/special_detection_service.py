from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from .database import db

class SpecialDetectionService:
    def __init__(self, db_path: str = "/data/speciesid.db"):
        # db_path kept for compatibility but not used since we use the shared db manager
        pass

    def update_rarity_scores(self) -> None:
        """Update rarity scores for all species based on detection history."""
        def do_update(session):
            # Get total detection counts for each species
            species_counts = session.execute(text("""
                SELECT 
                    display_name,
                    COUNT(*) as visit_count,
                    MAX(detection_time) as last_seen
                FROM detections
                WHERE display_name IS NOT NULL
                GROUP BY display_name
            """)).fetchall()
            
            # Calculate the maximum count for normalization
            max_count = max(row[1] for row in species_counts) if species_counts else 1
            
            # Update rarity scores for each species
            for species in species_counts:
                # Calculate frequency score (inverse of normalized visits)
                frequency_score = 1 - (species[1] / max_count)
                
                # Calculate seasonal score based on recent activity
                three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                recent_count = session.execute(
                    text("""
                        SELECT COUNT(*) as recent_count
                        FROM detections
                        WHERE display_name = :name AND detection_time >= :date
                    """),
                    {"name": species[0], "date": three_months_ago}
                ).scalar()
                
                seasonal_score = 1 - (recent_count / species[1]) if species[1] > 0 else 1
                
                # Update or insert rarity scores
                session.execute(
                    text("""
                        INSERT OR REPLACE INTO rarity_scores 
                        (species_id, frequency_score, seasonal_score, last_seen, total_visits)
                        VALUES (:species, :freq, :seasonal, :last_seen, :visits)
                    """),
                    {
                        "species": species[0],
                        "freq": frequency_score,
                        "seasonal": seasonal_score,
                        "last_seen": species[2],
                        "visits": species[1]
                    }
                )
        
        db.execute_write(do_update)

    def evaluate_image_quality(self, detection_id: int, image_data: Dict = None) -> None:
        """Evaluate and store image quality metrics for a detection."""
        def do_evaluate(session):
            # Get image path
            result = session.execute(
                text("SELECT frigate_event FROM detections WHERE id = :id"),
                {"id": detection_id}
            ).fetchone()
            
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
            local_result = session.execute(
                text("""
                    SELECT clarity_score, composition_score, behavior_tags
                    FROM vision_analysis_cache
                    WHERE detection_id = :id
                """),
                {"id": detection_id}
            ).fetchone()
            
            if local_result:
                # Average with OpenAI scores if available, otherwise use local scores
                if image_data:
                    clarity_score = (clarity_score + local_result[0]) / 2
                    composition_score = (composition_score + local_result[1]) / 2
                else:
                    clarity_score = local_result[0]
                    composition_score = local_result[1]
                
                # Combine behavior tags
                if local_result[2]:
                    local_behaviors = json.loads(local_result[2])
                    behavior_tags.extend(local_behaviors)
            
            # Calculate visibility score as average of clarity and composition
            visibility_score = (clarity_score + composition_score) / 2
            
            # Remove duplicate behavior tags and convert to JSON
            behavior_tags = list(set(behavior_tags))
            behavior_tags_json = json.dumps(behavior_tags)
            
            # Update image_quality table
            session.execute(
                text("""
                    INSERT OR REPLACE INTO image_quality 
                    (detection_id, clarity_score, composition_score, behavior_tags, visibility_score)
                    VALUES (:id, :clarity, :composition, :behaviors, :visibility)
                """),
                {
                    "id": detection_id,
                    "clarity": clarity_score,
                    "composition": composition_score,
                    "behaviors": behavior_tags_json,
                    "visibility": visibility_score
                }
            )
            
            print(f"Updated quality scores for detection {detection_id}: clarity={clarity_score:.2f}, composition={composition_score:.2f}")
        
        db.execute_write(do_evaluate)

    def create_special_detection(self, detection_id: int) -> Optional[int]:
        """Evaluate a detection and create a special detection entry if it qualifies."""
        def do_create(session):
            # Get detection details including rarity and quality scores
            detection = session.execute(
                text("""
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
                    WHERE d.id = :id
                """),
                {"id": detection_id}
            ).fetchone()
            
            if not detection:
                print(f"No detection found for ID {detection_id}")
                return None

            # Add image quality if not present
            if not detection[7]:  # clarity_score index
                self.evaluate_image_quality(detection_id, {})

            # Determine highlight type based on frequency score
            frequency_score = detection[5] or 0  # frequency_score index
            highlight_type = 'rare' if frequency_score > 0.6 else 'quality'

            # Use raw frequency score for rare birds, detection score for quality birds
            final_score = frequency_score if highlight_type == 'rare' else detection[3]  # score index

            # Only create special detection if score is significant
            if final_score > 0.7:  # Threshold for special detection
                result = session.execute(
                    text("""
                        INSERT INTO special_detections 
                        (detection_id, highlight_type, score, created_at)
                        VALUES (:id, :type, :score, CURRENT_TIMESTAMP)
                        RETURNING id
                    """),
                    {"id": detection_id, "type": highlight_type, "score": final_score}
                )
                return result.fetchone()[0]
            
            return None
        
        return db.execute_write(do_create)

    def get_recent_special_detections(self, limit: int = 10) -> List[Dict]:
        """Get recent special detections with their details."""
        def do_query(session):
            rows = session.execute(
                text("""
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
                    LIMIT :limit
                """),
                {"limit": limit}
            ).fetchall()
            
            return [dict(zip(row.keys(), row)) for row in rows]
        
        return db.execute_read(do_query)

    def update_community_votes(self, special_detection_id: int, increment: bool = True) -> None:
        """Update the community vote count for a special detection."""
        def do_update(session):
            session.execute(
                text("""
                    UPDATE special_detections
                    SET community_votes = community_votes + :change
                    WHERE id = :id
                """),
                {"change": 1 if increment else -1, "id": special_detection_id}
            )
        
        db.execute_write(do_update)

    def toggle_featured_status(self, special_detection_id: int) -> bool:
        """Toggle the featured status of a special detection."""
        def do_toggle(session):
            result = session.execute(
                text("""
                    UPDATE special_detections
                    SET featured_status = NOT featured_status
                    WHERE id = :id
                    RETURNING featured_status
                """),
                {"id": special_detection_id}
            ).fetchone()
            return bool(result[0]) if result else False
        
        return db.execute_write(do_toggle)
