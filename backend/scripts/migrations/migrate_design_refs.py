"""
Design, References & Provenance Migration Script

This script adds schema support for:
- Coin design fields (obverse/reverse legends, descriptions, exergue)
- Denomination and portrait_subject fields
- Catalog references table (RIC, Crawford, Sear, etc.)
- Provenance events table (ownership history)

Run from backend directory: python -m scripts.migrations.migrate_design_refs
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


def get_db_path() -> Path:
    """Get path to the database file."""
    possible_paths = [
        Path("coinstack_v2.db"),
        Path("backend/coinstack_v2.db"),
        Path(__file__).parent.parent.parent / "coinstack_v2.db",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    raise FileNotFoundError("Could not find coinstack_v2.db")


def backup_database(db_path: Path) -> Path:
    """Create a timestamped backup of the database."""
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"coinstack_{timestamp}.db"
    
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    # Clean old backups (keep 5 most recent)
    backups = sorted(backup_dir.glob("coinstack_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_backup in backups[5:]:
        old_backup.unlink()
        print(f"Removed old backup: {old_backup}")
    
    return backup_path


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Check if a table exists."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None


def run_migration(db_path: Path):
    """Run the design/references/provenance migration."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        # =====================================================================
        # 1. Add new columns to coins_v2 table
        # =====================================================================
        print("Adding new columns to coins_v2...")
        
        new_columns = [
            # Denomination and portrait subject
            ("denomination", "TEXT"),
            ("portrait_subject", "TEXT"),
            # Design fields
            ("obverse_legend", "TEXT"),
            ("obverse_description", "TEXT"),
            ("reverse_legend", "TEXT"),
            ("reverse_description", "TEXT"),
            ("exergue", "TEXT"),
        ]
        
        for col_name, col_type in new_columns:
            if not column_exists(conn, "coins_v2", col_name):
                print(f"  Adding column: {col_name}")
                conn.execute(f"ALTER TABLE coins_v2 ADD COLUMN {col_name} {col_type}")
            else:
                print(f"  Column already exists: {col_name}")
        
        # =====================================================================
        # 2. Create coin_references table
        # =====================================================================
        print("\nCreating coin_references table...")
        
        if not table_exists(conn, "coin_references"):
            conn.execute("""
                CREATE TABLE coin_references (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coin_id INTEGER NOT NULL,
                    catalog TEXT NOT NULL,
                    volume TEXT,
                    number TEXT NOT NULL,
                    suffix TEXT,
                    raw_text TEXT NOT NULL,
                    FOREIGN KEY(coin_id) REFERENCES coins_v2(id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX ix_coin_references_coin_id ON coin_references(coin_id)")
            conn.execute("CREATE INDEX ix_coin_references_catalog ON coin_references(catalog)")
            conn.execute("CREATE INDEX ix_coin_references_number ON coin_references(catalog, number)")
            print("  Created coin_references table with indexes")
        else:
            print("  Table already exists: coin_references")
        
        # =====================================================================
        # 3. Create provenance_events table
        # =====================================================================
        print("\nCreating provenance_events table...")
        
        if not table_exists(conn, "provenance_events"):
            conn.execute("""
                CREATE TABLE provenance_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coin_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    event_date TEXT,
                    lot_number TEXT,
                    notes TEXT,
                    raw_text TEXT,
                    FOREIGN KEY(coin_id) REFERENCES coins_v2(id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX ix_provenance_events_coin_id ON provenance_events(coin_id)")
            conn.execute("CREATE INDEX ix_provenance_events_source ON provenance_events(source_name)")
            print("  Created provenance_events table with indexes")
        else:
            print("  Table already exists: provenance_events")
        
        # =====================================================================
        # 4. Create indexes for filtering on coins_v2
        # =====================================================================
        print("\nCreating additional indexes for filtering...")
        
        indexes = [
            ("ix_coins_v2_denomination", "coins_v2", "denomination"),
            ("ix_coins_v2_grading_state", "coins_v2", "grading_state"),
            ("ix_coins_v2_grade_service", "coins_v2", "grade_service"),
        ]
        
        for idx_name, table, column in indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
                print(f"  Created index: {idx_name}")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    print(f"  Index already exists: {idx_name}")
                else:
                    raise
        
        conn.commit()
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
        # Print table info
        print("\nNew schema additions:")
        cursor = conn.execute("PRAGMA table_info(coins_v2)")
        cols = [row[1] for row in cursor.fetchall()]
        design_cols = [c for c in cols if c in ['denomination', 'portrait_subject', 'obverse_legend', 
                                                  'obverse_description', 'reverse_legend', 
                                                  'reverse_description', 'exergue']]
        print(f"  coins_v2 new columns: {', '.join(design_cols)}")
        
        cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='coin_references'")
        if cursor.fetchone()[0]:
            print("  coin_references table: created")
        
        cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='provenance_events'")
        if cursor.fetchone()[0]:
            print("  provenance_events table: created")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def main():
    print("=" * 60)
    print("Design, References & Provenance Migration")
    print("=" * 60)
    
    try:
        db_path = get_db_path()
        print(f"Database: {db_path}")
        
        # Create backup
        backup_path = backup_database(db_path)
        
        # Run migration
        run_migration(db_path)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run this script from the backend directory or ensure coinstack_v2.db exists")
        return 1
    except Exception as e:
        print(f"Migration failed: {e}")
        print("Database has been backed up. Please restore from backup if needed.")
        raise
    
    return 0


if __name__ == "__main__":
    exit(main())
