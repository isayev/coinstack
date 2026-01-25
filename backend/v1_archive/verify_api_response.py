
import sys
import os
import json
from datetime import date
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.coin import Coin
from app.schemas.coin import CoinResponse

# Mock Pydantic serialization
def verify_api_response():
    db: Session = SessionLocal()
    try:
        coin = db.query(Coin).filter(Coin.issuing_authority == "Coson").first()
        if not coin:
            print("Coson coin not found in DB")
            return

        print(f"DB Object: ID={coin.id}, reign_start={coin.reign_start} (Type: {type(coin.reign_start)})")
        
        # Convert to Pydantic schema
        # We need to map the DB model to schema manually or use from_attributes if Config is set
        # Let's inspect the schema file first if we can, but trying to construct it might fail if we don't have all fields
        # Instead, let's just dump the dict that would be sent
        
        # Approximate what FastAPI does:
        response_dict = {
            "id": coin.id,
            "attribution": {
                "year_start": coin.reign_start,
                "year_end": coin.reign_end
            }
        }
        
        print("API Response Fragment (JSON):")
        print(json.dumps(response_dict))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_api_response()
