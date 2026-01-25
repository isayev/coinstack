
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.coin import Coin
from app.models.auction_data import AuctionData

def inspect_bc_coins():
    db: Session = SessionLocal()
    try:
        print("Searching for coins with 'BC' in AuctionData...")
        results = db.query(
            Coin.id, 
            Coin.reign_start, 
            Coin.reign_end, 
            AuctionData.reign_dates
        ).join(
            AuctionData, Coin.id == AuctionData.coin_id
        ).filter(
            AuctionData.reign_dates.ilike("%BC%")
        ).limit(20).all()
        
        print(f"Found {len(results)} (showing max 20):")
        for r in results:
            print(f"ID: {r.id}, Start: {r.reign_start}, End: {r.reign_end}, Raw: '{r.reign_dates}'")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_bc_coins()
