"""Orchestrator service for managing auction scrapers."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .base import AuctionScraperBase, LotData, ScrapeResult
from .adapters import HeritageAdapter, CNGAdapter, BiddrAdapter, EBayAdapter
from .simple_agora import AgoraScraper  # No rich version available
from app.models.auction_data import AuctionData

logger = logging.getLogger(__name__)


class ScrapeJob(BaseModel):
    """Represents a scrape job for tracking status."""
    
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    total_urls: int
    completed_urls: int = 0
    failed_urls: int = 0
    results: list[ScrapeResult] = []
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None


# In-memory job store (for simple BackgroundTask tracking)
_job_store: dict[str, ScrapeJob] = {}


class AuctionOrchestrator:
    """
    Orchestrates auction scraping across multiple platforms.
    
    Features:
    - URL detection: Routes URLs to correct scraper
    - Batch processing: Process multiple URLs with rate limiting
    - Error handling: Graceful failure with logging
    - Upsert logic: Create or update AuctionData records
    """
    
    # Rate limit: seconds between requests to same house
    RATE_LIMIT_SECONDS = 2.0
    
    def __init__(
        self,
        timeout: float = 30.0,
        user_agent: str | None = None,
        rate_limit: float | None = None,
    ):
        """Initialize orchestrator with scrapers."""
        self.timeout = timeout
        self.user_agent = user_agent
        self.rate_limit = rate_limit or self.RATE_LIMIT_SECONDS
        
        # Initialize scrapers (using rich scraper adapters where available)
        self._scrapers: list[AuctionScraperBase] = [
            HeritageAdapter(timeout=timeout, user_agent=user_agent),
            CNGAdapter(timeout=timeout, user_agent=user_agent),
            BiddrAdapter(timeout=timeout, user_agent=user_agent),
            EBayAdapter(timeout=timeout, user_agent=user_agent),
            AgoraScraper(timeout=timeout, user_agent=user_agent),  # No rich version
        ]
        
        # Track last request time per house for rate limiting
        self._last_request: dict[str, datetime] = {}
    
    def detect_house(self, url: str) -> str | None:
        """
        Detect which auction house a URL belongs to.
        
        Args:
            url: The auction URL
            
        Returns:
            House name or None if not detected
        """
        for scraper in self._scrapers:
            if scraper.detect_url(url):
                return scraper.HOUSE
        return None
    
    def get_scraper(self, url: str) -> AuctionScraperBase | None:
        """
        Get the appropriate scraper for a URL.
        
        Args:
            url: The auction URL
            
        Returns:
            Scraper instance or None if no match
        """
        for scraper in self._scrapers:
            if scraper.detect_url(url):
                return scraper
        return None
    
    async def _rate_limit(self, house: str) -> None:
        """Apply rate limiting for a specific house."""
        last = self._last_request.get(house)
        if last:
            elapsed = (datetime.utcnow() - last).total_seconds()
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)
        
        self._last_request[house] = datetime.utcnow()
    
    async def scrape_url(self, url: str) -> ScrapeResult:
        """
        Scrape a single URL.
        
        Args:
            url: The auction URL to scrape
            
        Returns:
            ScrapeResult with extracted data or error info
        """
        scraper = self.get_scraper(url)
        
        if not scraper:
            return ScrapeResult(
                status="error",
                url=url,
                error_message=f"No scraper found for URL: {url}",
            )
        
        # Apply rate limiting
        await self._rate_limit(scraper.HOUSE)
        
        # Scrape the page
        result = await scraper.extract_lot(url)
        
        return result
    
    async def scrape_batch(
        self,
        urls: list[str],
        job_id: str | None = None,
    ) -> list[ScrapeResult]:
        """
        Scrape multiple URLs with rate limiting.
        
        Args:
            urls: List of auction URLs to scrape
            job_id: Optional job ID for tracking
            
        Returns:
            List of ScrapeResults
        """
        results = []
        
        # Create or get job
        if job_id and job_id in _job_store:
            job = _job_store[job_id]
        elif job_id:
            job = ScrapeJob(
                job_id=job_id,
                status="processing",
                total_urls=len(urls),
                created_at=datetime.utcnow(),
            )
            _job_store[job_id] = job
        else:
            job = None
        
        for url in urls:
            try:
                result = await self.scrape_url(url)
                results.append(result)
                
                if job:
                    job.results.append(result)
                    if result.status in ("success", "partial"):
                        job.completed_urls += 1
                    else:
                        job.failed_urls += 1
                        
            except Exception as e:
                logger.exception(f"Error scraping {url}")
                error_result = ScrapeResult(
                    status="error",
                    url=url,
                    error_message=str(e),
                )
                results.append(error_result)
                
                if job:
                    job.results.append(error_result)
                    job.failed_urls += 1
        
        # Update job status
        if job:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
        
        return results
    
    def lot_data_to_auction_data(
        self,
        lot_data: LotData,
        coin_id: int | None = None,
        reference_type_id: int | None = None,
    ) -> dict:
        """
        Convert LotData to AuctionData dict for database insert/update.
        
        Maps ALL available fields from LotData to AuctionData columns.
        
        Args:
            lot_data: Extracted lot data
            coin_id: Optional coin ID to link
            reference_type_id: Optional reference type ID for comparables
            
        Returns:
            Dict suitable for AuctionData model
        """
        house = lot_data.house
        if lot_data.sub_house:
            house = f"{lot_data.house}/{lot_data.sub_house}"
        
        # Calculate die_axis_degrees from die_axis (hours)
        die_axis_degrees = None
        if lot_data.die_axis is not None:
            die_axis_degrees = (lot_data.die_axis * 30) % 360
        
        return {
            # ─────────────────────────────────────────────────────────────────
            # IDENTIFICATION
            # ─────────────────────────────────────────────────────────────────
            "coin_id": coin_id,
            "auction_house": house,
            "sub_house": lot_data.sub_house,
            "source_lot_id": lot_data.lot_id,
            "url": lot_data.url,
            
            # ─────────────────────────────────────────────────────────────────
            # AUCTION INFO
            # ─────────────────────────────────────────────────────────────────
            "sale_name": lot_data.sale_name,
            "lot_number": lot_data.lot_number,
            "auction_date": lot_data.auction_date,
            
            # ─────────────────────────────────────────────────────────────────
            # PRICING
            # ─────────────────────────────────────────────────────────────────
            "estimate_low": lot_data.estimate_low,
            "estimate_high": lot_data.estimate_high,
            "hammer_price": lot_data.hammer_price,
            "total_price": lot_data.total_price or lot_data.hammer_price,
            "buyers_premium_pct": lot_data.buyers_premium_pct,
            "currency": lot_data.currency,
            "sold": lot_data.sold,
            "bids": lot_data.bids,
            
            # ─────────────────────────────────────────────────────────────────
            # RULER & CLASSIFICATION
            # ─────────────────────────────────────────────────────────────────
            "ruler": lot_data.ruler,
            "ruler_title": lot_data.ruler_title,
            "reign_dates": lot_data.reign_dates,
            "denomination": lot_data.denomination,
            "metal": lot_data.metal,
            "mint": lot_data.mint,
            "struck_dates": lot_data.struck_dates,
            "struck_under": lot_data.struck_under,
            "categories": lot_data.categories if lot_data.categories else None,
            
            # ─────────────────────────────────────────────────────────────────
            # PHYSICAL MEASUREMENTS
            # ─────────────────────────────────────────────────────────────────
            "weight_g": lot_data.weight_g,
            "diameter_mm": lot_data.diameter_mm,
            "thickness_mm": lot_data.thickness_mm,
            "die_axis": lot_data.die_axis,
            "die_axis_degrees": die_axis_degrees,
            
            # ─────────────────────────────────────────────────────────────────
            # DESCRIPTIONS
            # ─────────────────────────────────────────────────────────────────
            "title": lot_data.title,
            "description": lot_data.description,
            "obverse_description": lot_data.obverse_description,
            "reverse_description": lot_data.reverse_description,
            "exergue": lot_data.exergue,
            
            # ─────────────────────────────────────────────────────────────────
            # CONDITION & GRADING
            # ─────────────────────────────────────────────────────────────────
            "grade": lot_data.grade,
            "grade_service": lot_data.grade_service,
            "certification_number": lot_data.certification_number,
            "condition_notes": lot_data.condition_notes,
            
            # ─────────────────────────────────────────────────────────────────
            # CATALOG REFERENCES
            # ─────────────────────────────────────────────────────────────────
            "catalog_references": lot_data.catalog_references if lot_data.catalog_references else None,
            "catalog_references_raw": lot_data.catalog_references_raw if lot_data.catalog_references_raw else None,
            "primary_reference": lot_data.primary_reference,
            "reference_type_id": reference_type_id,
            
            # ─────────────────────────────────────────────────────────────────
            # PROVENANCE
            # ─────────────────────────────────────────────────────────────────
            "provenance_text": lot_data.provenance_text,
            "pedigree_year": lot_data.pedigree_year,
            "has_provenance": lot_data.has_provenance,
            "provenance_entries": lot_data.provenance_entries,
            
            # ─────────────────────────────────────────────────────────────────
            # PHOTOS
            # ─────────────────────────────────────────────────────────────────
            "photos": lot_data.photos if lot_data.photos else None,
            "primary_photo_url": lot_data.primary_photo_url,
            
            # ─────────────────────────────────────────────────────────────────
            # EBAY-SPECIFIC
            # ─────────────────────────────────────────────────────────────────
            "seller_username": lot_data.seller_username,
            "seller_feedback_score": lot_data.seller_feedback_score,
            "seller_feedback_pct": lot_data.seller_feedback_pct,
            "seller_is_top_rated": lot_data.seller_is_top_rated,
            "seller_location": lot_data.seller_location,
            "listing_type": lot_data.listing_type,
            "shipping_cost": lot_data.shipping_cost,
            "watchers": lot_data.watchers,
            
            # ─────────────────────────────────────────────────────────────────
            # METADATA
            # ─────────────────────────────────────────────────────────────────
            "scraped_at": lot_data.fetched_at or datetime.utcnow(),
            "raw_data": lot_data.raw_data,
        }
    
    def upsert_auction_data(
        self,
        db: Session,
        lot_data: LotData,
        coin_id: int | None = None,
        reference_type_id: int | None = None,
    ) -> AuctionData:
        """
        Create or update AuctionData record from scraped lot data.
        
        Args:
            db: Database session
            lot_data: Extracted lot data
            coin_id: Optional coin ID to link
            reference_type_id: Optional reference type ID for comparables
            
        Returns:
            Created or updated AuctionData record
        """
        # Check if exists by URL
        existing = db.query(AuctionData).filter(AuctionData.url == lot_data.url).first()
        
        data_dict = self.lot_data_to_auction_data(
            lot_data,
            coin_id=coin_id,
            reference_type_id=reference_type_id,
        )
        
        if existing:
            # Update existing record
            for key, value in data_dict.items():
                if value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new record
            auction_data = AuctionData(**data_dict)
            db.add(auction_data)
            db.commit()
            db.refresh(auction_data)
            return auction_data


# Job management functions

def create_job(total_urls: int) -> ScrapeJob:
    """Create a new scrape job."""
    job = ScrapeJob(
        job_id=str(uuid.uuid4()),
        status="pending",
        total_urls=total_urls,
        created_at=datetime.utcnow(),
    )
    _job_store[job.job_id] = job
    return job


def get_job(job_id: str) -> ScrapeJob | None:
    """Get a scrape job by ID."""
    return _job_store.get(job_id)


def update_job(job_id: str, **kwargs) -> ScrapeJob | None:
    """Update a scrape job."""
    job = _job_store.get(job_id)
    if job:
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
    return job


def cleanup_old_jobs(max_age_hours: int = 24) -> int:
    """Remove jobs older than max_age_hours."""
    cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
    removed = 0
    
    for job_id in list(_job_store.keys()):
        job = _job_store[job_id]
        if job.created_at.timestamp() < cutoff:
            del _job_store[job_id]
            removed += 1
    
    return removed
