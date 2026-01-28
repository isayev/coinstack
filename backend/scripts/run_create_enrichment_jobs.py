#!/usr/bin/env python3
"""
Run create_enrichment_jobs_table.sql against the project DB.
Use when enrichment_jobs does not exist; then re-run enrichment.
No migration—standalone. Backup before use if required by project rules.
"""
import os
import sqlite3

# DB path: coinstack_v2.db in backend/ (script lives in backend/scripts/)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, "coinstack_v2.db")
SQL_PATH = os.path.join(os.path.dirname(__file__), "create_enrichment_jobs_table.sql")


def main():
    if not os.path.exists(DB_PATH):
        print(f"DB not found: {DB_PATH}")
        return 1
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(sql)
        conn.commit()
        print("enrichment_jobs table created or already exists.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
