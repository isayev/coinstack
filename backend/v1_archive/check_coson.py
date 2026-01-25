
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.coin import Coin

def check_coson():
    db: Session = SessionLocal()
    try:
        coins = db.query(Coin).filter(Coin.issuing_authority == "Coson").all()
        for c in coins:
            print(f"ID: {c.id}, Ruler: {c.issuing_authority}, Reign: {c.reign_start} to {c.reign_end}")
    finally:
        db.close()

if __name__ == "__main__":
    check_coson()
