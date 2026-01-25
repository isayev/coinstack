
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.auction_data import AuctionData

def count_auction_data():
    db: Session = SessionLocal()
    try:
        count = db.query(AuctionData).count()
        print(f"Total AuctionData records: {count}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    count_auction_data()
