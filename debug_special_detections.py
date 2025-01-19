from special_detection_service import SpecialDetectionService
import sqlite3

def get_detection_details(db_path: str, detection_id: int):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("""
        SELECT 
            d.*,
            r.frequency_score,
            r.seasonal_score
        FROM detections d
        LEFT JOIN rarity_scores r ON d.display_name = r.species_id
        WHERE d.id = ?
    """, (detection_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def main():
    db_path = '/data/speciesid.db'
    with open('/data/debug.log', 'w') as f:
        f.write('Starting special detection creation\n')
        
        service = SpecialDetectionService(db_path)
        service.update_rarity_scores()
        
        f.write('\nRarity scores updated\n')
        
        for detection_id in range(1, 15):
            f.write(f'\nProcessing detection {detection_id}\n')
            details = get_detection_details(db_path, detection_id)
            if details:
                f.write(f'Species: {details["display_name"]}\n')
                f.write(f'Detection score: {details["score"]}\n')
                f.write(f'Frequency score: {details["frequency_score"]}\n')
                f.write(f'Seasonal score: {details["seasonal_score"]}\n')
                
                # Calculate final scores like in create_special_detection
                rarity_score = (details['frequency_score'] or 0) * 0.9
                quality_score = details['score']
                highlight_type = 'rare' if details['frequency_score'] > 0.6 else 'quality'
                final_score = rarity_score if highlight_type == 'rare' else quality_score
                
                f.write(f'Combined rarity score: {rarity_score}\n')
                f.write(f'Quality score: {quality_score}\n')
                f.write(f'Highlight type: {highlight_type}\n')
                f.write(f'Final score: {final_score}\n')
                f.write(f'Meets threshold (>0.7): {final_score > 0.7}\n')
            else:
                f.write('No detection found\n')
            
            result = service.create_special_detection(detection_id)
            f.write(f'Result: {result}\n')

if __name__ == '__main__':
    main()
