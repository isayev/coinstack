import pytest
from src.domain.services.scraper_orchestrator import ScraperOrchestrator
from src.infrastructure.scrapers.mock_scraper import MockScraper

@pytest.mark.asyncio
async def test_orchestrator_routes_correctly():
    mock = MockScraper()
    orchestrator = ScraperOrchestrator([mock])
    
    # Supported URL
    result = await orchestrator.scrape("http://mock-auction.com/item/1")
    assert result is not None
    assert result.source == "MockAuction"
    assert result.lot_id == "12345"

@pytest.mark.asyncio
async def test_orchestrator_raises_on_unknown_url():
    mock = MockScraper()
    orchestrator = ScraperOrchestrator([mock])
    
    with pytest.raises(ValueError, match="No scraper found"):
        await orchestrator.scrape("http://unknown.com/item/1")
