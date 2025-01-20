from pathlib import Path
from sqlalchemy import text
from services.shared.database import db

print("Setting up database...")
BIRDS = [
    # Original entries from init_db.sql
    ('Cardinalis cardinalis', 'Northern Cardinal'),
    ('Cyanocitta cristata', 'Blue Jay'),
    ('Poecile atricapillus', 'Black-capped Chickadee'),
    ('Sitta carolinensis', 'White-breasted Nuthatch'),
    ('Haemorhous mexicanus', 'House Finch'),
    ('Melospiza melodia', 'Song Sparrow'),
    ('Spinus tristis', 'American Goldfinch'),
    ('Zenaida macroura', 'Mourning Dove'),
    ('Junco hyemalis', 'Dark-eyed Junco'),
    ('Baeolophus bicolor', 'Tufted Titmouse'),
    ('Melanerpes carolinus', 'Red-bellied Woodpecker'),
    ('Dryobates pubescens', 'Downy Woodpecker'),
    ('Pipilo erythrophthalmus', 'Eastern Towhee'),
    ('Thryothorus ludovicianus', 'Carolina Wren'),
    
    # Additional common backyard birds
    ('Corvus brachyrhynchos', 'American Crow'),
    ('Sturnus vulgaris', 'European Starling'),
    ('Passer domesticus', 'House Sparrow'),
    ('Turdus migratorius', 'American Robin'),
    ('Bombycilla cedrorum', 'Cedar Waxwing'),
    ('Picoides villosus', 'Hairy Woodpecker'),
    ('Colaptes auratus', 'Northern Flicker'),
    ('Mimus polyglottos', 'Northern Mockingbird'),
    ('Dumetella carolinensis', 'Gray Catbird'),
    ('Molothrus ater', 'Brown-headed Cowbird'),
    ('Quiscalus quiscula', 'Common Grackle'),
    ('Agelaius phoeniceus', 'Red-winged Blackbird'),
    ('Poecile carolinensis', 'Carolina Chickadee'),
    ('Setophaga coronata', 'Yellow-rumped Warbler'),
    ('Setophaga petechia', 'Yellow Warbler'),
    ('Setophaga palmarum', 'Palm Warbler'),
    ('Geothlypis trichas', 'Common Yellowthroat'),
    ('Piranga olivacea', 'Scarlet Tanager'),
    ('Cardinalis cardinalis', 'Northern Cardinal'),
    ('Passerina cyanea', 'Indigo Bunting'),
    ('Passerina ciris', 'Painted Bunting'),
    ('Spizella passerina', 'Chipping Sparrow'),
    ('Spizella pusilla', 'Field Sparrow'),
    ('Zonotrichia albicollis', 'White-throated Sparrow'),
    ('Zonotrichia leucophrys', 'White-crowned Sparrow'),
    ('Melospiza georgiana', 'Swamp Sparrow'),
    ('Pipilo maculatus', 'Spotted Towhee'),
    ('Carduelis tristis', 'American Goldfinch'),
    ('Haemorhous purpureus', 'Purple Finch'),
    ('Carpodacus mexicanus', 'House Finch'),
    ('Sialia mexicana', 'Western Bluebird'),
]

def setup_database():
    """Create and populate the birdnames table using SQLAlchemy."""
    
    def do_setup(session):
        # Create table if it doesn't exist
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS birdnames (
                scientific_name TEXT PRIMARY KEY,
                common_name TEXT NOT NULL
            )
        """))
        
        # Insert bird data
        print("Populating birdnames table...")
        for scientific_name, common_name in BIRDS:
            session.execute(
                text("INSERT OR REPLACE INTO birdnames (scientific_name, common_name) VALUES (:scientific, :common)"),
                {"scientific": scientific_name, "common": common_name}
            )
        
        # Verify the data
        count = session.execute(text("SELECT COUNT(*) FROM birdnames")).scalar()
        print(f"Added {count} bird species to database")
        
        # Show some sample entries
        print("\nSample entries:")
        rows = session.execute(text("SELECT * FROM birdnames LIMIT 5")).fetchall()
        for row in rows:
            print(f"  {row[1]} ({row[0]})")

if __name__ == "__main__":
    try:
        # Execute setup within a transaction
        db.execute_write(do_setup)
        print("\nDatabase setup complete!")
    except Exception as e:
        print(f"Error during database setup: {str(e)}")
