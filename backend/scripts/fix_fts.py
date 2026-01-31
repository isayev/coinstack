import sqlite3
import os
import sys

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.config import get_settings

def fix_fts():
    settings = get_settings()
    db_url = settings.DATABASE_URL
    
    if not db_url.startswith("sqlite:///"):
        print("This script is intended for SQLite databases only.")
        return

    db_path = db_url.replace("sqlite:///", "")
    print(f"Connecting to database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Create FTS5 virtual table
        print("Creating virtual table 'vocab_terms_fts'...")
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS vocab_terms_fts USING fts5(
                canonical_name,
                vocab_type,
                content='vocab_terms',
                content_rowid='id'
            );
        """)

        # 2. Create Triggers
        print("Creating triggers for synchronization...")
        
        # After Insert
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS vocab_terms_ai AFTER INSERT ON vocab_terms BEGIN
              INSERT INTO vocab_terms_fts(rowid, canonical_name, vocab_type) VALUES (new.id, new.canonical_name, new.vocab_type);
            END;
        """)

        # After Delete
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS vocab_terms_ad AFTER DELETE ON vocab_terms BEGIN
              INSERT INTO vocab_terms_fts(vocab_terms_fts, rowid, canonical_name, vocab_type) VALUES('delete', old.id, old.canonical_name, old.vocab_type);
            END;
        """)

        # After Update
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS vocab_terms_au AFTER UPDATE ON vocab_terms BEGIN
              INSERT INTO vocab_terms_fts(vocab_terms_fts, rowid, canonical_name, vocab_type) VALUES('delete', old.id, old.canonical_name, old.vocab_type);
              INSERT INTO vocab_terms_fts(rowid, canonical_name, vocab_type) VALUES (new.id, new.canonical_name, new.vocab_type);
            END;
        """)

        # 3. Rebuild Index
        print("Rebuilding FTS index from existing data...")
        cursor.execute("INSERT INTO vocab_terms_fts(vocab_terms_fts) VALUES('rebuild');")

        conn.commit()
        print("Successfully fixed FTS5 table and triggers.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_fts()
