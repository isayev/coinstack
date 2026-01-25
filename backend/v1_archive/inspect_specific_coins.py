
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, or_

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.coin import Coin


def inspect_specific_coins():
    db: Session = SessionLocal()
    try:
        rulers = ["Augustus", "Coson", "C. Malleolus"]
        print(f"Searching for rulers: {rulers}")
        
        # Select specific columns to avoid enum validation issues
        coins = db.query(
            Coin.id,
            Coin.issuing_authority,
            Coin.reign_start,
            Coin.reign_end,
            Coin.mint_year_start,
            Coin.mint_year_end
        ).filter(
            or_(
                Coin.issuing_authority.in_(rulers),
                Coin.portrait_subject.in_(rulers)
            )
        ).all()
        
        print(f"Found {len(coins)} coins:")
        for c in coins:
            print(f"ID: {c.id}")
            print(f"  Ruler: {c.issuing_authority}")
            print(f"  Reign: {c.reign_start} to {c.reign_end}")
            print(f"  Minted: {c.mint_year_start} to {c.mint_year_end}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    inspect_specific_coins()
