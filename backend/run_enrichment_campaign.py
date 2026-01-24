#!/usr/bin/env python
"""
Enrichment Campaign Script - Re-scrape auction URLs.

Processes auction URLs from CNG, Biddr, eBay, and Agora.
Skips Heritage (requires separate campaign with manual captcha solving).

Usage:
    python run_enrichment_campaign.py [--batch-size 50] [--delay 3] [--dry-run]
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from typing import Literal

from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

# Setup path for imports
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models.auction_data import AuctionData
from app.models.coin import Coin
from app.services.scrapers.orchestrator import AuctionOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# URL patterns for each auction house
AUCTION_PATTERNS = {
    "cng": ["cngcoins.com", "cng.com"],
    "biddr": ["biddr.com", "biddr.ch"],
    "ebay": ["ebay.com", "ebay.co.uk", "ebay.de"],
    "agora": ["agoraauctions.com", "agora-auctions"],
    "heritage": ["ha.com", "heritage"],  # For exclusion
}


def is_heritage_url(url: str) -> bool:
    """Check if URL is from Heritage (to be skipped)."""
    url_lower = url.lower()
    return any(p in url_lower for p in AUCTION_PATTERNS["heritage"])


def is_supported_url(url: str) -> bool:
    """Check if URL is from a supported (non-Heritage) auction house."""
    url_lower = url.lower()
    for house, patterns in AUCTION_PATTERNS.items():
        if house == "heritage":
            continue
        if any(p in url_lower for p in patterns):
            return True
    return False


def get_pending_urls_from_auction_data(db: Session) -> list[str]:
    """
    Get non-Heritage URLs from auction_data that need campaign processing.
    
    Returns URLs where:
    - campaign_scraped_at IS NULL (not yet processed)
    - NOT Heritage auction house
    """
    # Build exclusion filter for Heritage
    heritage_filter = or_(
        AuctionData.auction_house.ilike("%heritage%"),
        AuctionData.url.contains("ha.com")
    )
    
    records = db.query(AuctionData).filter(
        and_(
            AuctionData.campaign_scraped_at.is_(None),
            ~heritage_filter  # NOT Heritage
        )
    ).all()
    
    # Further filter to only supported URLs
    urls = [r.url for r in records if is_supported_url(r.url)]
    return urls


def get_pending_urls_from_coins(db: Session) -> list[str]:
    """
    Get non-Heritage acquisition URLs from coins table.
    
    Returns URLs that:
    - Are NOT Heritage URLs
    - Don't have AuctionData records yet OR have records not campaign-processed
    """
    coins = db.query(Coin).filter(
        Coin.acquisition_url.isnot(None)
    ).all()
    
    urls = []
    for coin in coins:
        url = coin.acquisition_url
        if not url:
            continue
        
        # Skip Heritage
        if is_heritage_url(url):
            continue
        
        # Skip unsupported URLs
        if not is_supported_url(url):
            continue
        
        # Check if already in AuctionData and campaign-processed
        existing = db.query(AuctionData).filter(
            AuctionData.url == url
        ).first()
        
        if existing and existing.campaign_scraped_at:
            continue
        
        urls.append(url)
    
    return urls


def get_all_pending_urls(db: Session) -> list[str]:
    """Get all non-Heritage URLs that need processing."""
    urls_from_auction = set(get_pending_urls_from_auction_data(db))
    urls_from_coins = set(get_pending_urls_from_coins(db))
    
    all_urls = urls_from_auction | urls_from_coins
    
    logger.info(f"Found {len(urls_from_auction)} URLs from auction_data")
    logger.info(f"Found {len(urls_from_coins)} URLs from coins")
    logger.info(f"Total unique URLs: {len(all_urls)}")
    
    return list(all_urls)


def categorize_urls(urls: list[str]) -> dict[str, list[str]]:
    """Categorize URLs by auction house."""
    categorized: dict[str, list[str]] = {
        "cng": [],
        "biddr": [],
        "ebay": [],
        "agora": [],
        "unknown": [],
    }
    
    for url in urls:
        url_lower = url.lower()
        matched = False
        
        for house, patterns in AUCTION_PATTERNS.items():
            if house == "heritage":
                continue
            if any(p in url_lower for p in patterns):
                categorized[house].append(url)
                matched = True
                break
        
        if not matched:
            categorized["unknown"].append(url)
    
    return categorized


async def process_url(
    db: Session,
    orchestrator: AuctionOrchestrator,
    url: str
) -> dict:
    """Process a single URL and update the database."""
    logger.info(f"Scraping: {url}")
    
    # Check existing record
    existing = db.query(AuctionData).filter(AuctionData.url == url).first()
    
    try:
        result = await orchestrator.scrape_url(url)
        now = datetime.utcnow()
        
        if result.status in ("success", "partial") and result.lot_data:
            lot_data = result.lot_data
            is_successful = True
            error_msg = None
            
            if existing:
                # Update existing record with scraped data
                data_dict = orchestrator.lot_data_to_auction_data(lot_data)
                for key, value in data_dict.items():
                    if value is not None and hasattr(existing, key):
                        setattr(existing, key, value)
                existing.campaign_scraped_at = now
                existing.campaign_successful = True
                existing.campaign_error = None
                existing.scraped_at = now
            else:
                # Create new record
                data_dict = orchestrator.lot_data_to_auction_data(lot_data)
                # Remove scraped_at if already in dict to avoid duplicate
                data_dict.pop('scraped_at', None)
                auction_data = AuctionData(
                    **data_dict,
                    scraped_at=now,
                    campaign_scraped_at=now,
                    campaign_successful=True,
                    campaign_error=None
                )
                db.add(auction_data)
            
            db.commit()
            logger.info(f"  ✓ Success: {lot_data.title[:60] if lot_data.title else 'No title'}...")
            
            return {
                "status": "success",
                "url": url,
                "title": lot_data.title,
            }
        else:
            # Error or no data
            error_msg = result.error_message or "No data extracted"
            
            if existing:
                existing.campaign_scraped_at = now
                existing.campaign_successful = False
                existing.campaign_error = error_msg[:500]
                db.commit()
            
            logger.warning(f"  ✗ Failed: {error_msg}")
            
            return {
                "status": "error",
                "url": url,
                "error": error_msg,
            }
            
    except Exception as e:
        logger.error(f"  ✗ Exception: {e}")
        
        if existing:
            existing.campaign_scraped_at = datetime.utcnow()
            existing.campaign_successful = False
            existing.campaign_error = str(e)[:500]
            db.commit()
        
        return {
            "status": "error",
            "url": url,
            "error": str(e),
        }


async def run_campaign(
    batch_size: int = 50,
    delay_seconds: float = 3.0,
    dry_run: bool = False,
    houses: list[str] | None = None,
):
    """
    Run the enrichment campaign.
    
    Args:
        batch_size: Maximum URLs to process
        delay_seconds: Delay between requests (per house)
        dry_run: If True, just show what would be done
        houses: List of houses to process (None = all)
    """
    db = SessionLocal()
    
    try:
        # Get all pending URLs
        all_urls = get_all_pending_urls(db)
        
        if not all_urls:
            logger.info("No pending URLs to process!")
            return
        
        # Categorize by house
        categorized = categorize_urls(all_urls)
        
        # Print summary
        print("\n" + "=" * 60)
        print("ENRICHMENT CAMPAIGN - Non-Heritage Auction URLs")
        print("=" * 60)
        print(f"\nPending URLs by auction house:")
        for house, urls in categorized.items():
            if urls:
                print(f"  {house.upper()}: {len(urls)} URLs")
        print()
        
        # Filter to selected houses
        if houses:
            houses_lower = [h.lower() for h in houses]
            urls_to_process = []
            for house, urls in categorized.items():
                if house in houses_lower:
                    urls_to_process.extend(urls)
        else:
            # All non-Heritage houses
            urls_to_process = []
            for house, urls in categorized.items():
                if house != "unknown":
                    urls_to_process.extend(urls)
        
        # Limit to batch size
        urls_to_process = urls_to_process[:batch_size]
        
        print(f"Will process {len(urls_to_process)} URLs (batch_size={batch_size})")
        print(f"Delay between requests: {delay_seconds}s")
        print()
        
        if dry_run:
            print("DRY RUN - URLs that would be processed:")
            for i, url in enumerate(urls_to_process[:20], 1):
                print(f"  {i}. {url}")
            if len(urls_to_process) > 20:
                print(f"  ... and {len(urls_to_process) - 20} more")
            return
        
        # Initialize orchestrator
        orchestrator = AuctionOrchestrator(
            timeout=30.0,
            rate_limit=delay_seconds,
        )
        
        # Process URLs
        results = {
            "success": 0,
            "error": 0,
            "total": len(urls_to_process),
        }
        
        for i, url in enumerate(urls_to_process, 1):
            print(f"\n[{i}/{len(urls_to_process)}] Processing...")
            
            result = await process_url(db, orchestrator, url)
            
            if result["status"] == "success":
                results["success"] += 1
            else:
                results["error"] += 1
            
            # Delay between requests (orchestrator handles per-house rate limiting)
            if i < len(urls_to_process):
                await asyncio.sleep(delay_seconds)
        
        # Final summary
        print("\n" + "=" * 60)
        print("CAMPAIGN COMPLETE")
        print("=" * 60)
        print(f"Total processed: {results['total']}")
        print(f"Successful: {results['success']}")
        print(f"Errors: {results['error']}")
        print()
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Run enrichment campaign for non-Heritage auction URLs"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=50,
        help="Maximum number of URLs to process (default: 50)"
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=3.0,
        help="Delay between requests in seconds (default: 3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually scraping"
    )
    parser.add_argument(
        "--houses",
        nargs="+",
        choices=["cng", "biddr", "ebay", "agora"],
        help="Only process specific auction houses"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_campaign(
        batch_size=args.batch_size,
        delay_seconds=args.delay,
        dry_run=args.dry_run,
        houses=args.houses,
    ))


if __name__ == "__main__":
    main()
