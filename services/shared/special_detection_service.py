from typing import List, Dict, Any, Optional
from .base_service import BaseService

class SpecialDetectionService(BaseService):
    """Service for handling special bird detections with standardized responses."""

    def _base_special_detection_query(self) -> str:
        """Base query for getting special detection data with consistent field names."""
        return """
            SELECT 
                d.id,
                datetime(d.detection_time, 'localtime') as detection_time,
                d.display_name,
                d.score,
                d.frigate_event,
                b.common_name,
                COALESCE(iq.clarity_score, 0) as clarity_score,
                COALESCE(iq.composition_score, 0) as composition_score,
                iq.behavior_tags,
                COALESCE(iq.clarity_score * 0.6 + iq.composition_score * 0.4, 0) as visibility_score,
                d.enhancement_status,
                COALESCE(iq.quality_improvement, 0) as quality_improvement,
                iq.enhanced_path,
                iq.enhanced_thumbnail_path,
                1 as is_special,
                sd.highlight_type,
                sd.score as special_score,
                sd.community_votes,
                sd.featured_status
            FROM special_detections sd
            JOIN detections d ON sd.detection_id = d.id
            JOIN birdnames b ON d.display_name = b.scientific_name
            LEFT JOIN image_quality iq ON d.id = iq.detection_id
        """

    def get_recent_special_detections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent special detections with all related data.
        
        Args:
            limit: Maximum number of detections to return
            
        Returns:
            List of special detections with full metadata
        """
        query = f"""
            {self._base_special_detection_query()}
            ORDER BY sd.created_at DESC
            LIMIT ?
        """
        return self.execute_query(query, (limit,))

    def get_special_detections_by_type(self, highlight_type: str) -> List[Dict[str, Any]]:
        """
        Get special detections filtered by type.
        
        Args:
            highlight_type: Type of special detection (rare/quality/behavior)
            
        Returns:
            List of special detections of the specified type
        """
        if highlight_type not in ['rare', 'quality', 'behavior']:
            raise ValueError("Invalid highlight type")

        query = f"""
            {self._base_special_detection_query()}
            WHERE sd.highlight_type = ?
            ORDER BY sd.score DESC
            LIMIT 50
        """
        return self.execute_query(query, (highlight_type,))

    def update_community_votes(self, special_detection_id: int, increment: bool) -> None:
        """
        Update community votes for a special detection.
        
        Args:
            special_detection_id: ID of the special detection
            increment: True to increment, False to decrement
        """
        query = """
            UPDATE special_detections 
            SET community_votes = community_votes + ?
            WHERE id = ?
        """
        self.execute_write_query(query, (1 if increment else -1, special_detection_id))

    def toggle_featured_status(self, special_detection_id: int) -> bool:
        """
        Toggle featured status of a special detection.
        
        Args:
            special_detection_id: ID of the special detection
            
        Returns:
            New featured status
        """
        # Use a transaction to ensure atomicity
        conn = self.begin_transaction()
        try:
            cursor = conn.cursor()
            
            # Get current status
            cursor.execute(
                "SELECT featured_status FROM special_detections WHERE id = ?",
                (special_detection_id,)
            )
            current = cursor.fetchone()
            if not current:
                raise ValueError("Special detection not found")

            # Toggle status
            new_status = 0 if current['featured_status'] else 1
            cursor.execute(
                "UPDATE special_detections SET featured_status = ? WHERE id = ?",
                (new_status, special_detection_id)
            )
            
            self.commit_transaction(conn)
            return bool(new_status)
            
        except Exception as e:
            self.rollback_transaction(conn)
            raise Exception(f"Failed to toggle featured status: {str(e)}")
