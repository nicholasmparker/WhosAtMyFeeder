import os
import json
import asyncio
from typing import Dict, List, Optional
import sqlite3
from datetime import datetime, timedelta
from openai import AsyncOpenAI

class VisionService:
    def __init__(self, db_path: str = "/data/speciesid.db"):
        """Initialize the Vision Service with OpenAI client and database connection."""
        self.db_path = db_path
        self.client = AsyncOpenAI()
        self._setup_database()

    def _get_db_connection(self) -> sqlite3.Connection:
        """Create a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _setup_database(self) -> None:
        """Ensure required tables exist."""
        conn = self._get_db_connection()
        try:
            # Create cache table for API responses
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vision_analysis_cache (
                    detection_id INTEGER PRIMARY KEY,
                    analysis_data TEXT,  -- JSON string of OpenAI response
                    clarity_score REAL,
                    composition_score REAL,
                    behavior_tags TEXT,  -- JSON array of behaviors
                    cost_tokens INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (detection_id) REFERENCES detections(id)
                )
            """)
            
            # Create cost tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vision_api_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    total_tokens INTEGER,
                    total_cost REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
        finally:
            conn.close()

    async def analyze_image(self, detection_id: int, image_path: str) -> Optional[Dict]:
        """
        Analyze an image using OpenAI's Vision API with caching.
        
        Args:
            detection_id: The ID of the detection
            image_path: Path to the image file
            
        Returns:
            Dict containing analysis results or None if analysis fails
        """
        # Check cache first
        cached = self._get_cached_analysis(detection_id)
        if cached:
            return cached

        try:
            # Prepare the image
            with open(image_path, 'rb') as image_file:
                # TODO: Convert image to base64 if needed
                image_data = image_file.read()

            # Analyze with OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this bird photo and provide scores from 0-1 for:
                                1. Image Quality:
                                   - Clarity (focus, resolution)
                                   - Composition (framing, background)
                                2. Bird Behavior:
                                   - What is the bird doing?
                                   - Is this behavior interesting or rare?
                                3. Special Characteristics:
                                   - Multiple birds?
                                   - Unusual pose?
                                   - Interesting interaction?
                                
                                Format response as JSON with these keys:
                                {
                                    "clarity_score": float,
                                    "composition_score": float,
                                    "behaviors": [string],
                                    "special_notes": string
                                }"""
                            },
                            {
                                "type": "image_url",
                                "url": f"file://{image_path}"
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            # Parse response
            analysis = json.loads(response.choices[0].message.content)
            
            # Cache results
            self._cache_analysis(
                detection_id=detection_id,
                analysis_data=response.choices[0].message.content,
                clarity_score=analysis['clarity_score'],
                composition_score=analysis['composition_score'],
                behavior_tags=json.dumps(analysis['behaviors']),
                cost_tokens=response.usage.total_tokens
            )

            return analysis

        except Exception as e:
            print(f"Error analyzing image: {e}")
            return None

    def _get_cached_analysis(self, detection_id: int) -> Optional[Dict]:
        """Get cached analysis results if they exist."""
        conn = self._get_db_connection()
        try:
            cursor = conn.execute("""
                SELECT analysis_data
                FROM vision_analysis_cache
                WHERE detection_id = ?
            """, (detection_id,))
            result = cursor.fetchone()
            if result:
                return json.loads(result['analysis_data'])
            return None
        finally:
            conn.close()

    def _cache_analysis(
        self,
        detection_id: int,
        analysis_data: str,
        clarity_score: float,
        composition_score: float,
        behavior_tags: str,
        cost_tokens: int
    ) -> None:
        """Cache analysis results and update cost tracking."""
        conn = self._get_db_connection()
        try:
            # Cache analysis
            conn.execute("""
                INSERT INTO vision_analysis_cache
                (detection_id, analysis_data, clarity_score, composition_score, behavior_tags, cost_tokens)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                detection_id,
                analysis_data,
                clarity_score,
                composition_score,
                behavior_tags,
                cost_tokens
            ))

            # Update cost tracking
            today = datetime.now().date()
            cost = (cost_tokens / 1000) * 0.01  # $0.01 per 1K tokens
            
            conn.execute("""
                INSERT INTO vision_api_costs (date, total_tokens, total_cost)
                VALUES (?, ?, ?)
                ON CONFLICT (date) DO UPDATE SET
                    total_tokens = total_tokens + excluded.total_tokens,
                    total_cost = total_cost + excluded.total_cost
            """, (today, cost_tokens, cost))
            
            conn.commit()
        finally:
            conn.close()

    async def batch_process_images(
        self,
        detection_ids: List[int],
        batch_size: int = 10,
        cost_limit: float = 5.0
    ) -> Dict[str, int]:
        """
        Process multiple images in batches with cost control.
        
        Args:
            detection_ids: List of detection IDs to process
            batch_size: Number of images to process in parallel
            cost_limit: Maximum cost in USD for this batch
            
        Returns:
            Dict with success and failure counts
        """
        # Check today's costs
        conn = self._get_db_connection()
        try:
            cursor = conn.execute("""
                SELECT COALESCE(SUM(total_cost), 0) as daily_cost
                FROM vision_api_costs
                WHERE date = DATE('now')
            """)
            daily_cost = cursor.fetchone()['daily_cost']
            
            if daily_cost >= cost_limit:
                print(f"Daily cost limit reached: ${daily_cost:.2f}")
                return {"processed": 0, "skipped": len(detection_ids)}
        finally:
            conn.close()

        results = {"processed": 0, "skipped": 0}
        
        # Process in batches
        for i in range(0, len(detection_ids), batch_size):
            batch = detection_ids[i:i + batch_size]
            
            # Get image paths for batch
            conn = self._get_db_connection()
            try:
                cursor = conn.execute("""
                    SELECT id, frigate_event
                    FROM detections
                    WHERE id IN ({})
                """.format(','.join('?' * len(batch))), batch)
                images = cursor.fetchall()
            finally:
                conn.close()

            # Process batch in parallel
            tasks = []
            for img in images:
                image_path = f"/path/to/frigate/events/{img['frigate_event']}/snapshot.jpg"
                if os.path.exists(image_path):
                    tasks.append(self.analyze_image(img['id'], image_path))
                else:
                    results["skipped"] += 1

            if tasks:
                batch_results = await asyncio.gather(*tasks)
                results["processed"] += sum(1 for r in batch_results if r is not None)
                results["skipped"] += sum(1 for r in batch_results if r is None)

            # Check cost after each batch
            conn = self._get_db_connection()
            try:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(total_cost), 0) as daily_cost
                    FROM vision_api_costs
                    WHERE date = DATE('now')
                """)
                daily_cost = cursor.fetchone()['daily_cost']
                
                if daily_cost >= cost_limit:
                    print(f"Cost limit reached after processing {results['processed']} images")
                    results["skipped"] += len(detection_ids) - (i + batch_size)
                    break
            finally:
                conn.close()

        return results

    def get_daily_costs(self, days: int = 30) -> List[Dict]:
        """Get cost tracking data for the last N days."""
        conn = self._get_db_connection()
        try:
            cursor = conn.execute("""
                SELECT 
                    date,
                    total_tokens,
                    total_cost
                FROM vision_api_costs
                WHERE date >= DATE('now', ?)
                ORDER BY date DESC
            """, (f'-{days} days',))
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
