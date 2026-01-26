import sqlite3
import sys
from pathlib import Path

def get_db_path() -> Path:
    possible_paths = [
        Path("backend/coinstack_v2.db"),
        Path("coinstack_v2.db")
    ]
    for path in possible_paths:
        if path.exists():
            return path
    raise FileNotFoundError("DB not found")

def verify():
    db_path = get_db_path()
    print(f"Verifying DB: {db_path}")
    conn = sqlite3.connect(db_path)
    
    try:
        # 1. Check Columns in coins_v2
        cursor = conn.execute("PRAGMA table_info(coins_v2)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required = [
            'issue_status', 'specific_gravity', 'obverse_die_id', 
            'reverse_die_id', 'secondary_treatments', 'find_spot', 'find_date'
        ]
        
        print("\nChecking coins_v2 columns:")
        missing = []
        for col in required:
            if col in columns:
                print(f"  [OK] {col} ({columns[col]})")
            else:
                print(f"  [FAIL] {col} MISSING")
                missing.append(col)
        
        if missing:
            print("FAILED: Missing columns in coins_v2")
            return 1

        # 2. Check Tables
        print("\nChecking new tables:")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'monograms' in tables:
            print("  [OK] monograms table exists")
        else:
            print("  [FAIL] monograms table MISSING")
            return 1
            
        if 'coin_monograms' in tables:
            print("  [OK] coin_monograms table exists")
        else:
            print("  [FAIL] coin_monograms table MISSING")
            return 1
            
        print("\nAll Schema Checks Passed.")
        
        # 3. Data Integrity Check (Select a few rows)
        print("\nChecking data access...")
        cursor = conn.execute("SELECT id, issue_status FROM coins_v2 LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  Coin {row[0]}: status={row[1]}")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1
    finally:
        conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(verify())
