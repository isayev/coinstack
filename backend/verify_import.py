import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Coin

db = SessionLocal()
try:
    # Check BC dates
    print("=== BC Dates (should be negative) ===")
    bc_coins = db.query(Coin).filter(Coin.mint_year_start < 0).order_by(Coin.mint_year_start).all()
    for coin in bc_coins:
        print(f"  {coin.issuing_authority}: {coin.mint_year_start} to {coin.mint_year_end}")
    
    # Check Greek text preserved
    print("\n=== Greek Text Samples ===")
    coins_with_greek = db.query(Coin).filter(Coin.obverse_legend.like('%Σ%')).limit(3).all()
    for coin in coins_with_greek:
        print(f"  {coin.issuing_authority}: {coin.obverse_legend[:50] if coin.obverse_legend else 'N/A'}...")
    
    # Check bullets preserved
    print("\n=== Bullet Samples ===")
    coins_with_bullets = db.query(Coin).filter(Coin.obverse_legend.like('%•%')).limit(3).all()
    for coin in coins_with_bullets:
        print(f"  {coin.issuing_authority}: {coin.obverse_legend[:50] if coin.obverse_legend else 'N/A'}...")
    
    # Check Æ preserved in denomination
    print("\n=== Æ Denomination Samples ===")
    ae_coins = db.query(Coin).filter(Coin.denomination.like('%Æ%')).limit(3).all()
    for coin in ae_coins:
        print(f"  {coin.issuing_authority}: {coin.denomination}")
    
    # Check no NBSP or en-dash in key fields
    print("\n=== Checking for remaining problematic characters ===")
    problem_found = False
    all_coins = db.query(Coin).all()
    for coin in all_coins:
        for field in ['issuing_authority', 'denomination', 'obverse_legend', 'reverse_legend']:
            value = getattr(coin, field)
            if value:
                if '\xa0' in value:
                    print(f"  NBSP found in {field}: {value[:40]}")
                    problem_found = True
                if '\u2013' in value:
                    print(f"  En-dash found in {field}: {value[:40]}")
                    problem_found = True
    if not problem_found:
        print("  None found - all normalized correctly!")
    
    print(f"\n=== Total: {db.query(Coin).count()} coins ===")
finally:
    db.close()
