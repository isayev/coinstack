import sys
from pathlib import Path
# Add current directory to path so we can import 'src' and 'app'
sys.path.append(str(Path.cwd()))

from sqlalchemy import create_engine, text
from app.config import get_settings
# Import ORM to ensure tables are registered if needed (though verify just uses raw SQL)
import src.infrastructure.persistence.orm 

def verify():
    settings = get_settings()
    db_url = settings.DATABASE_URL
    # Normalize URL for script
    if db_url.startswith("sqlite:///./"):
        db_url = db_url.replace("sqlite:///./", "sqlite:///")
        
    print(f"Connecting to: {db_url}")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        try:
            v1_count = conn.execute(text("SELECT COUNT(*) FROM coins")).scalar()
            v2_count = conn.execute(text("SELECT COUNT(*) FROM coins_v2")).scalar()
            v2_img_count = conn.execute(text("SELECT COUNT(*) FROM coin_images_v2")).scalar()
            
            print(f"V1 Coins: {v1_count}")
            print(f"V2 Coins: {v2_count}")
            print(f"V2 Images: {v2_img_count}")
            
            if v1_count == v2_count:
                print("SUCCESS: Record counts match.")
            else:
                print("FAILURE: Record counts mismatch.")

            if v2_img_count > 0:
                print("SUCCESS: Images migrated.")
            else:
                print("WARNING: No images found in V2.")

        except Exception as e:
            print(f"Verification Error: {e}")

if __name__ == "__main__":
    verify()
