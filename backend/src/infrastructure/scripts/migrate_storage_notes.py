"""
Migration script to add storage_location and personal_notes columns to coins_v2
and migrate data from V1 coins table.

Usage:
    python -m src.infrastructure.scripts.migrate_storage_notes [--verify]
"""

import sqlite3
import argparse
from pathlib import Path


def get_db_path() -> Path:
    """Get the path to the database file."""
    return Path(__file__).parent.parent.parent.parent / "coinstack_v2.db"


def add_columns(cursor: sqlite3.Cursor) -> tuple[bool, bool]:
    """Add storage_location and personal_notes columns if they don't exist.
    
    Returns tuple of (storage_added, notes_added) booleans.
    """
    # Check existing columns
    cursor.execute("PRAGMA table_info(coins_v2)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    storage_added = False
    notes_added = False
    
    if "storage_location" not in existing_columns:
        print("Adding storage_location column to coins_v2...")
        cursor.execute("ALTER TABLE coins_v2 ADD COLUMN storage_location TEXT")
        storage_added = True
    else:
        print("Column storage_location already exists")
    
    if "personal_notes" not in existing_columns:
        print("Adding personal_notes column to coins_v2...")
        cursor.execute("ALTER TABLE coins_v2 ADD COLUMN personal_notes TEXT")
        notes_added = True
    else:
        print("Column personal_notes already exists")
    
    return storage_added, notes_added


def migrate_data(cursor: sqlite3.Cursor) -> dict:
    """Migrate storage_location and personal_notes from V1 coins to V2 coins_v2.
    
    Returns migration statistics.
    """
    stats = {
        "storage_migrated": 0,
        "notes_migrated": 0,
        "total_updated": 0
    }
    
    # Check if V1 coins table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coins'")
    if not cursor.fetchone():
        print("V1 coins table not found, skipping data migration")
        return stats
    
    # Get coins with storage_location data in V1
    cursor.execute("""
        SELECT id, storage_location, personal_notes 
        FROM coins 
        WHERE (storage_location IS NOT NULL AND storage_location != '')
           OR (personal_notes IS NOT NULL AND personal_notes != '')
    """)
    v1_data = cursor.fetchall()
    
    print(f"Found {len(v1_data)} coins with data to migrate")
    
    for coin_id, storage, notes in v1_data:
        # Check if coin exists in V2
        cursor.execute("SELECT id FROM coins_v2 WHERE id = ?", (coin_id,))
        if not cursor.fetchone():
            print(f"  Warning: Coin {coin_id} not found in coins_v2, skipping")
            continue
        
        # Update V2 record
        cursor.execute("""
            UPDATE coins_v2 
            SET storage_location = COALESCE(?, storage_location),
                personal_notes = COALESCE(?, personal_notes)
            WHERE id = ?
        """, (storage if storage else None, notes if notes else None, coin_id))
        
        if storage:
            stats["storage_migrated"] += 1
        if notes:
            stats["notes_migrated"] += 1
        stats["total_updated"] += 1
    
    return stats


def verify_migration(cursor: sqlite3.Cursor) -> None:
    """Verify the migration was successful."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    # Check columns exist
    cursor.execute("PRAGMA table_info(coins_v2)")
    columns = {row[1] for row in cursor.fetchall()}
    
    print(f"\nColumns present:")
    print(f"  storage_location: {'✓' if 'storage_location' in columns else '❌'}")
    print(f"  personal_notes: {'✓' if 'personal_notes' in columns else '❌'}")
    
    # Count records with data
    cursor.execute("SELECT COUNT(*) FROM coins_v2 WHERE storage_location IS NOT NULL AND storage_location != ''")
    storage_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM coins_v2 WHERE personal_notes IS NOT NULL AND personal_notes != ''")
    notes_count = cursor.fetchone()[0]
    
    print(f"\nData in coins_v2:")
    print(f"  Records with storage_location: {storage_count}")
    print(f"  Records with personal_notes: {notes_count}")
    
    # Compare with V1
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coins'")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM coins WHERE storage_location IS NOT NULL AND storage_location != ''")
        v1_storage = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM coins WHERE personal_notes IS NOT NULL AND personal_notes != ''")
        v1_notes = cursor.fetchone()[0]
        
        print(f"\nComparison with V1 coins table:")
        print(f"  V1 storage_location: {v1_storage} -> V2: {storage_count} {'✓' if storage_count >= v1_storage else '⚠️'}")
        print(f"  V1 personal_notes: {v1_notes} -> V2: {notes_count} {'✓' if notes_count >= v1_notes else '⚠️'}")
    
    # Sample data
    print("\nSample migrated records:")
    cursor.execute("""
        SELECT id, issuer, storage_location, 
               SUBSTR(personal_notes, 1, 50) as notes_preview
        FROM coins_v2 
        WHERE storage_location IS NOT NULL OR personal_notes IS NOT NULL
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  Coin {row[0]} ({row[1]}): loc='{row[2]}', notes='{row[3]}...'")


def main():
    parser = argparse.ArgumentParser(description="Migrate storage_location and personal_notes to V2")
    parser.add_argument("--verify", action="store_true", help="Only verify, don't migrate")
    args = parser.parse_args()
    
    db_path = get_db_path()
    print(f"Database: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        if args.verify:
            verify_migration(cursor)
        else:
            print("\n" + "=" * 60)
            print("MIGRATION: storage_location and personal_notes")
            print("=" * 60)
            
            # Step 1: Add columns
            storage_added, notes_added = add_columns(cursor)
            
            # Step 2: Migrate data
            stats = migrate_data(cursor)
            
            # Commit changes
            conn.commit()
            
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETE")
            print("=" * 60)
            print(f"  Columns added: storage_location={storage_added}, personal_notes={notes_added}")
            print(f"  Storage locations migrated: {stats['storage_migrated']}")
            print(f"  Personal notes migrated: {stats['notes_migrated']}")
            print(f"  Total records updated: {stats['total_updated']}")
            
            # Verify
            verify_migration(cursor)
            
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return 1
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
