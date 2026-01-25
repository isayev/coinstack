"""
Heritage Data Enrichment Campaign Service.

Processes Heritage auction URLs one at a time with visible browser
for manual captcha solving. Tracks processing status to prevent duplicates.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.auction_data import AuctionData
from app.models.coin import Coin
from app.services.scrapers.browser_scraper import BrowserConfig, scrape_heritage

logger = logging.getLogger(__name__)


@dataclass
class CampaignConfig:
    """Configuration for enrichment campaign."""
    delay_between_urls: float = 30.0  # Seconds between URLs
    captcha_wait_time: float = 45.0   # Time to wait for captcha solving
    headless: bool = False            # Visible browser for captcha
    slow_mo: int = 500                # Slow down browser actions (ms)
    batch_size: int = 10              # How many to process in one run
    

@dataclass
class CampaignStatus:
    """Current campaign status."""
    total_urls: int
    processed: int
    pending: int
    successful: int
    errors: int
    is_running: bool = False
    current_url: Optional[str] = None


class HeritageEnrichmentCampaign:
    """
    Manages Heritage data enrichment campaign.
    
    Processes URLs slowly with visible browser for manual captcha solving.
    Tracks processing status in database to prevent duplicates.
    """
    
    _instance = None
    _is_running = False
    _current_url: Optional[str] = None
    
    def __new__(cls):
        """Singleton pattern to prevent multiple campaigns running."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.config = CampaignConfig()
    
    @classmethod
    def is_running(cls) -> bool:
        """Check if campaign is currently running."""
        return cls._is_running
    
    @classmethod
    def get_current_url(cls) -> Optional[str]:
        """Get the URL currently being processed."""
        return cls._current_url
    
    def get_heritage_urls_from_coins(self, db: Session) -> List[str]:
        """
        Get Heritage acquisition URLs from coins table.
        
        Returns URLs that:
        - Are Heritage URLs (contain 'ha.com' or 'heritage')
        - Don't have AuctionData records yet OR have records not campaign-processed
        """
        # Get all coins with Heritage acquisition URLs
        coins = db.query(Coin).filter(
            Coin.acquisition_url.isnot(None),
            or_(
                Coin.acquisition_url.contains('ha.com'),
                Coin.acquisition_url.contains('heritage')
            )
        ).all()
        
        urls = []
        for coin in coins:
            url = coin.acquisition_url
            if not url:
                continue
                
            # Check if already in AuctionData and campaign-processed
            existing = db.query(AuctionData).filter(
                AuctionData.url == url
            ).first()
            
            if existing and existing.campaign_scraped_at:
                # Already processed by campaign
                continue
            
            urls.append(url)
        
        return urls
    
    def get_heritage_urls_from_auction_data(self, db: Session) -> List[str]:
        """
        Get Heritage URLs from auction_data table that need campaign processing.
        
        Returns URLs that:
        - Are Heritage auction house
        - Have not been campaign-processed (campaign_scraped_at IS NULL)
        """
        records = db.query(AuctionData).filter(
            and_(
                or_(
                    AuctionData.auction_house.ilike('%heritage%'),
                    AuctionData.url.contains('ha.com')
                ),
                AuctionData.campaign_scraped_at.is_(None)
            )
        ).all()
        
        return [r.url for r in records]
    
    def get_all_pending_urls(self, db: Session) -> List[str]:
        """
        Get all Heritage URLs that need processing.
        
        Combines URLs from:
        1. Coin.acquisition_url (new URLs)
        2. AuctionData.url (existing records needing enrichment)
        
        Deduplicates and filters already-processed.
        """
        urls_from_coins = set(self.get_heritage_urls_from_coins(db))
        urls_from_auction = set(self.get_heritage_urls_from_auction_data(db))
        
        all_urls = urls_from_coins | urls_from_auction
        
        logger.info(f"Found {len(urls_from_coins)} URLs from coins, "
                   f"{len(urls_from_auction)} from auction_data, "
                   f"{len(all_urls)} unique total")
        
        return list(all_urls)
    
    def get_status(self, db: Session) -> CampaignStatus:
        """Get current campaign status."""
        # Total Heritage URLs
        total_from_auction = db.query(AuctionData).filter(
            or_(
                AuctionData.auction_house.ilike('%heritage%'),
                AuctionData.url.contains('ha.com')
            )
        ).count()
        
        # Processed (campaign_scraped_at is set)
        processed = db.query(AuctionData).filter(
            and_(
                or_(
                    AuctionData.auction_house.ilike('%heritage%'),
                    AuctionData.url.contains('ha.com')
                ),
                AuctionData.campaign_scraped_at.isnot(None)
            )
        ).count()
        
        # Successful
        successful = db.query(AuctionData).filter(
            and_(
                or_(
                    AuctionData.auction_house.ilike('%heritage%'),
                    AuctionData.url.contains('ha.com')
                ),
                AuctionData.campaign_successful == True
            )
        ).count()
        
        # Errors
        errors = db.query(AuctionData).filter(
            and_(
                or_(
                    AuctionData.auction_house.ilike('%heritage%'),
                    AuctionData.url.contains('ha.com')
                ),
                AuctionData.campaign_scraped_at.isnot(None),
                AuctionData.campaign_successful == False
            )
        ).count()
        
        # Pending includes coin acquisition URLs not yet in auction_data
        pending_urls = self.get_all_pending_urls(db)
        
        return CampaignStatus(
            total_urls=total_from_auction + len(pending_urls),
            processed=processed,
            pending=len(pending_urls),
            successful=successful,
            errors=errors,
            is_running=self._is_running,
            current_url=self._current_url
        )
    
    async def process_single_url(
        self, 
        db: Session, 
        url: str,
        wait_for_captcha: float = 45.0
    ) -> Dict[str, Any]:
        """
        Process a single Heritage URL.
        
        Args:
            db: Database session
            url: Heritage auction URL
            wait_for_captcha: Seconds to wait for manual captcha solving
            
        Returns:
            Scraped data dictionary
        """
        logger.info(f"Processing Heritage URL: {url}")
        self._current_url = url
        
        # Mark as being processed (prevents duplicate runs)
        existing = db.query(AuctionData).filter(AuctionData.url == url).first()
        
        if existing and existing.campaign_scraped_at:
            logger.warning(f"URL already processed by campaign: {url}")
            return {
                'status': 'skipped',
                'reason': 'already_processed',
                'url': url,
                'campaign_scraped_at': existing.campaign_scraped_at.isoformat()
            }
        
        # Configure browser for manual captcha solving
        config = BrowserConfig(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
            min_delay=5.0,  # Longer delays for Heritage
            max_delay=10.0,
            timeout=60000  # 60s timeout
        )
        
        try:
            # Run scraper with captcha wait time
            logger.info(f"Scraping with {wait_for_captcha}s captcha wait time...")
            
            # Run scraper - captcha_wait tells it how long to wait for manual solving
            data = await scrape_heritage(url, config, captcha_wait=wait_for_captcha)
            
            # Determine if scrape was successful (got real data, not just URL slug)
            is_successful = bool(
                data.get('title') and 
                not data.get('_error') and
                data.get('status') != 'error'
            )
            
            # Update or create AuctionData record
            now = datetime.utcnow()
            
            if existing:
                # Update existing record
                for key, value in data.items():
                    if value is not None and hasattr(existing, key):
                        setattr(existing, key, value)
                existing.campaign_scraped_at = now
                existing.campaign_successful = is_successful
                existing.campaign_error = data.get('_error') or data.get('error')
            else:
                # Create new record
                auction_data = AuctionData(
                    url=url,
                    auction_house=data.get('auction_house', 'Heritage Auctions'),
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
                    grade_service=data.get('grade_service'),
                    lot_number=data.get('lot_number'),
                    hammer_price=data.get('hammer_price'),
                    photos=data.get('photos'),
                    primary_photo_url=data.get('primary_photo_url'),
                    obverse_description=data.get('obverse_description'),
                    reverse_description=data.get('reverse_description'),
                    description=data.get('description'),
                    condition_notes=data.get('condition_notes'),
                    provenance_text=data.get('provenance'),
                    raw_data=data,
                    scraped_at=now,
                    campaign_scraped_at=now,
                    campaign_successful=is_successful,
                    campaign_error=data.get('_error') or data.get('error')
                )
                db.add(auction_data)
            
            db.commit()
            
            logger.info(f"Processed {url} - successful: {is_successful}")
            
            return {
                'status': 'success' if is_successful else 'partial',
                'url': url,
                'campaign_successful': is_successful,
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            
            # Record the error
            if existing:
                existing.campaign_scraped_at = datetime.utcnow()
                existing.campaign_successful = False
                existing.campaign_error = str(e)[:500]
                db.commit()
            
            return {
                'status': 'error',
                'url': url,
                'error': str(e)
            }
        finally:
            self._current_url = None
    
    async def run_campaign(
        self,
        db: Session,
        batch_size: Optional[int] = None,
        delay_between: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Run the enrichment campaign.
        
        Args:
            db: Database session
            batch_size: Number of URLs to process (default: config.batch_size)
            delay_between: Seconds between URLs (default: config.delay_between_urls)
            
        Returns:
            Campaign results summary
        """
        if self._is_running:
            return {
                'status': 'error',
                'error': 'Campaign is already running',
                'current_url': self._current_url
            }
        
        batch_size = batch_size or self.config.batch_size
        delay_between = delay_between or self.config.delay_between_urls
        
        self._is_running = True
        
        try:
            # Get pending URLs
            pending_urls = self.get_all_pending_urls(db)
            
            if not pending_urls:
                return {
                    'status': 'complete',
                    'message': 'No pending URLs to process',
                    'processed': 0
                }
            
            # Limit to batch size
            urls_to_process = pending_urls[:batch_size]
            
            logger.info(f"Starting campaign: {len(urls_to_process)} URLs "
                       f"(of {len(pending_urls)} pending)")
            
            results = []
            successful = 0
            errors = 0
            
            for i, url in enumerate(urls_to_process):
                logger.info(f"Processing {i+1}/{len(urls_to_process)}: {url}")
                
                result = await self.process_single_url(
                    db, url, 
                    wait_for_captcha=self.config.captcha_wait_time
                )
                results.append(result)
                
                if result.get('status') == 'success':
                    successful += 1
                elif result.get('status') == 'error':
                    errors += 1
                
                # Wait between URLs (unless last one)
                if i < len(urls_to_process) - 1:
                    logger.info(f"Waiting {delay_between}s before next URL...")
                    await asyncio.sleep(delay_between)
            
            return {
                'status': 'complete',
                'total_processed': len(results),
                'successful': successful,
                'errors': errors,
                'remaining': len(pending_urls) - len(urls_to_process),
                'results': results
            }
            
        finally:
            self._is_running = False
            self._current_url = None


# Singleton instance
campaign = HeritageEnrichmentCampaign()


def get_campaign() -> HeritageEnrichmentCampaign:
    """Get the campaign singleton instance."""
    return campaign
