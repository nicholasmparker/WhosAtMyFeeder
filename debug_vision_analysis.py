import asyncio
import os
from vision_service import VisionService
import sqlite3
from datetime import datetime, timedelta

async def test_vision_analysis():
    """Test the OpenAI Vision integration with sample images."""
    vision_service = VisionService()
    
    # Get some recent detections to analyze
    conn = sqlite3.connect('/data/speciesid.db')
    cursor = conn.cursor()
    
    try:
        # Get high confidence detections from the last day
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            SELECT id, frigate_event, display_name, score
            FROM detections
            WHERE detection_time >= ?
            AND score >= 0.8
            LIMIT 5
        """, (yesterday,))
        
        detections = cursor.fetchall()
        
        print(f"\nTesting Vision Analysis with {len(detections)} recent detections")
        print("=" * 80)
        
        for detection_id, frigate_event, species, score in detections:
            print(f"\nAnalyzing detection {detection_id}:")
            print(f"Species: {species}")
            print(f"Original confidence: {score:.2f}")
            
            # Get image path
            image_path = f"/path/to/frigate/events/{frigate_event}/snapshot.jpg"
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                continue
            
            # Analyze with OpenAI Vision
            print("\nRequesting OpenAI Vision analysis...")
            analysis = await vision_service.analyze_image(detection_id, image_path)
            
            if analysis:
                print("\nAnalysis Results:")
                print(f"Clarity Score: {analysis['clarity_score']:.2f}")
                print(f"Composition Score: {analysis['composition_score']:.2f}")
                print("\nDetected Behaviors:")
                for behavior in analysis['behaviors']:
                    print(f"- {behavior}")
                print(f"\nSpecial Notes: {analysis['special_notes']}")
            else:
                print("Analysis failed")
            
            print("-" * 80)
        
        # Check cost tracking
        print("\nCost Analysis:")
        print("=" * 80)
        costs = vision_service.get_daily_costs(days=7)
        for cost in costs:
            print(f"Date: {cost['date']}")
            print(f"Tokens Used: {cost['total_tokens']}")
            print(f"Cost: ${cost['total_cost']:.2f}")
            print("-" * 40)
        
    finally:
        conn.close()

async def test_batch_processing():
    """Test batch processing with cost limits."""
    vision_service = VisionService()
    
    # Get a batch of detections
    conn = sqlite3.connect('/data/speciesid.db')
    cursor = conn.cursor()
    
    try:
        # Get detection IDs for testing
        cursor.execute("""
            SELECT id 
            FROM detections 
            WHERE score >= 0.8
            AND id NOT IN (SELECT detection_id FROM vision_analysis_cache)
            LIMIT 20
        """)
        
        detection_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"\nTesting Batch Processing with {len(detection_ids)} detections")
        print("=" * 80)
        
        # Process with a low cost limit to test limiting
        results = await vision_service.batch_process_images(
            detection_ids=detection_ids,
            batch_size=5,
            cost_limit=1.00  # $1.00 limit
        )
        
        print("\nBatch Processing Results:")
        print(f"Successfully processed: {results['processed']}")
        print(f"Skipped: {results['skipped']}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("OpenAI Vision Integration Test")
    print("=" * 80)
    
    # Run tests
    asyncio.run(test_vision_analysis())
    print("\nTesting batch processing...")
    asyncio.run(test_batch_processing())
