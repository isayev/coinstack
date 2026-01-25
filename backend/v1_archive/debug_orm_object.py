
import sys
import os
from sqlalchemy.orm import Session, defer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.coin import Coin

def debug_orm():
    db: Session = SessionLocal()
    try:
        print("Loading Coin 2 via ORM...")
        # Defer enum fields that might cause crashes
        coin = db.query(Coin).filter(Coin.id == 2).options(
            defer(Coin.grade_service),
            defer(Coin.holder_type),
            defer(Coin.rarity),
            defer(Coin.orientation),
            defer(Coin.dating_certainty),
            defer(Coin.category),
            defer(Coin.metal)
        ).first()

        if coin:
            print(f"Coin ID: {coin.id}")
            print(f"Mint Year Start (ORM): {coin.mint_year_start}")
            print(f"Reign Start (ORM): {coin.reign_start}")
        else:
            print("Coin 2 not found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_orm()
