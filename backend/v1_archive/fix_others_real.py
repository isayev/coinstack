
import sys
import os
from sqlalchemy import create_engine, text

def fix_others_real():
    db_path = "data/coinstack.db"
    engine = create_engine(f"sqlite:///{db_path}")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Fix C. Malleolus (ID 3) - Positive 96 to Negative 96
            print("Fixing Malleolus (ID 3)...")
            conn.execute(text("UPDATE coins_v2 SET year_start = -96, year_end = -96 WHERE id = 3"))
            conn.execute(text("UPDATE coins SET mint_year_start = -96, mint_year_end = -96, reign_start = -96, reign_end = -96 WHERE id = 3"))

            # Fix Augustus (ID 1) - Mint Date (-2) to Reign Date (-27) ?? 
            # User specifically listed Reign 27 BC - AD 14 in the task description.
            # Assuming they want the primary display to be Reign.
            print("Fixing Augustus (ID 1) to Reign dates...")
            conn.execute(text("UPDATE coins_v2 SET year_start = -27, year_end = 14 WHERE id = 1"))
            # Legacy table might differentiate reign/mint
            conn.execute(text("UPDATE coins SET reign_start = -27, reign_end = 14 WHERE id = 1"))

            trans.commit()
            print("Updates successful.")
            
        except Exception as e:
            trans.rollback()
            print(f"Update failed: {e}")

if __name__ == "__main__":
    fix_others_real()
