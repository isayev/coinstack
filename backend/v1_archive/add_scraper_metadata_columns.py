"""
Migration script to add new scraper metadata columns to auction_data table.

Run this once to add columns for:
- NGC/PCGS slab details (strike_score, surface_score, etc.)
- eBay seller info
- Biddr sub-house
- Legends and historical notes

Safe to run multiple times - checks if columns exist first.
"""
import sqlite3
import os
from app.config import get_settings

settings = get_settings()

# Extract database path from URL
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    db_path = db_url.replace("sqlite:///", "")
else:
    print(f"Unsupported database URL: {db_url}")
    exit(1)

print(f"Database path: {db_path}")

if not os.path.exists(db_path):
    print(f"Database file not found: {db_path}")
    print("Tables will be created when the app starts.")
    exit(0)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check existing columns
cursor.execute("PRAGMA table_info(auction_data)")
existing_columns = {row[1] for row in cursor.fetchall()}
print(f"Existing columns: {len(existing_columns)}")

# New columns to add
new_columns = [
    # NGC/PCGS slab details
    ("strike_score", "VARCHAR(10)", None),
    ("surface_score", "VARCHAR(10)", None),
    ("numeric_grade", "INTEGER", None),
    ("grade_designation", "VARCHAR(50)", None),
    
    # Physical
    ("thickness_mm", "DECIMAL(4,2)", None),
    
    # Biddr sub-house
    ("sub_house", "VARCHAR(50)", None),
    
    # eBay seller info
    ("seller_username", "VARCHAR(100)", None),
    ("seller_feedback_score", "INTEGER", None),
    ("seller_feedback_pct", "DECIMAL(5,2)", None),
    ("seller_is_top_rated", "BOOLEAN", None),
    ("seller_location", "VARCHAR(100)", None),
    
    # Listing type (eBay)
    ("listing_type", "VARCHAR(50)", None),
    ("shipping_cost", "DECIMAL(10,2)", None),
    ("watchers", "INTEGER", None),
    
    # Legends
    ("obverse_legend", "VARCHAR(500)", None),
    ("reverse_legend", "VARCHAR(500)", None),
    ("exergue", "VARCHAR(200)", None),
    
    # Historical notes
    ("historical_notes", "TEXT", None),
]

added = 0
for col_name, col_type, default in new_columns:
    if col_name not in existing_columns:
        print(f"Adding column: {col_name} ({col_type})")
        try:
            sql = f"ALTER TABLE auction_data ADD COLUMN {col_name} {col_type}"
            if default is not None:
                sql += f" DEFAULT {default}"
            cursor.execute(sql)
            added += 1
        except sqlite3.OperationalError as e:
            print(f"  Error: {e}")
    else:
        print(f"  Column {col_name} already exists")

conn.commit()
conn.close()

print(f"\nMigration complete! Added {added} new columns.")
