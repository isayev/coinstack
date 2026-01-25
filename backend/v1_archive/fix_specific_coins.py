
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, update

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.coin import Coin

def fix_specific_coins():
    db: Session = SessionLocal()
    try:
        # 1. Coson (54 BC)
        print("Fixing Coson...")
        stmt = update(Coin).where(Coin.issuing_authority == "Coson").values(
            reign_start=-54,
            reign_end=-54,
            mint_year_start=-54,
            mint_year_end=-54
        )
        result = db.execute(stmt)
        print(f"  Updated {result.rowcount} rows.")

        # 2. C. Malleolus (96 BC)
        print("Fixing C. Malleolus...")
        stmt = update(Coin).where(Coin.issuing_authority == "C. Malleolus").values(
            reign_start=-96,
            reign_end=-96,
            mint_year_start=-96,
            mint_year_end=-96
        )
        result = db.execute(stmt)
        print(f"  Updated {result.rowcount} rows.")
        
        # 3. Augustus (27 BC - AD 14, Mint 2 BC - AD 4)
        # Assuming ID 1 or name match. User's ID was 17. Safe to update by name.
        print("Fixing Augustus...")
        stmt = update(Coin).where(Coin.issuing_authority == "Augustus").values(
            reign_start=-27,
            reign_end=14,
            mint_year_start=-2,
            mint_year_end=4
        )
        result = db.execute(stmt)
        print(f"  Updated {result.rowcount} rows.")

        db.commit()
        print("Done.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_specific_coins()
