
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, update

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.coin import Coin
from app.models.auction_data import AuctionData
from app.services.excel_import import parse_reign_years

def repair_bc_dates(dry_run: bool = True):
    db: Session = SessionLocal()
    try:
        print(f"Starting date repair (Dry Run: {dry_run})...")
        
        # Query specific columns to avoid hydrating Coin objects (which triggers Enum checks)
        # We need Coin ID, dates, and the raw AuctionData string
        results = db.query(
            Coin.id, 
            Coin.reign_start, 
            Coin.reign_end, 
            AuctionData.reign_dates
        ).join(
            AuctionData, Coin.id == AuctionData.coin_id
        ).filter(
            AuctionData.reign_dates.ilike("%BC%")
        ).all()
        
        fixed_count = 0
        
        for coin_id, current_start, current_end, raw_dates in results:
            if not raw_dates:
                continue
                
            # Re-parse utilizing the NEW logic
            start, end = parse_reign_years(raw_dates)
            
            if start is None:
                continue
                
            # Check if current values match new parsed values
            # Handle None values in DB
            c_start = current_start
            c_end = current_end
            
            if c_start == start and c_end == end:
                continue
            
            # Additional check: If coin has positive dates but raw says BC, we fix it.
            # Or if dates are missing.
            
            needs_fix = False
            if c_start is None:
                needs_fix = True
            elif start < 0 and c_start > 0:
                # Mismatch: DB has AD, source has BC
                needs_fix = True
            elif start != c_start:
                # Just different
                needs_fix = True
                
            if needs_fix:
                print(f"Fixing Coin {coin_id}: '{raw_dates}'")
                print(f"  Current: {c_start} to {c_end}")
                print(f"  New:     {start} to {end}")
                
                if not dry_run:
                    stmt = update(Coin).where(Coin.id == coin_id).values(
                        reign_start=start,
                        reign_end=end
                    )
                    db.execute(stmt)
                fixed_count += 1
        
        if not dry_run:
            db.commit()
            print(f"Committed {fixed_count} changes.")
        else:
            print(f"Found {fixed_count} coins to fix.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true", help="Commit changes to DB")
    args = parser.parse_args()
    
    repair_bc_dates(dry_run=not args.commit)
