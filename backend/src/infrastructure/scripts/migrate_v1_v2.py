import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import logging

# Add current directory to path
sys.path.append(str(Path.cwd()))

from sqlalchemy import create_engine, text
from src.infrastructure.config import get_settings
from src.infrastructure.persistence.database import init_db, SessionLocal as V2SessionLocal
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO
from src.domain.coin import GradingState

logger = logging.getLogger(__name__)

def migrate():
    settings = get_settings()
    db_url = settings.DATABASE_URL
    print(f"Connecting to DB: {db_url}")
    engine = create_engine(db_url)
    
    print("Initializing V2 Schema (including images)...")
    init_db() 
    
    # Clean V2 tables
    with engine.connect() as conn:
        try:
            conn.execute(text("DELETE FROM coin_images_v2"))
            conn.execute(text("DELETE FROM coins_v2"))
            conn.commit()
            print("Cleaned existing V2 data.")
        except Exception as e:
            print(f"Warning cleaning V2: {e}")
    
    # 2. Extract V1 Data (Including Images)
    print("Extracting V1 Data...")
    
    v2_session = V2SessionLocal()
    repo = SqlAlchemyCoinRepository(v2_session)
    use_case = CreateCoinUseCase(repo) # Note: CreateCoin doesn't handle images yet in DTO
    
    success = 0
    failed = 0
    
    # We need to manually handle image migration because CreateCoinUseCase/DTO 
    # hasn't been updated to accept images yet. 
    # So we'll Create Coin -> Then Add Images directly via Repo/Entity.
    
    with engine.connect() as conn:
        # ATTACH V1 DATABASE
        v1_path = Path("data/coinstack.db").absolute()
        print(f"Attaching V1 DB: {v1_path}")
        conn.execute(text(f"ATTACH DATABASE '{v1_path}' AS v1"))

        # Get Coins
        v1_coins = conn.execute(text("""
            SELECT 
                c.id, c.category, c.metal, c.weight_g, c.diameter_mm, c.die_axis,
                c.issuing_authority, m.name as mint_name, 
                c.mint_year_start, c.mint_year_end,
                c.grade, c.grade_service, c.certification_number,
                c.acquisition_price, c.acquisition_source, c.acquisition_date
            FROM v1.coins c
            LEFT JOIN v1.mints m ON c.mint_id = m.id
        """)).fetchall()
        
        # Get Images map
        v1_images = conn.execute(text("""
            SELECT coin_id, file_path, image_type, is_primary 
            FROM v1.coin_images
        """)).fetchall()
        
        images_by_coin = {}
        for img in v1_images:
            if img.coin_id not in images_by_coin:
                images_by_coin[img.coin_id] = []
            images_by_coin[img.coin_id].append(img)

    print(f"Found {len(v1_coins)} coins and {len(v1_images)} images.")

    for row in v1_coins:
        try:
            # ... (Mapping logic same as before) ...
            cat_map = {
                "IMPERIAL": "roman_imperial",
                "PROVINCIAL": "roman_imperial",
                "REPUBLIC": "roman_republic"
            }
            category = cat_map.get(row.category, "greek")
            metal = row.metal.lower() if row.metal else "bronze"
            
            service_str = row.grade_service
            grade_service = None
            if service_str:
                service_str = service_str.lower()
                if service_str in ['ngc', 'pcgs', 'icg', 'anacs']:
                    grade_service = service_str
                else:
                    grade_service = 'none' 

            grading_state = GradingState.SLABBED.value if grade_service and grade_service != 'none' else GradingState.RAW.value
            
            acq_date = None
            if row.acquisition_date:
                if isinstance(row.acquisition_date, str):
                     try:
                         acq_date = datetime.strptime(row.acquisition_date, "%Y-%m-%d").date()
                     except ValueError:
                         acq_date = None
                else:
                    acq_date = row.acquisition_date
            
            weight_val = Decimal(str(row.weight_g)) if row.weight_g is not None else Decimal("0.0")
            diameter_val = Decimal(str(row.diameter_mm)) if row.diameter_mm is not None else Decimal("0.0")
            
            dto = CreateCoinDTO(
                category=category,
                metal=metal,
                weight_g=weight_val,
                diameter_mm=diameter_val,
                die_axis=row.die_axis,
                issuer=row.issuing_authority or "Unknown",
                mint=row.mint_name,
                year_start=row.mint_year_start,
                year_end=row.mint_year_end,
                grading_state=grading_state,
                grade=row.grade or "Unknown",
                grade_service=grade_service,
                certification=row.certification_number,
                acquisition_price=Decimal(str(row.acquisition_price)) if row.acquisition_price is not None else None,
                acquisition_source=row.acquisition_source,
                acquisition_date=acq_date
            )
            
            # 1. Create Coin
            coin = use_case.execute(dto)
            
            # 2. Add Images (Port from V1)
            # The UseCase returns a coin with a new ID (in memory if not committed, or DB id)
            # Since we cleared V2, IDs might change unless we force them. 
            # Ideally we want to preserve IDs? 
            # Repo.save() doesn't let us force ID easily with this DTO flow.
            # But wait, SqlAlchemyCoinRepository.save() uses merge().
            # If we want to preserve ID, we should set it on the Entity.
            
            # Hack: Manually update ID to match V1 for consistency? 
            # Or just let it generate new IDs. 
            # If we let it generate new, we lose the link to V1 images unless we use the V1 loop index.
            # Actually, `use_case.execute` returns the SAVED coin with ID.
            # But the mapping from V1 ID -> V2 ID is needed if we process images separately?
            # No, we are inside the loop for a specific V1 coin.
            
            # Retrieve V1 images for this coin
            coin_images = images_by_coin.get(row.id, [])
            
            for img_row in coin_images:
                # Fix path: V1 stored relative paths like 'coin_images/file.jpg'
                # V2 needs full URL or consistent path. 
                # Let's assume we serve 'data/' statically.
                # So if V1 path was 'coin_images/abc.jpg', URL is '/data/coin_images/abc.jpg'
                
                # Check if path is absolute or relative
                path = img_row.file_path
                # Normalize path for URL
                if '\\' in path: path = path.replace('\\', '/')
                
                # Ensure it starts with /data/ or similar for serving
                if not path.startswith('/'):
                    final_url = f"/data/{path}"
                else:
                    final_url = path
                    
                image_type = img_row.image_type.value if hasattr(img_row.image_type, 'value') else str(img_row.image_type)
                
                coin.add_image(final_url, image_type, img_row.is_primary)
            
            # Save again to persist images
            repo.save(coin)
            
            success += 1
            print(".", end="", flush=True)
            
        except Exception as e:
            failed += 1
            print("x", end="", flush=True)
            logger.error(f"Failed ID {row.id}: {e}")
            
    try:
        v2_session.commit()
        print(f"\nCommitted {success} records to V2.")
    except Exception as e:
        v2_session.rollback()
        print(f"\nError committing migration: {e}")

if __name__ == "__main__":
    migrate()