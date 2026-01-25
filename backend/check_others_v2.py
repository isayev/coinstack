
import sys
import os
from sqlalchemy import create_engine, text

def check_others_v2():
    db_path = "data/coinstack.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found!")
        return

    print(f"Connecting to {db_path}...")
    engine = create_engine(f"sqlite:///{db_path}")
    
    with engine.connect() as conn:
        print("Searching for Augustus and Malleolus...")
        # Search by issuer
        result = conn.execute(text("SELECT id, issuer, year_start, year_end, mint, grading_state FROM coins_v2 WHERE issuer LIKE '%Augustus%' OR issuer LIKE '%Malleolus%' OR issuer LIKE '%Coson%'"))
        
        for row in result:
            print(f"ID: {row[0]}, Issuer: {row[1]}, Year Start: {row[2]}, Year End: {row[3]}, Mint: {row[4]}")

if __name__ == "__main__":
    check_others_v2()
