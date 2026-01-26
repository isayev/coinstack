"""
Research Extensions Migration Script (V2.1)

This script migrates the database to include Research Grade Extensions.
- Die Linking (obverse_die_id, reverse_die_id)
- Issue Status (official, fourree, etc.)
- Secondary Treatments (JSON)
- Monograms (Table + Link Table)
- Metrology (specific_gravity)
- Find Data (find_spot, find_date)

Run from backend directory: python -m scripts.migrations.migrate_research_extensions
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
import shutil

def get_db_path() -> Path:
    """Get path to the database file."""
    possible_paths = [
        Path("backend/coinstack_v2.db"),
        Path("coinstack_v2.db"),
        Path(__file__).parent.parent.parent / "coinstack_v2.db",
        Path("C:/vibecode/coinstack/backend/coinstack_v2.db")
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
    backup_path = backup_dir / f"coinstack_{timestamp}_research_ext.db"
    
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def run_migration(db_path: Path):
    """Run the Research Extensions migration."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        print("Starting Research Extensions Migration...")

        # 1. Add new columns to coins_v2
        print("Adding new columns to coins_v2...")
        new_columns = [
            ("issue_status", "TEXT DEFAULT 'official'"),
            ("specific_gravity", "REAL"),
            ("obverse_die_id", "TEXT"),
            ("reverse_die_id", "TEXT"),
            ("secondary_treatments", "TEXT"),
            ("find_spot", "TEXT"),
            ("find_date", "DATE"), # SQLite uses TEXT/NUMERIC for dates usually
        ]
        
        for col_name, col_type in new_columns:
            if not column_exists(conn, "coins_v2", col_name):
                print(f"  Adding column: {col_name}")
                # Update existing records for issue_status to have default 'official'
                if col_name == "issue_status":
                     conn.execute(f"ALTER TABLE coins_v2 ADD COLUMN {col_name} {col_type}")
                     conn.execute("UPDATE coins_v2 SET issue_status = 'official' WHERE issue_status IS NULL")
                else:
                    conn.execute(f"ALTER TABLE coins_v2 ADD COLUMN {col_name} {col_type}")
            else:
                print(f"  Column already exists: {col_name}")

        # 2. Create index on die ids and issue_status
        print("Creating indexes...")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_coins_v2_obv_die ON coins_v2(obverse_die_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_coins_v2_rev_die ON coins_v2(reverse_die_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_coins_v2_issue_status ON coins_v2(issue_status)")

        # 3. Create Monograms table
        print("Creating monograms table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS monograms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                image_url TEXT,
                vector_data TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ix_monograms_label ON monograms(label)")

        # 4. Create Link Table
        print("Creating coin_monograms table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS coin_monograms (
                coin_id INTEGER NOT NULL,
                monogram_id INTEGER NOT NULL,
                PRIMARY KEY (coin_id, monogram_id),
                FOREIGN KEY(coin_id) REFERENCES coins_v2(id),
                FOREIGN KEY(monogram_id) REFERENCES monograms(id)
            )
        """)
        
        conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    try:
        db_path = get_db_path()
        print(f"Database: {db_path}")
        
        # Backup
        backup_database(db_path)
        
        # Migration
        run_migration(db_path)
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
