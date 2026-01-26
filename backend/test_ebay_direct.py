"""Direct test of eBay scraper."""
import asyncio
import sys
sys.path.insert(0, '.')

from src.infrastructure.scrapers.ebay.scraper import EbayScraper

async def test_ebay():
    scraper = EbayScraper(headless=True)
    print("Testing eBay scraper with URL: https://www.ebay.com/itm/197805685775")
    
    result = await scraper.scrape('https://www.ebay.com/itm/197805685775')
    
    print(f"\n=== RESULT ===")
    print(f"Success: {result is not None}")
    
    if result:
        print(f"Source: {result.source}")
        print(f"Lot ID: {result.lot_id}")
        print(f"Issuer: {result.issuer}")
        print(f"Description: {result.description[:100] if result.description else 'None'}...")
        print(f"Price: {result.hammer_price}")
    else:
        print("Scraper returned None")
    
    await scraper.stop()
    return result

if __name__ == "__main__":
    result = asyncio.run(test_ebay())
    sys.exit(0 if result else 1)
