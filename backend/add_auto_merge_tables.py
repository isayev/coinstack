"""
Migration script to add auto-merge tables and columns.

Run this once to add:
- field_history table
- field_sources column to coins table

Safe to run multiple times - checks if objects exist first.
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

# Check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
existing_tables = {row[0] for row in cursor.fetchall()}
print(f"Existing tables: {len(existing_tables)}")

# 1. Create field_history table if not exists
if "field_history" not in existing_tables:
    print("Creating field_history table...")
    cursor.execute("""
        CREATE TABLE field_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id INTEGER NOT NULL,
            field_name VARCHAR(50) NOT NULL,
            old_value JSON,
            new_value JSON,
            old_source VARCHAR(50),
            new_source VARCHAR(50),
            old_source_id VARCHAR(100),
            new_source_id VARCHAR(100),
            change_type VARCHAR(20) NOT NULL,
            changed_at DATETIME NOT NULL,
            changed_by VARCHAR(100),
            batch_id VARCHAR(36),
            conflict_type VARCHAR(50),
            trust_old INTEGER,
            trust_new INTEGER,
            reason VARCHAR(500),
            FOREIGN KEY (coin_id) REFERENCES coins(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX ix_field_history_coin_id ON field_history(coin_id)")
    cursor.execute("CREATE INDEX ix_field_history_batch_id ON field_history(batch_id)")
    cursor.execute("CREATE INDEX ix_field_history_batch_coin ON field_history(batch_id, coin_id)")
    cursor.execute("CREATE INDEX ix_field_history_coin_field ON field_history(coin_id, field_name)")
    
    print("  field_history table created with indexes")
else:
    print("  field_history table already exists")

# 2. Add field_sources column to coins table if not exists
cursor.execute("PRAGMA table_info(coins)")
coin_columns = {row[1] for row in cursor.fetchall()}

if "field_sources" not in coin_columns:
    print("Adding field_sources column to coins table...")
    cursor.execute("ALTER TABLE coins ADD COLUMN field_sources JSON DEFAULT '{}'")
    print("  field_sources column added")
else:
    print("  field_sources column already exists")

conn.commit()
conn.close()

print("\nMigration complete!")
