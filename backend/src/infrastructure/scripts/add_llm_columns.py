"""
Add LLM output columns to coins_v2 table.

This migration adds columns for storing LLM-generated content:
- obverse_legend_expanded: Expanded Latin legend (e.g., IMP -> Imperator)
- reverse_legend_expanded: Expanded reverse legend
- historical_significance: Historical context narrative
- catalog_description: Catalog-style description
- condition_observations: JSON string with wear/surface observations
- llm_enriched_at: Timestamp of last LLM enrichment

Usage:
    python -m src.infrastructure.scripts.add_llm_columns

Options:
    --verify  Only verify columns exist, don't add
    --dry-run  Show SQL without executing
"""

import argparse
import sqlite3
import sys
from pathlib import Path


# Columns to add
LLM_COLUMNS = [
    ("obverse_legend_expanded", "TEXT"),
    ("reverse_legend_expanded", "TEXT"),
    ("historical_significance", "TEXT"),
    ("catalog_description", "TEXT"),
    ("condition_observations", "TEXT"),
    ("llm_enriched_at", "DATETIME"),
]


def get_existing_columns(cursor: sqlite3.Cursor, table: str) -> set:
    """Get existing column names for a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def add_column(cursor: sqlite3.Cursor, table: str, column: str, col_type: str, dry_run: bool = False):
    """Add a column to a table if it doesn't exist."""
    sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
    if dry_run:
        print(f"[DRY RUN] {sql}")
    else:
        cursor.execute(sql)
        print(f"Added column: {table}.{column}")


def verify_columns(cursor: sqlite3.Cursor, table: str, columns: list) -> bool:
    """Verify all columns exist."""
    existing = get_existing_columns(cursor, table)
    missing = [col for col, _ in columns if col not in existing]
    
    if missing:
        print(f"Missing columns in {table}: {', '.join(missing)}")
        return False
    else:
        print(f"All LLM columns present in {table}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Add LLM columns to coins_v2 table")
    parser.add_argument("--verify", action="store_true", help="Only verify columns exist")
    parser.add_argument("--dry-run", action="store_true", help="Show SQL without executing")
    parser.add_argument("--db", default="coinstack_v2.db", help="Database path")
    args = parser.parse_args()
    
    # Find database
    db_paths = [
        Path(args.db),
        Path("backend") / args.db,
        Path(__file__).parent.parent.parent.parent / args.db,
    ]
    
    db_path = None
    for p in db_paths:
        if p.exists():
            db_path = p
            break
    
    if not db_path:
        print(f"Database not found. Tried: {', '.join(str(p) for p in db_paths)}")
        sys.exit(1)
    
    print(f"Using database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coins_v2'")
    if not cursor.fetchone():
        print("Table coins_v2 does not exist!")
        sys.exit(1)
    
    existing_columns = get_existing_columns(cursor, "coins_v2")
    
    if args.verify:
        success = verify_columns(cursor, "coins_v2", LLM_COLUMNS)
        sys.exit(0 if success else 1)
    
    # Add missing columns
    added = 0
    for column, col_type in LLM_COLUMNS:
        if column not in existing_columns:
            add_column(cursor, "coins_v2", column, col_type, dry_run=args.dry_run)
            added += 1
        else:
            print(f"Column already exists: {column}")
    
    if not args.dry_run:
        conn.commit()
    
    conn.close()
    
    print(f"\nMigration complete. Added {added} new columns.")


if __name__ == "__main__":
    main()
