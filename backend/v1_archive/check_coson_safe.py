
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.coin import Coin

def check_coson_safe():
    db: Session = SessionLocal()
    try:
        # Select ONLY specific columns tuple to avoid hydrating the full object
        # and triggering the Enum validation error
        results = db.query(
            Coin.id, 
            Coin.issuing_authority, 
            Coin.reign_start, 
            Coin.reign_end,
            Coin.mint_year_start,
            Coin.mint_year_end
        ).filter(
            Coin.issuing_authority == "Coson"
        ).all()
        
        print(f"Found {len(results)} matches:")
        for r in results:
            print(f"ID: {r.id}, Ruler: {r.issuing_authority}, Reign: {r.reign_start}/{r.reign_end}, Minted: {r.mint_year_start}/{r.mint_year_end}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_coson_safe()
