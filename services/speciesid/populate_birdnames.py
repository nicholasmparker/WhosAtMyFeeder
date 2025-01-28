import sqlite3

DBPATH = '/data/speciesid.db'

print("Setting up database...")

def clear_database():
    """Clear existing entries from the birdnames table"""
    conn = sqlite3.connect(DBPATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS birdnames")
    conn.commit()
    conn.close()
    print("Cleared existing birdnames table")

# Birds commonly found in Austin, Texas area
BIRDS = [
    # Year-round residents
    ('Cardinalis cardinalis', 'Northern Cardinal'),
    ('Cyanocitta cristata', 'Blue Jay'),
    ('Poecile carolinensis', 'Carolina Chickadee'),  # Not Black-capped in Texas
    ('Sitta carolinensis', 'White-breasted Nuthatch'),
    ('Haemorhous mexicanus', 'House Finch'),
    ('Spinus tristis', 'American Goldfinch'),
    ('Zenaida macroura', 'Mourning Dove'),
    ('Baeolophus atricristatus', 'Black-crested Titmouse'),  # Texas subspecies
    ('Melanerpes carolinus', 'Red-bellied Woodpecker'),
    ('Dryobates pubescens', 'Downy Woodpecker'),
    ('Thryothorus ludovicianus', 'Carolina Wren'),
    ('Mimus polyglottos', 'Northern Mockingbird'),
    ('Toxostoma rufum', 'Brown Thrasher'),
    ('Melozone fusca', 'Canyon Towhee'),
    
    # Common Texas species
    ('Corvus brachyrhynchos', 'American Crow'),
    ('Sturnus vulgaris', 'European Starling'),
    ('Passer domesticus', 'House Sparrow'),
    ('Molothrus ater', 'Brown-headed Cowbird'),
    ('Quiscalus mexicanus', 'Great-tailed Grackle'),
    ('Agelaius phoeniceus', 'Red-winged Blackbird'),
    ('Columbina inca', 'Inca Dove'),
    ('Streptopelia decaocto', 'Eurasian Collared-Dove'),
    ('Charadrius vociferus', 'Killdeer'),
    ('Setophaga coronata', 'Yellow-rumped Warbler'),
    ('Vireo griseus', 'White-eyed Vireo'),
    ('Passerina ciris', 'Painted Bunting'),
    ('Spizella passerina', 'Chipping Sparrow'),
    ('Zonotrichia leucophrys', 'White-crowned Sparrow'),
    ('Amphispiza bilineata', 'Black-throated Sparrow'),
    ('Chondestes grammacus', 'Lark Sparrow'),
    ('Icterus bullockii', 'Bullock\'s Oriole'),
    ('Tyrannus forficatus', 'Scissor-tailed Flycatcher'),
    ('Sayornis phoebe', 'Eastern Phoebe'),
    ('Buteo jamaicensis', 'Red-tailed Hawk')
]

def setup_database():
    """Create and populate the birdnames table."""
    conn = sqlite3.connect(DBPATH)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birdnames (
            scientific_name TEXT PRIMARY KEY,
            common_name TEXT NOT NULL
        )
    """)
    
    # Insert bird data
    print("Populating birdnames table...")
    for scientific_name, common_name in BIRDS:
        cursor.execute(
            "INSERT OR REPLACE INTO birdnames (scientific_name, common_name) VALUES (?, ?)",
            (scientific_name, common_name)
        )
    
    # Verify the data
    cursor.execute("SELECT COUNT(*) FROM birdnames")
    count = cursor.fetchone()[0]
    print(f"Added {count} bird species to database")
    
    # Show some sample entries
    print("\nSample entries:")
    cursor.execute("SELECT * FROM birdnames LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row[1]} ({row[0]})")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    try:
        clear_database()
        setup_database()
        print("\nDatabase setup complete!")
    except Exception as e:
        print(f"Error during database setup: {str(e)}")
