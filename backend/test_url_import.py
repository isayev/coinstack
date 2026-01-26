"""Test script for URL import endpoint."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.domain.services.scraper_orchestrator import ScraperOrchestrator
from src.infrastructure.scrapers.heritage.scraper import HeritageScraper
from src.infrastructure.scrapers.cng.scraper import CNGScraper
from src.infrastructure.scrapers.biddr.scraper import BiddrScraper
from src.infrastructure.scrapers.ebay.scraper import EbayScraper
from src.infrastructure.scrapers.agora.scraper import AgoraScraper


async def test_url_scrape(url: str):
    """Test URL scraping."""
    orchestrator = ScraperOrchestrator([
        HeritageScraper(),
        CNGScraper(),
        BiddrScraper(),
        EbayScraper(),
        AgoraScraper(),
    ])
    
    print(f"Testing URL scrape: {url}")
    print("-" * 50)
    
    try:
        result = await orchestrator.scrape(url)
        
        if not result:
            print("❌ Scrape returned None")
            return False
        
        print(f"✅ Success!")
        print(f"   Source: {result.source}")
        print(f"   Lot ID: {result.lot_id}")
        print(f"   Sale Name: {result.sale_name}")
        print(f"   Issuer: {result.issuer}")
        print(f"   Grade: {result.grade}")
        print(f"   Weight: {result.weight_g}g" if result.weight_g else "   Weight: N/A")
        print(f"   Diameter: {result.diameter_mm}mm" if result.diameter_mm else "   Diameter: N/A")
        print(f"   Hammer Price: ${result.hammer_price}" if result.hammer_price else "   Hammer Price: N/A")
        print(f"   Primary Image: {result.primary_image_url[:80] if result.primary_image_url else 'N/A'}...")
        print(f"   Additional Images: {len(result.additional_images or [])}")
        return True
        
    except ValueError as e:
        print(f"❌ Invalid URL or no scraper found: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup scrapers
        for scraper in orchestrator.scrapers:
            if hasattr(scraper, 'stop'):
                try:
                    await scraper.stop()
                except:
                    pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_url_import.py <url>")
        print("Example: python test_url_import.py https://www.ebay.com/itm/197805685775")
        sys.exit(1)
    
    url = sys.argv[1]
    result = asyncio.run(test_url_scrape(url))
    sys.exit(0 if result else 1)
