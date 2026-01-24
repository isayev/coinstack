"""One-time migration script to add missing columns to coin_images table."""
import sqlite3

conn = sqlite3.connect('./data/coinstack.db')
cursor = conn.cursor()

# Check current schema
cursor.execute("PRAGMA table_info(coin_images)")
columns = [col[1] for col in cursor.fetchall()]
print('Current columns:', columns)

# Add missing columns if they don't exist
if 'perceptual_hash' not in columns:
    cursor.execute('ALTER TABLE coin_images ADD COLUMN perceptual_hash VARCHAR(64)')
    print('Added perceptual_hash column')

if 'source_url' not in columns:
    cursor.execute('ALTER TABLE coin_images ADD COLUMN source_url VARCHAR(500)')
    print('Added source_url column')

if 'source_auction_id' not in columns:
    cursor.execute('ALTER TABLE coin_images ADD COLUMN source_auction_id INTEGER')
    print('Added source_auction_id column')

if 'source_house' not in columns:
    cursor.execute('ALTER TABLE coin_images ADD COLUMN source_house VARCHAR(50)')
    print('Added source_house column')

if 'downloaded_at' not in columns:
    cursor.execute('ALTER TABLE coin_images ADD COLUMN downloaded_at DATETIME')
    print('Added downloaded_at column')

conn.commit()

# Verify
cursor.execute("PRAGMA table_info(coin_images)")
columns = [col[1] for col in cursor.fetchall()]
print('Updated columns:', columns)

conn.close()
print('Migration complete!')
