"""
Add variant, mint, supplement, collection columns to reference_types table.

Catalog-specific fields for RIC/Crawford/RPC/SNG. Run from backend directory:
  uv run python scripts/migrations/add_reference_type_variant_mint_supplement_collection.py
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


def get_db_path() -> Path:
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
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"coinstack_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")
    backups = sorted(
        backup_dir.glob("coinstack_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old_backup in backups[5:]:
        old_backup.unlink()
        print(f"Removed old backup: {old_backup}")
    return backup_path


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cursor.fetchall()]


def run_migration(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        added = []
        for col, typ in [
            ("variant", "VARCHAR(10)"),
            ("mint", "VARCHAR(30)"),
            ("supplement", "VARCHAR(10)"),
            ("collection", "VARCHAR(50)"),
        ]:
            if not column_exists(conn, "reference_types", col):
                conn.execute(f"ALTER TABLE reference_types ADD COLUMN {col} {typ} NULL")
                added.append(col)
        if added:
            conn.commit()
            print(f"Added columns reference_types: {added}")
        else:
            print("Columns reference_types.variant, mint, supplement, collection already exist.")
    finally:
        conn.close()


def main() -> None:
    db_path = get_db_path()
    backup_database(db_path)
    run_migration(db_path)
    print("Migration complete.")


if __name__ == "__main__":
    main()
