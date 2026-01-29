"""
One-time data migration: normalize existing grade values in coins_v2.

Applies the same rule as normalize_grade_for_storage: strip, collapse spaces, uppercase.
Run from repo root or backend directory. Back up the database first (see database-safety rules).

Usage:
  cd backend && python scripts/normalize_grades_in_db.py
  # or from repo root:
  python backend/scripts/normalize_grades_in_db.py
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Resolve path to coinstack_v2.db."""
    possible = [
        Path("coinstack_v2.db"),
        Path("backend/coinstack_v2.db"),
        Path(__file__).resolve().parent.parent / "coinstack_v2.db",
    ]
    for p in possible:
        if p.exists():
            return p
    raise FileNotFoundError("coinstack_v2.db not found in current directory or backend/")


def normalize_grade(grade: str | None) -> str | None:
    """Same logic as application grade_normalizer: strip, collapse spaces, upper."""
    if not grade or not grade.strip():
        return None
    return " ".join(grade.strip().split()).upper()


def run_migration(db_path: Path) -> tuple[int, int]:
    """Normalize all non-empty grades in coins_v2. Returns (updated_count, total_with_grade)."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        cur = conn.execute(
            "SELECT id, grade FROM coins_v2 WHERE grade IS NOT NULL AND TRIM(grade) != ''"
        )
        rows = cur.fetchall()
        total = len(rows)
        updated = 0
        for (coin_id, grade) in rows:
            normalized = normalize_grade(grade)
            if normalized is None:
                continue
            if normalized != grade:
                conn.execute("UPDATE coins_v2 SET grade = ? WHERE id = ?", (normalized, coin_id))
                updated += 1
        conn.commit()
        return (updated, total)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> int:
    try:
        db_path = get_db_path()
        print(f"Database: {db_path}")
        print("Normalizing grade values (strip, collapse spaces, uppercase)...")
        updated, total = run_migration(db_path)
        print(f"Coins with grade: {total}")
        print(f"Updated: {updated}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Failed: {e}")
        raise


if __name__ == "__main__":
    exit(main())
