
import sys
import os
from sqlalchemy import create_engine, text, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Direct SQL check to avoid importing src structure complications
def check_coins_v2():
    # Assume default SQLite path
    db_path = "backend/coinstack.db" 
    if not os.path.exists(db_path):
        db_path = "coinstack.db" # Maybe running from backend dir
        
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("Checking coins_v2 table...")
        result = session.execute(text("SELECT id, issuer, year_start FROM coins_v2 WHERE id = 2"))
        row = result.fetchone()
        
        if row:
            print(f"ID: {row[0]}, Issuer: {row[1]}, Year Start: {row[2]}")
        else:
            print("Coin 2 not found in coins_v2")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_coins_v2()
