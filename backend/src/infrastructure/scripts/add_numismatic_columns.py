"""
Add advanced numismatic columns to coins_v2 table.

This migration adds columns for comprehensive numismatic cataloging:
- Iconography: obverse/reverse design elements, control marks
- Mint details: mintmark, field_marks
- Die study: die_state, die_match_notes
- Republican: moneyer name
- Edge: edge_type, edge_inscription
- Attribution: confidence level, notes
- Conservation: cleaning_history, conservation_notes
- Valuation: market_value, market_value_date

Usage:
    python -m src.infrastructure.scripts.add_numismatic_columns

Options:
    --verify  Only verify columns exist, don't add
    --dry-run  Show SQL without executing
"""

import argparse
import sqlite3
import sys
from pathlib import Path


# Columns to add
NUMISMATIC_COLUMNS = [
    # Iconography and design
    ("obverse_iconography", "TEXT"),
    ("reverse_iconography", "TEXT"),
    ("control_marks", "TEXT"),
    
    # Mint marks
    ("mintmark", "VARCHAR(50)"),
    ("field_marks", "TEXT"),
    
    # Die study
    ("die_state", "VARCHAR(20)"),
    ("die_match_notes", "TEXT"),
    
    # Republican coinage
    ("moneyer", "VARCHAR(100)"),
    
    # Edge details
    ("edge_type", "VARCHAR(30)"),
    ("edge_inscription", "TEXT"),
    
    # Attribution confidence
    ("attribution_confidence", "VARCHAR(20)"),
    ("attribution_notes", "TEXT"),
    
    # Conservation
    ("cleaning_history", "TEXT"),
    ("conservation_notes", "TEXT"),
    
    # Market value
    ("market_value", "DECIMAL(10,2)"),
    ("market_value_date", "DATE"),
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
        print(f"All numismatic columns present in {table}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Add numismatic columns to coins_v2 table")
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
        success = verify_columns(cursor, "coins_v2", NUMISMATIC_COLUMNS)
        sys.exit(0 if success else 1)
    
    # Add missing columns
    added = 0
    for column, col_type in NUMISMATIC_COLUMNS:
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
