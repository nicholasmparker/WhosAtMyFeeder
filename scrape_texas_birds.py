import sqlite3
from pathlib import Path
import re

# Use absolute path to match Docker configuration
DBPATH = '/data/speciesid.db'

def parse_bird_entry(line: str) -> tuple:
    """Parse a bird entry line into scientific and common names."""
    # Remove footnote references [1], [2], etc. and annotations like (R), (I), etc.
    line = re.sub(r'\[\d+\]|\([A-Z,\s]+\)', '', line)
    
    # Split on comma and clean up whitespace
    parts = [part.strip() for part in line.split(',', 1)]
    if len(parts) != 2:
        return None
        
    common_name, scientific_info = parts
    
    # Extract scientific name from the second part (usually in italics in the wiki)
    scientific_match = re.search(r'([A-Z][a-z]+\s+[a-z]+)', scientific_info)
    if not scientific_match:
        return None
        
    scientific_name = scientific_match.group(1)
    return (scientific_name, common_name)

def get_texas_birds():
    """Get list of Texas birds from provided data."""
    birds = []
    
    # Full Texas birds data
    data = """
    Northern cardinal, Cardinalis cardinalis
    Blue jay, Cyanocitta cristata
    Black-capped chickadee, Poecile atricapillus
    White-breasted nuthatch, Sitta carolinensis
    House finch, Haemorhous mexicanus
    Song sparrow, Melospiza melodia
    American goldfinch, Spinus tristis
    Mourning dove, Zenaida macroura
    Dark-eyed junco, Junco hyemalis
    Tufted titmouse, Baeolophus bicolor
    Red-bellied woodpecker, Melanerpes carolinus
    Downy woodpecker, Dryobates pubescens
    Eastern towhee, Pipilo erythrophthalmus
    Carolina wren, Thryothorus ludovicianus
    American crow, Corvus brachyrhynchos
    European starling, Sturnus vulgaris
    House sparrow, Passer domesticus
    American robin, Turdus migratorius
    Cedar waxwing, Bombycilla cedrorum
    Hairy woodpecker, Picoides villosus
    Northern flicker, Colaptes auratus
    Northern mockingbird, Mimus polyglottos
    Gray catbird, Dumetella carolinensis
    Brown-headed cowbird, Molothrus ater
    Common grackle, Quiscalus quiscula
    Red-winged blackbird, Agelaius phoeniceus
    Carolina chickadee, Poecile carolinensis
    Yellow-rumped warbler, Setophaga coronata
    Yellow warbler, Setophaga petechia
    Palm warbler, Setophaga palmarum
    Common yellowthroat, Geothlypis trichas
    Scarlet tanager, Piranga olivacea
    Northern cardinal, Cardinalis cardinalis
    Indigo bunting, Passerina cyanea
    Painted bunting, Passerina ciris
    Chipping sparrow, Spizella passerina
    Field sparrow, Spizella pusilla
    White-throated sparrow, Zonotrichia albicollis
    White-crowned sparrow, Zonotrichia leucophrys
    Swamp sparrow, Melospiza georgiana
    Spotted towhee, Pipilo maculatus
    American goldfinch, Carduelis tristis
    Purple finch, Haemorhous purpureus
    House finch, Carpodacus mexicanus
    Great blue heron, Ardea herodias
    Great egret, Ardea alba
    Snowy egret, Egretta thula
    Green heron, Butorides virescens
    Black-crowned night-heron, Nycticorax nycticorax
    Turkey vulture, Cathartes aura
    Red-tailed hawk, Buteo jamaicensis
    Red-shouldered hawk, Buteo lineatus
    Cooper's hawk, Accipiter cooperii
    Barred owl, Strix varia
    Great horned owl, Bubo virginianus
    Belted kingfisher, Megaceryle alcyon
    Ruby-throated hummingbird, Archilochus colubris
    Black-chinned hummingbird, Archilochus alexandri
    Eastern phoebe, Sayornis phoebe
    Great crested flycatcher, Myiarchus crinitus
    Eastern wood-pewee, Contopus virens
    White-eyed vireo, Vireo griseus
    Red-eyed vireo, Vireo olivaceus
    """
    
    # Process each line
    for line in data.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        result = parse_bird_entry(line)
        if result:
            birds.append(result)
            print(f"Found bird: {result[1]} ({result[0]})")
    
    return birds

def update_database(birds, db_path):
    """Update the database with bird data."""
    print(f"\nUpdating database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing table if it exists
    cursor.execute("DROP TABLE IF EXISTS birdnames")
    
    # Create table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS birdnames (
        scientific_name TEXT PRIMARY KEY,
        common_name TEXT NOT NULL
    )
    """)
    
    # Insert bird data
    print("Inserting bird data...")
    cursor.executemany(
        "INSERT OR REPLACE INTO birdnames (scientific_name, common_name) VALUES (?, ?)",
        birds
    )
    
    conn.commit()
    
    # Verify the data
    cursor.execute("SELECT COUNT(*) FROM birdnames")
    count = cursor.fetchone()[0]
    print(f"Database now contains {count} bird species")
    
    # Show some sample entries
    print("\nSample entries:")
    cursor.execute("SELECT * FROM birdnames LIMIT 5")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[0]})")
    
    conn.close()
    print("\nDatabase update complete!")

def main():
    print("Starting Texas birds database update")
    birds = get_texas_birds()
    
    if birds:
        db_path = DBPATH  # Use the same path as other modules
        update_database(birds, db_path)
        print(f"\nTo use this database, ensure your application is configured to use: {Path(db_path).absolute()}")
        print("\nNote: This is an initial set of common Texas birds. More species will be added in subsequent updates.")
    else:
        print("No bird data was found.")

if __name__ == "__main__":
    main()
