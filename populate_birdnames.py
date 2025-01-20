import sqlite3
import csv
from pathlib import Path

# Common North American birds with scientific names
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
]

def setup_database(db_path):
    """Create and populate the birdnames table."""
    print(f"Setting up database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birdnames (
        scientific_name TEXT PRIMARY KEY,
        common_name TEXT NOT NULL
    )
    """)

    # Insert bird data
    print("Populating birdnames table...")
    cursor.executemany(
        "INSERT OR REPLACE INTO birdnames (scientific_name, common_name) VALUES (?, ?)",
        BIRDS
    )

    conn.commit()
    
    # Verify the data
    cursor.execute("SELECT COUNT(*) FROM birdnames")
    count = cursor.fetchone()[0]
    print(f"Added {count} bird species to database")
    
    # Show some sample entries
    print("\nSample entries:")
    cursor.execute("SELECT * FROM birdnames LIMIT 5")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[0]})")
    
    conn.close()
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    db_path = "speciesid.db"  # Use the same path as in your application
    setup_database(db_path)
    print(f"\nTo use this database, ensure your application is configured to use: {Path(db_path).absolute()}")
