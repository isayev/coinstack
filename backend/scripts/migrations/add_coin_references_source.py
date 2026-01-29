"""
Add source column to coin_references table.

Tracks origin of each reference link: user, import, scraper, llm_approved, catalog_lookup.
Run from backend directory: uv run python scripts/migrations/add_coin_references_source.py
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
    """Create a timestamped backup of the database (per database-safety rule)."""
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
        if not column_exists(conn, "coin_references", "source"):
            conn.execute(
                "ALTER TABLE coin_references ADD COLUMN source VARCHAR(30) NULL"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_coin_references_source "
                "ON coin_references(source)"
            )
            conn.commit()
            print("Added column coin_references.source and index.")
        else:
            print("Column coin_references.source already exists.")
    finally:
        conn.close()


def main() -> None:
    db_path = get_db_path()
    backup_database(db_path)
    run_migration(db_path)
    print("Migration complete.")


if __name__ == "__main__":
    main()
