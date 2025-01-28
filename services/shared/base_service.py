from typing import Any, Dict, List, Optional, TypeVar, Generic
import sqlite3
from datetime import datetime
import json

T = TypeVar('T')

class BaseService(Generic[T]):
    """
    Base service class implementing common database operations and response formatting.
    Follows the Repository Pattern for data access.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_db_connection(self) -> sqlite3.Connection:
        """Create a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def format_datetime(self, timestamp: float) -> str:
        """Convert Unix timestamp to ISO 8601 format."""
        return datetime.fromtimestamp(timestamp).isoformat()

    def format_detection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a detection record into a consistent dictionary structure.
        Used by both regular and special detections.
        """
        return {
            'id': data.get('id'),
            'detection_time': data.get('detection_time'),  # Already formatted by SQLite
            'display_name': data.get('display_name'),
            'score': data.get('score'),
            'frigate_event': data.get('frigate_event'),
            'common_name': data.get('common_name'),
            'visibility_score': data.get('visibility_score', 0),
            'clarity_score': data.get('clarity_score', 0),
            'composition_score': data.get('composition_score', 0),
            'enhancement_status': data.get('enhancement_status'),
            'quality_improvement': data.get('quality_improvement', 0),
            'enhanced_path': data.get('enhanced_path'),
            'enhanced_thumbnail_path': data.get('enhanced_thumbnail_path'),
            'is_special': bool(data.get('is_special', False)),
            'highlight_type': data.get('highlight_type'),
            'special_score': data.get('special_score'),
            'community_votes': data.get('community_votes', 0),
            'featured_status': data.get('featured_status', 0)
        }

    def format_response(self, data: Dict[str, Any], is_detection: bool = False) -> Dict[str, Any]:
        """
        Format API response following a consistent structure.
        
        Args:
            data: Data to format
            is_detection: Whether this is a detection record
        """
        if is_detection:
            return self.format_detection(data)
            
        formatted = {}
        for key, value in data.items():
            if isinstance(value, sqlite3.Row):
                value = dict(value)
            if isinstance(value, (dict, sqlite3.Row)):
                formatted[key] = self.format_response(dict(value))
            else:
                formatted[key] = value
        return formatted

    def execute_query(
        self, 
        query: str, 
        params: tuple = (), 
        single_row: bool = False,
        is_detection: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a database query and return formatted results.
        
        Args:
            query: SQL query string
            params: Query parameters
            single_row: Whether to return a single row or all results
            is_detection: Whether this query returns detection records
            
        Returns:
            Formatted query results
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if single_row:
                    row = cursor.fetchone()
                    return self.format_response(dict(row), is_detection) if row else None
                
                rows = cursor.fetchall()
                return [self.format_response(dict(row), is_detection) for row in rows]
                
        except sqlite3.Error as e:
            # Log the error and re-raise with a clear message
            print(f"Database error: {e}")
            raise Exception(f"Database operation failed: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    def execute_write_query(
        self, 
        query: str, 
        params: tuple = ()
    ) -> int:
        """
        Execute a write query (INSERT, UPDATE, DELETE) and return affected row count.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise Exception(f"Database write operation failed: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    def begin_transaction(self) -> sqlite3.Connection:
        """Start a database transaction."""
        conn = self.get_db_connection()
        conn.execute("BEGIN")
        return conn

    def commit_transaction(self, conn: sqlite3.Connection) -> None:
        """Commit a database transaction."""
        conn.commit()
        conn.close()

    def rollback_transaction(self, conn: sqlite3.Connection) -> None:
        """Rollback a database transaction."""
        conn.rollback()
        conn.close()
