"""
Vocab V3 Migration Script

This script migrates the database to the V3 controlled vocabulary schema.
Run from backend directory: python -m scripts.migrations.migrate_vocab_v3

Features:
- Creates vocab_terms table with FTS5 index
- Creates coin_vocab_assignments table for audit trail
- Creates vocab_cache table
- Adds FK columns to coins_v2 (issuer_term_id, mint_term_id, denomination_term_id, dynasty_term_id)
- Adds canonical_vocab_id to series table
- Bootstraps dynasty and canonical series data
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime


def get_db_path() -> Path:
    """Get path to the database file."""
    # Look for database in standard locations
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
    
    import shutil
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
    """Run the V3 vocabulary migration."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        # 1. Create vocab_terms table
        print("Creating vocab_terms table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vocab_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vocab_type TEXT NOT NULL,
                canonical_name TEXT NOT NULL,
                nomisma_uri TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vocab_type, canonical_name)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ix_vocab_terms_type ON vocab_terms(vocab_type)")
        
        # 2. Create FTS5 virtual table (if not exists)
        print("Creating FTS5 index...")
        # Check if FTS table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vocab_terms_fts'"
        )
        if not cursor.fetchone():
            conn.execute("""
                CREATE VIRTUAL TABLE vocab_terms_fts USING fts5(
                    canonical_name, 
                    content=vocab_terms, 
                    content_rowid=id,
                    tokenize='porter unicode61'
                )
            """)
            
            # Create triggers for FTS sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS vocab_terms_ai AFTER INSERT ON vocab_terms BEGIN
                    INSERT INTO vocab_terms_fts(rowid, canonical_name) VALUES (new.id, new.canonical_name);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS vocab_terms_ad AFTER DELETE ON vocab_terms BEGIN
                    INSERT INTO vocab_terms_fts(vocab_terms_fts, rowid, canonical_name) VALUES('delete', old.id, old.canonical_name);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS vocab_terms_au AFTER UPDATE ON vocab_terms BEGIN
                    INSERT INTO vocab_terms_fts(vocab_terms_fts, rowid, canonical_name) VALUES('delete', old.id, old.canonical_name);
                    INSERT INTO vocab_terms_fts(rowid, canonical_name) VALUES (new.id, new.canonical_name);
                END
            """)
        
        # 3. Create coin_vocab_assignments table
        print("Creating coin_vocab_assignments table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS coin_vocab_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                raw_value TEXT NOT NULL,
                vocab_term_id INTEGER,
                confidence REAL,
                method TEXT,
                status TEXT DEFAULT 'assigned',
                assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT,
                FOREIGN KEY(coin_id) REFERENCES coins_v2(id),
                FOREIGN KEY(vocab_term_id) REFERENCES vocab_terms(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ix_cva_coin ON coin_vocab_assignments(coin_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_cva_status ON coin_vocab_assignments(status)")
        
        # 4. Create vocab_cache table
        print("Creating vocab_cache table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vocab_cache (
                cache_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ix_vocab_cache_expires ON vocab_cache(expires_at)")
        
        # 5. Add FK columns to coins_v2
        print("Adding vocab FK columns to coins_v2...")
        new_columns = [
            ("issuer_term_id", "INTEGER REFERENCES vocab_terms(id)"),
            ("mint_term_id", "INTEGER REFERENCES vocab_terms(id)"),
            ("denomination_term_id", "INTEGER REFERENCES vocab_terms(id)"),
            ("dynasty_term_id", "INTEGER REFERENCES vocab_terms(id)"),
        ]
        
        for col_name, col_type in new_columns:
            if not column_exists(conn, "coins_v2", col_name):
                print(f"  Adding column: {col_name}")
                conn.execute(f"ALTER TABLE coins_v2 ADD COLUMN {col_name} {col_type}")
            else:
                print(f"  Column already exists: {col_name}")
        
        # 6. Add canonical_vocab_id to series table
        print("Adding canonical_vocab_id to series table...")
        if table_exists(conn, "series"):
            if not column_exists(conn, "series", "canonical_vocab_id"):
                conn.execute("ALTER TABLE series ADD COLUMN canonical_vocab_id INTEGER REFERENCES vocab_terms(id)")
                print("  Added canonical_vocab_id column")
            else:
                print("  Column already exists: canonical_vocab_id")
        else:
            print("  Series table does not exist, skipping")
        
        # 7. Bootstrap dynasty data
        print("Bootstrapping dynasty data...")
        dynasties = [
            ('dynasty', 'Julio-Claudian', '{"period_start": -27, "period_end": 68, "rulers": ["Augustus", "Tiberius", "Caligula", "Claudius", "Nero"]}'),
            ('dynasty', 'Flavian', '{"period_start": 69, "period_end": 96, "rulers": ["Vespasian", "Titus", "Domitian"]}'),
            ('dynasty', 'Nerva-Antonine', '{"period_start": 96, "period_end": 192, "rulers": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius", "Lucius Verus", "Commodus"]}'),
            ('dynasty', 'Severan', '{"period_start": 193, "period_end": 235, "rulers": ["Septimius Severus", "Caracalla", "Geta", "Macrinus", "Elagabalus", "Severus Alexander"]}'),
            ('dynasty', 'Constantinian', '{"period_start": 306, "period_end": 363, "rulers": ["Constantine I", "Constantine II", "Constans", "Constantius II", "Julian"]}'),
            ('dynasty', 'Theodosian', '{"period_start": 379, "period_end": 455, "rulers": ["Theodosius I", "Arcadius", "Honorius", "Theodosius II"]}'),
            ('dynasty', 'Tetrarchy', '{"period_start": 284, "period_end": 324, "rulers": ["Diocletian", "Maximian", "Constantius I", "Galerius"]}'),
            ('dynasty', 'Valentinianic', '{"period_start": 364, "period_end": 392, "rulers": ["Valentinian I", "Valens", "Gratian", "Valentinian II"]}'),
            ('dynasty', 'Year of Four Emperors', '{"period_start": 69, "period_end": 69, "rulers": ["Galba", "Otho", "Vitellius", "Vespasian"]}'),
            ('dynasty', 'Military Emperors', '{"period_start": 235, "period_end": 284, "rulers": ["Maximinus I", "Gordian I", "Gordian II", "Gordian III", "Philip I", "Decius", "Trebonianus Gallus", "Valerian", "Gallienus"]}'),
            ('dynasty', 'Gallic Empire', '{"period_start": 260, "period_end": 274, "rulers": ["Postumus", "Victorinus", "Tetricus I", "Tetricus II"]}'),
            ('dynasty', 'Late Republic', '{"period_start": -133, "period_end": -27, "rulers": ["Sulla", "Pompey", "Caesar", "Brutus", "Cassius", "Mark Antony", "Octavian"]}'),
        ]
        
        for vocab_type, name, metadata in dynasties:
            conn.execute(
                "INSERT OR IGNORE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES (?, ?, ?)",
                (vocab_type, name, metadata)
            )
        
        # 8. Bootstrap canonical series
        print("Bootstrapping canonical series...")
        series = [
            ('canonical_series', 'Twelve Caesars', '{"expected_count": 12, "rulers": ["Julius Caesar", "Augustus", "Tiberius", "Caligula", "Claudius", "Nero", "Galba", "Otho", "Vitellius", "Vespasian", "Titus", "Domitian"], "category": "imperial", "description": "The twelve rulers from Julius Caesar through Domitian, as chronicled by Suetonius"}'),
            ('canonical_series', 'Five Good Emperors', '{"expected_count": 5, "rulers": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius"], "category": "imperial", "description": "The five emperors who presided over the most prosperous era in Roman history (96-180 AD)"}'),
            ('canonical_series', 'Year of Four Emperors', '{"expected_count": 4, "rulers": ["Galba", "Otho", "Vitellius", "Vespasian"], "category": "imperial", "description": "The four emperors who ruled in 69 AD during the civil war"}'),
            ('canonical_series', 'Adoptive Emperors', '{"expected_count": 5, "rulers": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius"], "category": "imperial", "description": "Emperors who adopted their successors rather than passing power to biological heirs"}'),
            ('canonical_series', 'Severan Dynasty', '{"expected_count": 6, "rulers": ["Septimius Severus", "Caracalla", "Geta", "Macrinus", "Elagabalus", "Severus Alexander"], "category": "imperial", "description": "The Severan dynasty emperors (193-235 AD)"}'),
            ('canonical_series', 'Julio-Claudian Dynasty', '{"expected_count": 5, "rulers": ["Augustus", "Tiberius", "Caligula", "Claudius", "Nero"], "category": "imperial", "description": "The first Roman imperial dynasty"}'),
            ('canonical_series', 'Flavian Dynasty', '{"expected_count": 3, "rulers": ["Vespasian", "Titus", "Domitian"], "category": "imperial", "description": "The Flavian dynasty emperors (69-96 AD)"}'),
            ('canonical_series', 'Constantinian Dynasty', '{"expected_count": 5, "rulers": ["Constantine I", "Constantine II", "Constans", "Constantius II", "Julian"], "category": "imperial", "description": "The Constantinian dynasty emperors (306-363 AD)"}'),
        ]
        
        for vocab_type, name, metadata in series:
            conn.execute(
                "INSERT OR IGNORE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES (?, ?, ?)",
                (vocab_type, name, metadata)
            )
        
        conn.commit()
        print("\nMigration completed successfully!")
        
        # Print summary
        cursor = conn.execute("SELECT vocab_type, COUNT(*) FROM vocab_terms GROUP BY vocab_type")
        print("\nVocab terms summary:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} entries")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def main():
    print("=" * 60)
    print("Vocab V3 Migration")
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
