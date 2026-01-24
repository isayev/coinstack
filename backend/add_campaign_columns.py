"""
Migration script to add campaign tracking columns to auction_data table.

Run this once to add the new columns:
    python add_campaign_columns.py

This is safe to run multiple times - it checks if columns exist first.
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
    print("The columns will be created when the app starts and creates tables.")
    exit(0)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check existing columns
cursor.execute("PRAGMA table_info(auction_data)")
existing_columns = {row[1] for row in cursor.fetchall()}
print(f"Existing columns in auction_data: {len(existing_columns)}")

# Columns to add
new_columns = [
    ("campaign_scraped_at", "DATETIME", None),
    ("campaign_successful", "BOOLEAN", None),
    ("campaign_error", "VARCHAR(500)", None),
]

added = 0
for col_name, col_type, default in new_columns:
    if col_name in existing_columns:
        print(f"  Column '{col_name}' already exists, skipping")
    else:
        sql = f"ALTER TABLE auction_data ADD COLUMN {col_name} {col_type}"
        if default is not None:
            sql += f" DEFAULT {default}"
        
        print(f"  Adding column: {col_name} ({col_type})")
        cursor.execute(sql)
        added += 1

conn.commit()
conn.close()

print(f"\nMigration complete. Added {added} new column(s).")
