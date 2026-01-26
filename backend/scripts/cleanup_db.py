import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.orm import CoinModel
from src.infrastructure.repositories.vocab_repository import SqlAlchemyVocabRepository
from src.domain.vocab import VocabType

def cleanup_db(dry_run: bool = True):
    db: Session = SessionLocal()
    repo = SqlAlchemyVocabRepository(db)
    
    print(f"=== Database Cleanup (Dry Run: {dry_run}) ===")
    
    try:
        coins = db.query(CoinModel).all()
        print(f"Found {len(coins)} coins to scan.")
        
        changes = 0
        date_fixes = 0
        vocab_fixes = 0
        
        for coin in coins:
            coin_changed = False
            
            # 1. Fix Date Logic (Swap if start > end)
            if coin.year_start is not None and coin.year_end is not None:
                if coin.year_start > coin.year_end:
                    print(f"[Date] Coin #{coin.id}: Swapping {coin.year_start} -> {coin.year_end}")
                    if not dry_run:
                        coin.year_start, coin.year_end = coin.year_end, coin.year_start
                        coin_changed = True
                    date_fixes += 1

            # 2. Normalize Issuer
            if coin.issuer and not coin.issuer_term_id:
                res = repo.normalize(coin.issuer, VocabType.ISSUER)
                if res.success and not res.needs_review:
                    print(f"[Vocab] Coin #{coin.id}: Linking Issuer '{coin.issuer}' -> '{res.term.canonical_name}' (ID: {res.term.id})")
                    if not dry_run:
                        coin.issuer_term_id = res.term.id
                        # Optional: Update text to canonical? Maybe keep original for now.
                        # coin.issuer = res.term.canonical_name 
                        coin_changed = True
                    vocab_fixes += 1
            
            # 3. Normalize Mint
            if coin.mint and not coin.mint_term_id:
                res = repo.normalize(coin.mint, VocabType.MINT)
                if res.success and not res.needs_review:
                    print(f"[Vocab] Coin #{coin.id}: Linking Mint '{coin.mint}' -> '{res.term.canonical_name}' (ID: {res.term.id})")
                    if not dry_run:
                        coin.mint_term_id = res.term.id
                        coin_changed = True
                    vocab_fixes += 1

            if coin_changed:
                changes += 1
        
        print(f"\nSummary:")
        print(f"  Date Fixes: {date_fixes}")
        print(f"  Vocab Links: {vocab_fixes}")
        print(f"  Total Coins Modified: {changes}")
        
        if not dry_run:
            db.commit()
            print("Changes committed to database.")
        else:
            db.rollback()
            print("Dry run complete. No changes made.")
            
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
    
    cleanup_db(dry_run=not args.commit)
