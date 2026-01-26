"""Test the import endpoint directly."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_endpoint():
    from src.infrastructure.web.routers.import_v2 import import_from_url, UrlImportRequest
    from src.infrastructure.web.dependencies import get_db
    from src.domain.services.scraper_orchestrator import ScraperOrchestrator
    from src.infrastructure.scrapers.heritage.scraper import HeritageScraper
    from src.infrastructure.scrapers.cng.scraper import CNGScraper
    from src.infrastructure.scrapers.biddr.scraper import BiddrScraper
    from src.infrastructure.scrapers.ebay.scraper import EbayScraper
    from src.infrastructure.scrapers.agora.scraper import AgoraScraper
    
    # Create dependencies
    db = next(get_db())
    orchestrator = ScraperOrchestrator([
        HeritageScraper(),
        CNGScraper(),
        BiddrScraper(),
        EbayScraper(),
        AgoraScraper(),
    ])
    
    request = UrlImportRequest(url="https://www.ebay.com/itm/197805685775")
    
    try:
        result = await import_from_url(request, db, orchestrator)
        print(f"Success: {result.success}")
        if result.error:
            print(f"Error: {result.error}")
        if result.coin_data:
            print(f"Coin data: {result.coin_data.title}")
        return result.success
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    result = asyncio.run(test_endpoint())
    sys.exit(0 if result else 1)
