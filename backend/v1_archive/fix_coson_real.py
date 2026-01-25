
import sys
import os
from sqlalchemy import create_engine, text

def fix_coson_real():
    # Target the DATA directory DB
    db_path = "data/coinstack.db"
    
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found!")
        return

    print(f"Connecting to {db_path}...")
    engine = create_engine(f"sqlite:///{db_path}")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Update coins_v2 if it exists
            try:
                print("Attempting to update coins_v2...")
                result = conn.execute(text("UPDATE coins_v2 SET year_start = -54, year_end = -54 WHERE id = 2"))
                print(f"coins_v2 rows updated: {result.rowcount}")
                
                # Check value
                res = conn.execute(text("SELECT year_start FROM coins_v2 WHERE id = 2"))
                print(f"coins_v2 new value: {res.scalar()}")
                
            except Exception as e:
                print(f"coins_v2 update failed (maybe table missing): {e}")

            # 2. Update coins table (legacy?) if it exists
            try:
                print("Attempting to update coins...")
                # Note: Schema might use different column names? 
                # src CoinModel uses year_start. app Coin model uses mint_year_start.
                # Let's try both names just in case.
                
                # Check columns first? No, just try update.
                result = conn.execute(text("UPDATE coins SET mint_year_start = -54, mint_year_end = -54, reign_start = -54, reign_end = -54 WHERE id = 2"))
                print(f"coins rows updated: {result.rowcount}")
                
                res = conn.execute(text("SELECT mint_year_start FROM coins WHERE id = 2"))
                print(f"coins new value: {res.scalar()}")
                
            except Exception as e:
                print(f"coins update failed: {e}")

            trans.commit()
            print("Commit successful.")
            
        except Exception as e:
            trans.rollback()
            print(f"Transaction failed: {e}")

if __name__ == "__main__":
    fix_coson_real()
