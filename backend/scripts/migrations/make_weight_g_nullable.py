"""
Make coins_v2.weight_g nullable (optional).

Allows slabbed coins and other cases where weight cannot be measured.
Run from backend directory: uv run python scripts/migrations/make_weight_g_nullable.py

Uses SQLite 3.25.1+ (RENAME COLUMN) and 3.35.0+ (DROP COLUMN).
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


def get_db_path() -> Path:
    """Resolve path to coinstack_v2.db."""
    possible = [
        Path("coinstack_v2.db"),
        Path("backend/coinstack_v2.db"),
        Path(__file__).resolve().parent.parent.parent / "coinstack_v2.db",
    ]
    for p in possible:
        if p.exists():
            return p
    raise FileNotFoundError("coinstack_v2.db not found")


def backup_database(db_path: Path) -> Path:
    """Create timestamped backup (database-safety rule)."""
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"coinstack_{ts}.db"
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")
    backups = sorted(
        backup_dir.glob("coinstack_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in backups[5:]:
        old.unlink()
        print(f"Removed old backup: {old}")
    return backup_path


def weight_g_is_not_null(conn: sqlite3.Connection) -> bool:
    """Return True if coins_v2.weight_g exists and is NOT NULL."""
    cur = conn.execute("PRAGMA table_info(coins_v2)")
    # row: cid, name, type, notnull, dflt_value, pk
    for row in cur.fetchall():
        if row[1] == "weight_g":
            return bool(row[3])
    return False


def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Return True if table has the given column."""
    cur = conn.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]


def _run_four_steps(conn: sqlite3.Connection) -> None:
    """Execute the four migration steps. Caller holds exclusive lock."""
    conn.execute("ALTER TABLE coins_v2 RENAME COLUMN weight_g TO weight_g_old")
    conn.execute("ALTER TABLE coins_v2 ADD COLUMN weight_g NUMERIC(10,2)")
    conn.execute("UPDATE coins_v2 SET weight_g = weight_g_old")
    conn.execute("ALTER TABLE coins_v2 DROP COLUMN weight_g_old")


def run_migration(db_path: Path) -> None:
    """Make weight_g nullable via RENAME -> ADD nullable -> UPDATE -> DROP.

    Uses BEGIN IMMEDIATE so we hold an exclusive lock for the duration. Note:
    SQLite (and Python's sqlite3) may still commit before each DDL, so the
    four steps are not fully atomic; if we fail mid-way, recovery runs.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        cur = conn.execute("SELECT sqlite_version()")
        version = cur.fetchone()[0]
        print(f"SQLite version: {version}")

        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coins_v2'")
        if not cur.fetchone():
            print("Table coins_v2 does not exist; nothing to migrate.")
            return

        if not weight_g_is_not_null(conn):
            print("weight_g is already nullable or missing; nothing to migrate.")
            return

        print("Making weight_g nullable...")
        conn.execute("BEGIN IMMEDIATE")
        try:
            _run_four_steps(conn)
            conn.commit()
            print("Migration complete: weight_g is now nullable.")
        except Exception as e:
            conn.rollback()
            # Recover if we have weight_g_old (RENAME ran) but migration didn't finish.
            # SQLite commits before each DDL, so we may be left with weight_g_old and/or weight_g.
            has_old = _table_has_column(conn, "coins_v2", "weight_g_old")
            has_new = _table_has_column(conn, "coins_v2", "weight_g")
            if has_old and not has_new:
                print("Recovering: ADD weight_g, UPDATE, DROP weight_g_old...")
                conn.execute("ALTER TABLE coins_v2 ADD COLUMN weight_g NUMERIC(10,2)")
                conn.execute("UPDATE coins_v2 SET weight_g = weight_g_old")
                conn.execute("ALTER TABLE coins_v2 DROP COLUMN weight_g_old")
                conn.commit()
                print("Recovery complete: weight_g is now nullable.")
            elif has_old and has_new:
                print("Recovering: DROP weight_g_old...")
                conn.execute("ALTER TABLE coins_v2 DROP COLUMN weight_g_old")
                conn.commit()
                print("Recovery complete: weight_g is now nullable.")
            elif not has_old and has_new:
                # Migration effectively done (e.g. exception after DROP).
                print("Migration already complete (weight_g present, weight_g_old gone).")
            else:
                raise RuntimeError("Migration failed and left DB inconsistent.") from e
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()


def main() -> None:
    try:
        db_path = get_db_path()
    except FileNotFoundError as e:
        print(f"Skip: {e}")
        return
    print(f"Database: {db_path}")
    backup_database(db_path)
    run_migration(db_path)


if __name__ == "__main__":
    main()
