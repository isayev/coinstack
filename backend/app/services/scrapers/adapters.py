"""
Adapter classes to bridge rich scrapers to the AuctionScraperBase interface.

Rich scrapers use Playwright and have their own data models. These adapters
provide a unified interface for the orchestrator and map ALL available fields
to capture complete metadata.
"""

import logging
from datetime import datetime
from typing import Optional

from .base import AuctionScraperBase, LotData, ScrapeResult

logger = logging.getLogger(__name__)


class CNGAdapter(AuctionScraperBase):
    """Adapter for CNG rich scraper."""
    
    HOUSE = "CNG"
    BASE_URL = "https://auctions.cngcoins.com"
    URL_PATTERNS = ["cngcoins.com", "cng"]
    
    def __init__(self, timeout: float | None = None, user_agent: str | None = None):
        super().__init__(timeout, user_agent)
        self._scraper = None
    
    def parse_lot_id(self, url: str) -> str | None:
        import re
        match = re.search(r'/lots/view/([^/?]+)', url)
        if match:
            return match.group(1)
        match = re.search(r'CoinID=(\d+)', url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    async def extract_lot(self, url: str) -> ScrapeResult:
        from .cng import CNGScraper
        
        start_time = datetime.utcnow()
        
        try:
            async with CNGScraper(headless=True) as scraper:
                coin_data = await scraper.scrape_url(url)
                
                if not coin_data:
                    return ScrapeResult(
                        status="not_found",
                        url=url,
                        house=self.HOUSE,
                        error_message="No data returned",
                    )
                
                # Extract auction info (may be None)
                auction = coin_data.auction
                physical = coin_data.physical
                provenance = coin_data.provenance
                
                # Extract closing date for auction_date
                auction_date = None
                closing_date = None
                if auction and auction.closing_date:
                    closing_date = auction.closing_date
                    auction_date = auction.closing_date.date()
                
                # Extract references
                catalog_refs = []
                catalog_refs_raw = []
                if coin_data.references:
                    catalog_refs = [ref.normalized for ref in coin_data.references]
                    catalog_refs_raw = [ref.raw_text for ref in coin_data.references]
                
                # Extract provenance entries
                prov_entries = None
                if provenance and provenance.entries:
                    prov_entries = [
                        {
                            "source_type": e.source_type,
                            "source_name": e.source_name,
                            "date": e.date,
                            "lot_number": e.lot_number,
                            "raw_text": e.raw_text,
                        }
                        for e in provenance.entries
                    ]
                
                # Convert CNGCoinData to LotData with ALL fields
                lot_data = LotData(
                    # Identification
                    lot_id=coin_data.cng_lot_id or self.parse_lot_id(url) or url,
                    house=self.HOUSE,
                    url=coin_data.url or url,
                    
                    # Pricing
                    hammer_price=float(auction.sold_price_usd) if auction and auction.sold_price_usd else None,
                    estimate_low=float(auction.estimate_usd) if auction and auction.estimate_usd else None,
                    total_price=float(coin_data.total_price_usd) if coin_data.total_price_usd else None,
                    currency="USD",
                    sold=auction.is_sold if auction else True,
                    bids=auction.bids if auction else None,
                    buyers_premium_pct=auction.buyers_premium_pct if auction else None,
                    
                    # Auction info
                    sale_name=auction.auction_name if auction else None,
                    lot_number=str(auction.lot_number) if auction and auction.lot_number else None,
                    auction_date=auction_date,
                    closing_date=closing_date,
                    
                    # Ruler & Classification
                    ruler=coin_data.ruler,
                    ruler_title=coin_data.ruler_title,
                    reign_dates=coin_data.reign_dates,
                    
                    # Coin type
                    denomination=coin_data.denomination,
                    metal=coin_data.metal.value if coin_data.metal else None,
                    mint=coin_data.mint,
                    struck_dates=coin_data.struck_dates,
                    struck_under=coin_data.struck_under,
                    
                    # Physical
                    weight_g=float(physical.weight_g) if physical and physical.weight_g else None,
                    diameter_mm=float(physical.diameter_mm) if physical and physical.diameter_mm else None,
                    die_axis=physical.die_axis_hours if physical else None,
                    
                    # Descriptions
                    title=coin_data.title,
                    description=coin_data.raw_description,
                    obverse_description=coin_data.obverse_description,
                    reverse_description=coin_data.reverse_description,
                    
                    # Grading
                    grade=coin_data.grade,
                    condition_notes=coin_data.condition_notes,
                    
                    # References
                    catalog_references=catalog_refs,
                    catalog_references_raw=catalog_refs_raw,
                    primary_reference=coin_data.primary_reference,
                    
                    # Provenance
                    provenance_text=provenance.raw_text if provenance else None,
                    pedigree_year=provenance.pedigree_year if provenance else None,
                    has_provenance=coin_data.has_provenance,
                    provenance_entries=prov_entries,
                    
                    # Photos
                    photos=[img.url for img in coin_data.images] if coin_data.images else [],
                    primary_photo_url=coin_data.images[0].url if coin_data.images else None,
                    
                    # Categories
                    categories=coin_data.categories or [],
                    
                    # Metadata
                    fetched_at=datetime.utcnow(),
                )
                
                elapsed = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return ScrapeResult(
                    status="success",
                    url=url,
                    house=self.HOUSE,
                    lot_data=lot_data,
                    elapsed_ms=elapsed,
                )
                
        except Exception as e:
            logger.exception(f"CNG scrape error for {url}")
            return ScrapeResult(
                status="error",
                url=url,
                house=self.HOUSE,
                error_message=str(e),
            )


class BiddrAdapter(AuctionScraperBase):
    """Adapter for Biddr rich scraper."""
    
    HOUSE = "Biddr"
    BASE_URL = "https://www.biddr.com"
    URL_PATTERNS = ["biddr.com", "biddr.ch"]
    
    def __init__(self, timeout: float | None = None, user_agent: str | None = None):
        super().__init__(timeout, user_agent)
    
    def parse_lot_id(self, url: str) -> str | None:
        import re
        match = re.search(r'[?&]l=(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    async def extract_lot(self, url: str) -> ScrapeResult:
        from .biddr import BiddrScraper
        
        start_time = datetime.utcnow()
        
        try:
            async with BiddrScraper(headless=True) as scraper:
                coin_data = await scraper.scrape_url(url)
                
                if not coin_data:
                    return ScrapeResult(
                        status="not_found",
                        url=url,
                        house=self.HOUSE,
                        error_message="No data returned",
                    )
                
                # Extract nested data
                auction = coin_data.auction
                physical = coin_data.physical
                provenance = coin_data.provenance
                
                # Extract closing date for auction_date
                auction_date = None
                closing_date = None
                if auction and auction.closing_date:
                    closing_date = auction.closing_date
                    auction_date = auction.closing_date.date()
                
                # Extract references
                catalog_refs = []
                catalog_refs_raw = []
                if coin_data.references:
                    catalog_refs = [ref.normalized for ref in coin_data.references]
                    catalog_refs_raw = [ref.raw_text for ref in coin_data.references]
                
                # Extract provenance entries
                prov_entries = None
                if provenance and provenance.entries:
                    prov_entries = [
                        {
                            "source_type": e.source_type,
                            "source_name": e.source_name,
                            "date": e.date,
                            "lot_number": e.lot_number,
                            "raw_text": e.raw_text,
                        }
                        for e in provenance.entries
                    ]
                
                # Convert BiddrCoinData to LotData with ALL fields
                lot_data = LotData(
                    # Identification
                    lot_id=coin_data.biddr_lot_id or self.parse_lot_id(url) or url,
                    house=self.HOUSE,
                    sub_house=coin_data.sub_house.value if coin_data.sub_house else None,
                    url=coin_data.url or url,
                    
                    # Pricing
                    hammer_price=float(auction.hammer_price) if auction and auction.hammer_price else None,
                    estimate_low=float(auction.estimate_low) if auction and auction.estimate_low else None,
                    estimate_high=float(auction.estimate_high) if auction and auction.estimate_high else None,
                    total_price=float(coin_data.total_price) if coin_data.total_price else None,
                    currency=auction.currency if auction else "EUR",
                    sold=auction.is_sold if auction else True,
                    bids=auction.bids if auction else None,
                    buyers_premium_pct=auction.buyers_premium_pct if auction else None,
                    
                    # Auction info
                    sale_name=auction.auction_name if auction else None,
                    lot_number=str(auction.lot_number) if auction and auction.lot_number else None,
                    auction_date=auction_date,
                    closing_date=closing_date,
                    
                    # Ruler & Classification
                    ruler=coin_data.ruler,
                    ruler_title=coin_data.ruler_title,
                    reign_dates=coin_data.reign_dates,
                    era=coin_data.era,
                    
                    # Coin type
                    denomination=coin_data.denomination,
                    metal=coin_data.metal.value if coin_data.metal else None,
                    mint=coin_data.mint,
                    struck_dates=coin_data.mint_date,  # Biddr uses mint_date
                    struck_under=coin_data.struck_under,
                    
                    # Physical
                    weight_g=float(physical.weight_g) if physical and physical.weight_g else None,
                    diameter_mm=float(physical.diameter_mm) if physical and physical.diameter_mm else None,
                    thickness_mm=float(physical.thickness_mm) if physical and physical.thickness_mm else None,
                    die_axis=physical.die_axis_hours if physical else None,
                    
                    # Descriptions
                    title=coin_data.title,
                    description=coin_data.raw_description,
                    obverse_description=coin_data.obverse_description,
                    reverse_description=coin_data.reverse_description,
                    exergue=coin_data.exergue,
                    
                    # Grading
                    grade=coin_data.grade,
                    condition_notes=coin_data.condition_notes,
                    
                    # References
                    catalog_references=catalog_refs,
                    catalog_references_raw=catalog_refs_raw,
                    primary_reference=coin_data.primary_reference,
                    
                    # Provenance
                    provenance_text=provenance.raw_text if provenance else None,
                    pedigree_year=provenance.pedigree_year if provenance else None,
                    has_provenance=coin_data.has_provenance,
                    provenance_entries=prov_entries,
                    
                    # Photos
                    photos=[img.url for img in coin_data.images] if coin_data.images else [],
                    primary_photo_url=coin_data.images[0].url if coin_data.images else None,
                    
                    # Metadata
                    fetched_at=datetime.utcnow(),
                )
                
                elapsed = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return ScrapeResult(
                    status="success",
                    url=url,
                    house=self.HOUSE,
                    lot_data=lot_data,
                    elapsed_ms=elapsed,
                )
                
        except Exception as e:
            logger.exception(f"Biddr scrape error for {url}")
            return ScrapeResult(
                status="error",
                url=url,
                house=self.HOUSE,
                error_message=str(e),
            )


class EBayAdapter(AuctionScraperBase):
    """Adapter for eBay rich scraper."""
    
    HOUSE = "eBay"
    BASE_URL = "https://www.ebay.com"
    URL_PATTERNS = ["ebay.com", "ebay.co.uk", "ebay.de", "ebay."]
    
    def __init__(self, timeout: float | None = None, user_agent: str | None = None):
        super().__init__(timeout, user_agent)
    
    def parse_lot_id(self, url: str) -> str | None:
        import re
        match = re.search(r'/itm/(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    async def extract_lot(self, url: str) -> ScrapeResult:
        from .ebay_rich import EBayScraper
        
        start_time = datetime.utcnow()
        
        try:
            async with EBayScraper(headless=True) as scraper:
                coin_data = await scraper.scrape_url(url)
                
                if not coin_data:
                    return ScrapeResult(
                        status="not_found",
                        url=url,
                        house=self.HOUSE,
                        error_message="No data returned",
                    )
                
                # Extract nested data
                listing = coin_data.listing
                seller = coin_data.seller
                grading = coin_data.grading
                physical = coin_data.physical
                
                # Determine price (sold_price or current_price)
                hammer_price = None
                if listing:
                    if listing.sold_price:
                        hammer_price = float(listing.sold_price)
                    elif listing.current_price:
                        hammer_price = float(listing.current_price)
                
                # Extract auction date from end_date
                auction_date = None
                closing_date = None
                if listing and listing.end_date:
                    closing_date = listing.end_date
                    auction_date = listing.end_date.date()
                elif listing and listing.sold_date:
                    closing_date = listing.sold_date
                    auction_date = listing.sold_date.date()
                
                # Extract references
                catalog_refs = []
                catalog_refs_raw = []
                if coin_data.references:
                    catalog_refs = [ref.normalized for ref in coin_data.references]
                    catalog_refs_raw = [ref.raw_text for ref in coin_data.references]
                
                # Convert EbayCoinData to LotData with ALL fields
                lot_data = LotData(
                    # Identification
                    lot_id=coin_data.ebay_item_id or self.parse_lot_id(url) or url,
                    house=self.HOUSE,
                    url=coin_data.url or url,
                    
                    # Pricing
                    hammer_price=hammer_price,
                    total_price=float(coin_data.final_price) if coin_data.final_price else None,
                    currency=listing.currency if listing else "USD",
                    sold=listing.is_sold if listing else True,
                    bids=listing.bid_count if listing else None,
                    shipping_cost=float(listing.shipping_cost) if listing and listing.shipping_cost else None,
                    
                    # Auction info
                    auction_date=auction_date,
                    closing_date=closing_date,
                    listing_type=listing.listing_type.value if listing and listing.listing_type else None,
                    watchers=listing.watchers if listing else None,
                    
                    # Ruler & Classification
                    ruler=coin_data.ruler,
                    reign_dates=coin_data.reign_dates,
                    era=coin_data.era,
                    
                    # Coin type
                    denomination=coin_data.denomination,
                    metal=coin_data.metal,  # eBay stores as string, not enum
                    mint=coin_data.mint,
                    struck_dates=coin_data.mint_date,
                    
                    # Physical
                    weight_g=float(physical.weight_g) if physical and physical.weight_g else None,
                    diameter_mm=float(physical.diameter_mm) if physical and physical.diameter_mm else None,
                    thickness_mm=float(physical.thickness_mm) if physical and physical.thickness_mm else None,
                    
                    # Descriptions
                    title=coin_data.title,
                    description=coin_data.description,
                    
                    # Grading
                    grade=grading.grade if grading else None,
                    grade_service=grading.grading_service if grading else None,
                    certification_number=grading.cert_number if grading else None,
                    
                    # References
                    catalog_references=catalog_refs,
                    catalog_references_raw=catalog_refs_raw,
                    primary_reference=coin_data.primary_reference,
                    
                    # Photos
                    photos=[img.url for img in coin_data.images] if coin_data.images else [],
                    primary_photo_url=coin_data.images[0].url if coin_data.images else None,
                    
                    # eBay-specific seller info
                    seller_username=seller.username if seller else None,
                    seller_feedback_score=seller.feedback_score if seller else None,
                    seller_feedback_pct=seller.feedback_percent if seller else None,
                    seller_is_top_rated=seller.is_top_rated if seller else None,
                    seller_location=seller.location if seller else None,
                    
                    # Metadata
                    raw_data=coin_data.item_specifics if coin_data.item_specifics else None,
                    fetched_at=datetime.utcnow(),
                )
                
                elapsed = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return ScrapeResult(
                    status="success",
                    url=url,
                    house=self.HOUSE,
                    lot_data=lot_data,
                    elapsed_ms=elapsed,
                )
                
        except Exception as e:
            logger.exception(f"eBay scrape error for {url}")
            return ScrapeResult(
                status="error",
                url=url,
                house=self.HOUSE,
                error_message=str(e),
            )


class HeritageAdapter(AuctionScraperBase):
    """Adapter for Heritage rich scraper."""
    
    HOUSE = "Heritage"
    BASE_URL = "https://coins.ha.com"
    URL_PATTERNS = ["ha.com", "heritage"]
    
    def __init__(self, timeout: float | None = None, user_agent: str | None = None):
        super().__init__(timeout, user_agent)
    
    def parse_lot_id(self, url: str) -> str | None:
        import re
        match = re.search(r'/a/(\d+-\d+)', url)
        if match:
            return match.group(1)
        return None
    
    async def extract_lot(self, url: str) -> ScrapeResult:
        from .heritage_rich import HeritageScraper
        
        start_time = datetime.utcnow()
        
        try:
            async with HeritageScraper(headless=True) as scraper:
                coin_data = await scraper.scrape_url(url)
                
                if not coin_data:
                    return ScrapeResult(
                        status="not_found",
                        url=url,
                        house=self.HOUSE,
                        error_message="No data returned",
                    )
                
                # Note: Heritage scraper model structure may vary
                # Using safe attribute access
                lot_data = LotData(
                    lot_id=getattr(coin_data, 'lot_id', None) or self.parse_lot_id(url) or url,
                    house=self.HOUSE,
                    url=url,
                    title=getattr(coin_data, 'title', None),
                    description=getattr(coin_data, 'description', None),
                    hammer_price=float(coin_data.hammer_price) if getattr(coin_data, 'hammer_price', None) else None,
                    estimate_low=float(coin_data.estimate_low) if getattr(coin_data, 'estimate_low', None) else None,
                    estimate_high=float(coin_data.estimate_high) if getattr(coin_data, 'estimate_high', None) else None,
                    currency=getattr(coin_data, 'currency', None) or "USD",
                    sold=getattr(coin_data, 'sold', True),
                    sale_name=getattr(coin_data, 'sale_name', None),
                    lot_number=getattr(coin_data, 'lot_number', None),
                    auction_date=getattr(coin_data, 'auction_date', None),
                    grade=getattr(coin_data, 'grade', None),
                    grade_service=getattr(coin_data, 'grade_service', None),
                    certification_number=getattr(coin_data, 'certification_number', None),
                    weight_g=float(coin_data.weight_g) if getattr(coin_data, 'weight_g', None) else None,
                    diameter_mm=float(coin_data.diameter_mm) if getattr(coin_data, 'diameter_mm', None) else None,
                    photos=[img.url for img in coin_data.images] if getattr(coin_data, 'images', None) else [],
                    primary_photo_url=coin_data.images[0].url if getattr(coin_data, 'images', None) else None,
                    fetched_at=datetime.utcnow(),
                )
                
                elapsed = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return ScrapeResult(
                    status="success",
                    url=url,
                    house=self.HOUSE,
                    lot_data=lot_data,
                    elapsed_ms=elapsed,
                )
                
        except Exception as e:
            logger.exception(f"Heritage scrape error for {url}")
            return ScrapeResult(
                status="error",
                url=url,
                house=self.HOUSE,
                error_message=str(e),
            )
