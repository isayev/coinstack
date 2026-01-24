"""
Batch processor for CNG, Biddr, and eBay auction URLs.

These venues are easier than Heritage - no captcha, can run headless.
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy import or_

from app.database import SessionLocal
from app.models.coin import Coin
from app.models.auction_data import AuctionData
from app.services.scrapers.browser_scraper import (
    BrowserConfig, 
    scrape_cng, 
    scrape_biddr, 
    scrape_ebay,
    scrape_auction_url
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rate limiting delays per venue
DELAYS = {
    'cng': 3.0,
    'biddr': 2.0,
    'ebay': 5.0,  # eBay needs more time
}

# Which venues to process (set to empty list for all, or specific ones)
ONLY_VENUES = ['ebay']  # Only process eBay this run


def get_urls_by_venue(db):
    """Get all acquisition URLs grouped by venue."""
    coins = db.query(Coin).filter(Coin.acquisition_url.isnot(None)).all()
    
    venues = {'cng': [], 'biddr': [], 'ebay': []}
    
    for coin in coins:
        url = coin.acquisition_url
        url_lower = url.lower()
        
        # Skip if already has AuctionData with campaign_scraped_at
        existing = db.query(AuctionData).filter(
            AuctionData.url == url,
            AuctionData.campaign_scraped_at.isnot(None)
        ).first()
        
        if existing:
            continue
        
        if 'cng' in url_lower:
            venues['cng'].append((coin.id, url))
        elif 'biddr' in url_lower:
            venues['biddr'].append((coin.id, url))
        elif 'ebay' in url_lower:
            venues['ebay'].append((coin.id, url))
    
    return venues


async def process_url(db, coin_id: int, url: str, venue: str) -> dict:
    """Process a single URL."""
    logger.info(f"Processing {venue.upper()}: {url[:80]}...")
    
    config = BrowserConfig(
        headless=True,
        min_delay=2.0,
        max_delay=4.0,
        timeout=45000
    )
    
    try:
        # Use the generic dispatcher which routes to correct scraper
        data = await scrape_auction_url(url, config)
        
        is_successful = bool(
            data.get('title') and 
            not data.get('_error') and
            data.get('status') != 'error'
        )
        
        now = datetime.utcnow()
        
        # Check if AuctionData exists
        existing = db.query(AuctionData).filter(AuctionData.url == url).first()
        
        if existing:
            # Update existing - only set specific fields, not raw data that might have string dates
            existing.title = data.get('title') or existing.title
            existing.ruler = data.get('ruler') or existing.ruler
            existing.reign_dates = data.get('reign_dates') or existing.reign_dates
            existing.denomination = data.get('denomination') or existing.denomination
            existing.metal = data.get('metal') or existing.metal
            existing.mint = data.get('mint') or existing.mint
            existing.grade = data.get('grade') or existing.grade
            existing.obverse_description = data.get('obverse_description') or existing.obverse_description
            existing.reverse_description = data.get('reverse_description') or existing.reverse_description
            existing.description = data.get('description') or existing.description
            existing.photos = data.get('photos') or existing.photos
            existing.primary_photo_url = data.get('primary_photo_url') or existing.primary_photo_url
            existing.hammer_price = data.get('hammer_price') or existing.hammer_price
            if data.get('weight_g'):
                existing.weight_g = data.get('weight_g')
            if data.get('diameter_mm'):
                existing.diameter_mm = data.get('diameter_mm')
            if data.get('die_axis'):
                existing.die_axis = data.get('die_axis')
            existing.raw_data = data
            existing.campaign_scraped_at = now
            existing.campaign_successful = is_successful
            existing.campaign_error = data.get('_error') or data.get('error')
            existing.coin_id = coin_id
        else:
            # Create new
            auction_house = data.get('auction_house')
            if not auction_house:
                if 'cng' in url.lower():
                    auction_house = 'CNG'
                elif 'biddr' in url.lower():
                    auction_house = 'Biddr'
                elif 'ebay' in url.lower():
                    auction_house = 'eBay'
            
            auction_data = AuctionData(
                url=url,
                coin_id=coin_id,
                auction_house=auction_house or venue.upper(),
                title=data.get('title'),
                ruler=data.get('ruler'),
                reign_dates=data.get('reign_dates'),
                denomination=data.get('denomination'),
                metal=data.get('metal'),
                mint=data.get('mint'),
                weight_g=data.get('weight_g'),
                diameter_mm=data.get('diameter_mm'),
                die_axis=data.get('die_axis'),
                grade=data.get('grade'),
                lot_number=data.get('lot_number'),
                hammer_price=data.get('hammer_price'),
                photos=data.get('photos'),
                primary_photo_url=data.get('primary_photo_url'),
                obverse_description=data.get('obverse_description'),
                reverse_description=data.get('reverse_description'),
                description=data.get('description'),
                raw_data=data,
                scraped_at=now,
                campaign_scraped_at=now,
                campaign_successful=is_successful,
                campaign_error=data.get('_error') or data.get('error')
            )
            db.add(auction_data)
        
        db.commit()
        
        status = 'SUCCESS' if is_successful else 'PARTIAL'
        logger.info(f"  [{status}] {data.get('title', 'No title')[:60]}")
        
        return {'status': 'success' if is_successful else 'partial', 'url': url}
        
    except Exception as e:
        logger.error(f"  [ERROR] {e}")
        
        # Record error
        existing = db.query(AuctionData).filter(AuctionData.url == url).first()
        if existing:
            existing.campaign_scraped_at = datetime.utcnow()
            existing.campaign_successful = False
            existing.campaign_error = str(e)[:500]
            db.commit()
        
        return {'status': 'error', 'url': url, 'error': str(e)}


async def main():
    db = SessionLocal()
    
    try:
        venues = get_urls_by_venue(db)
        
        print("\n" + "="*60)
        print("BATCH PROCESSING - CNG, Biddr, eBay")
        print("="*60)
        print(f"CNG:   {len(venues['cng'])} URLs")
        print(f"Biddr: {len(venues['biddr'])} URLs")
        print(f"eBay:  {len(venues['ebay'])} URLs")
        print("="*60 + "\n")
        
        results = {'success': 0, 'partial': 0, 'error': 0}
        
        # Process each venue
        venues_to_process = ONLY_VENUES if ONLY_VENUES else ['cng', 'biddr', 'ebay']
        for venue in venues_to_process:
            urls = venues[venue]
            if not urls:
                continue
                
            print(f"\n--- Processing {venue.upper()} ({len(urls)} URLs) ---\n")
            
            for i, (coin_id, url) in enumerate(urls):
                print(f"[{i+1}/{len(urls)}] ", end="")
                
                result = await process_url(db, coin_id, url, venue)
                results[result['status']] = results.get(result['status'], 0) + 1
                
                # Rate limit
                if i < len(urls) - 1:
                    delay = DELAYS.get(venue, 3.0)
                    await asyncio.sleep(delay)
        
        print("\n" + "="*60)
        print("COMPLETE")
        print("="*60)
        print(f"Success: {results.get('success', 0)}")
        print(f"Partial: {results.get('partial', 0)}")
        print(f"Errors:  {results.get('error', 0)}")
        print("="*60 + "\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
