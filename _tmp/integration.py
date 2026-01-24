"""
Heritage Integration with CoinStack Audit System

Integrates Heritage scraper with the data audit/enrichment workflow:
- Match scraped data to existing coins
- Create DiscrepancyRecords for conflicts
- Create EnrichmentRecords for missing data
- Download and link images
- Handle NGC/PCGS certification verification
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from .scraper import HeritageScraper, scrape_heritage_lot
from .models import HeritageCoinData, HeritageImage, GradingService

logger = logging.getLogger(__name__)


class HeritageIntegration:
    """
    Integrates Heritage scraper with CoinStack audit system.
    
    Heritage-specific features:
    - NGC/PCGS grade handling with certification verification
    - High-quality images from heritagestatic.com CDN
    - Historical notes extraction
    - Named collection provenance tracking
    """
    
    # Field mapping: Heritage field -> CoinStack field
    FIELD_MAPPING = {
        'ruler': 'issuing_authority',
        'denomination': 'denomination',
        'mint': 'mint',
        'physical.weight_gm': 'weight_g',
        'physical.diameter_mm': 'diameter_mm',
        'physical.die_axis_hours': 'die_axis',
        'grade_display': 'grade',
        'mint_date': 'minted_date',
        'obverse_description': 'obverse_description',
        'reverse_description': 'reverse_description',
        'obverse_legend': 'obverse_legend',
        'reverse_legend': 'reverse_legend',
    }
    
    def __init__(self, db=None):
        """
        Initialize integration.
        
        Args:
            db: Database session (SQLAlchemy AsyncSession)
        """
        self.db = db
        self.scraper = HeritageScraper()
    
    async def __aenter__(self):
        await self.scraper.__aenter__()
        return self
    
    async def __aexit__(self, *args):
        await self.scraper.__aexit__(*args)
    
    async def import_from_url(
        self,
        url: str,
        coin_id: Optional[int] = None,
        create_if_missing: bool = False,
        verify_certification: bool = True,
    ) -> dict:
        """
        Import Heritage lot data, optionally matching to existing coin.
        
        Args:
            url: Heritage lot URL
            coin_id: Optional existing coin to match/update
            create_if_missing: Create new coin if no match found
            verify_certification: Verify NGC/PCGS cert numbers
            
        Returns:
            dict with import results
        """
        # Scrape Heritage data
        heritage_data = await self.scraper.scrape_url(url, download_images=True)
        
        # Verify certification if slabbed
        cert_verified = None
        if verify_certification and heritage_data.is_slabbed:
            cert_verified = await self._verify_certification(heritage_data)
        
        # Store as AuctionData
        auction_data = await self._create_auction_data(heritage_data)
        
        result = {
            'heritage_lot_id': heritage_data.heritage_lot_id,
            'auction_data_id': auction_data.id if auction_data else None,
            'coin_id': coin_id,
            'discrepancies': [],
            'enrichments': [],
            'images_downloaded': len([i for i in heritage_data.images if i.local_path]),
            'is_slabbed': heritage_data.is_slabbed,
            'certification_verified': cert_verified,
        }
        
        # If coin_id provided, run audit
        if coin_id:
            result.update(await self._audit_against_coin(coin_id, heritage_data, auction_data))
        elif create_if_missing:
            new_coin = await self._create_coin_from_heritage(heritage_data, auction_data)
            result['coin_id'] = new_coin.id
            result['created_new'] = True
        
        return result
    
    async def _verify_certification(self, heritage_data: HeritageCoinData) -> Optional[bool]:
        """Verify NGC/PCGS certification"""
        if not heritage_data.slab_grade:
            return None
        
        cert_number = heritage_data.slab_grade.certification_number
        if not cert_number:
            return None
        
        if heritage_data.slab_grade.service == GradingService.NGC:
            verification = await self.scraper.verify_ngc_cert(cert_number)
            return verification.get('verified', False) if verification else False
        
        # PCGS verification would go here
        return None
    
    async def _create_auction_data(self, heritage_data: HeritageCoinData):
        """Create AuctionData record from Heritage scrape"""
        
        # Build grade string
        grade = None
        if heritage_data.is_slabbed and heritage_data.slab_grade:
            grade = heritage_data.slab_grade.full_grade
        elif heritage_data.raw_grade:
            grade = heritage_data.raw_grade.full_grade
        
        auction_data = {
            'source': 'heritage',
            'source_id': heritage_data.heritage_lot_id,
            'source_url': heritage_data.url,
            'auction_house': 'Heritage Auctions',
            'auction_name': heritage_data.auction.auction_name if heritage_data.auction else None,
            'lot_number': heritage_data.auction.lot_number if heritage_data.auction else None,
            'title': heritage_data.title,
            'description': heritage_data.raw_description,
            
            # Physical
            'weight_g': heritage_data.physical.weight_gm,
            'diameter_mm': heritage_data.physical.diameter_mm,
            'die_axis': heritage_data.physical.die_axis_hours,
            
            # Classification
            'category': heritage_data.category,
            'denomination': heritage_data.denomination,
            'metal': heritage_data.metal.value if heritage_data.metal else None,
            'mint': heritage_data.mint,
            
            # Grading
            'grade': grade,
            'is_slabbed': heritage_data.is_slabbed,
            'grading_service': heritage_data.slab_grade.service.value if heritage_data.slab_grade else None,
            'certification_number': heritage_data.certification_number,
            
            # Auction results
            'sold_price_usd': heritage_data.auction.sold_price_usd if heritage_data.auction else None,
            'auction_date': heritage_data.auction.auction_date if heritage_data.auction else None,
            'is_sold': heritage_data.auction.is_sold if heritage_data.auction else False,
            
            # Legends
            'obverse_legend': heritage_data.obverse_legend,
            'reverse_legend': heritage_data.reverse_legend,
            'obverse_description': heritage_data.obverse_description,
            'reverse_description': heritage_data.reverse_description,
            
            # Provenance
            'provenance_text': heritage_data.provenance.raw_text,
            'collection_name': heritage_data.provenance.collection_name,
            
            # References
            'references': [ref.raw_text for ref in heritage_data.references],
            
            # Images
            'image_urls': [img.url for img in heritage_data.images],
            'local_image_paths': [img.local_path for img in heritage_data.images if img.local_path],
            
            # Metadata
            'scraped_at': heritage_data.scraped_at,
        }
        
        logger.info(f"Would create AuctionData: {auction_data['source_id']}")
        return type('MockAuctionData', (), {'id': 1, **auction_data})()
    
    async def _audit_against_coin(
        self,
        coin_id: int,
        heritage_data: HeritageCoinData,
        auction_data
    ) -> dict:
        """Audit Heritage data against existing coin"""
        discrepancies = []
        enrichments = []
        
        # For each mapped field, compare values
        for heritage_field, coin_field in self.FIELD_MAPPING.items():
            heritage_value = self._get_nested_attr(heritage_data, heritage_field)
            coin_value = None  # Would fetch from DB
            
            if heritage_value is None:
                continue
            
            if coin_value is None:
                # Missing data - enrichment opportunity
                enrichments.append({
                    'field': coin_field,
                    'suggested_value': heritage_value,
                    'source': 'heritage',
                    'source_id': heritage_data.heritage_lot_id,
                    'confidence': 'high' if heritage_data.is_slabbed else 'medium',
                })
        
        # NGC/PCGS grade is authoritative - special handling
        if heritage_data.is_slabbed and heritage_data.slab_grade:
            enrichments.append({
                'field': 'certified_grade',
                'suggested_value': {
                    'service': heritage_data.slab_grade.service.value,
                    'grade': heritage_data.slab_grade.grade,
                    'strike': heritage_data.slab_grade.strike_score,
                    'surface': heritage_data.slab_grade.surface_score,
                    'cert_number': heritage_data.slab_grade.certification_number,
                },
                'source': 'heritage',
                'confidence': 'authoritative',
            })
        
        # Provenance enrichment
        if heritage_data.provenance.has_provenance:
            enrichments.append({
                'field': 'provenance',
                'suggested_value': heritage_data.provenance.raw_text,
                'source': 'heritage',
                'collection_name': heritage_data.provenance.collection_name,
            })
        
        # References enrichment
        if heritage_data.references:
            enrichments.append({
                'field': 'references',
                'suggested_value': [ref.normalized for ref in heritage_data.references],
                'source': 'heritage',
            })
        
        # Legends (often missing in user data)
        if heritage_data.obverse_legend:
            enrichments.append({
                'field': 'obverse_legend',
                'suggested_value': heritage_data.obverse_legend,
                'source': 'heritage',
            })
        
        if heritage_data.reverse_legend:
            enrichments.append({
                'field': 'reverse_legend',
                'suggested_value': heritage_data.reverse_legend,
                'source': 'heritage',
            })
        
        return {
            'discrepancies': discrepancies,
            'enrichments': enrichments,
        }
    
    async def _create_coin_from_heritage(
        self,
        heritage_data: HeritageCoinData,
        auction_data
    ):
        """Create new coin from Heritage data"""
        
        grade = None
        if heritage_data.is_slabbed and heritage_data.slab_grade:
            grade = heritage_data.slab_grade.full_grade
        elif heritage_data.raw_grade:
            grade = heritage_data.raw_grade.full_grade
        
        coin_data = {
            'issuing_authority': heritage_data.ruler,
            'ruler_title': heritage_data.ruler_title,
            'reign_dates': heritage_data.reign_dates,
            'denomination': heritage_data.denomination,
            'mint': heritage_data.mint,
            'metal': heritage_data.metal.value if heritage_data.metal else None,
            'minted_date': heritage_data.mint_date,
            'weight_g': heritage_data.physical.weight_gm,
            'diameter_mm': heritage_data.physical.diameter_mm,
            'die_axis': heritage_data.physical.die_axis_hours,
            'grade': grade,
            'is_slabbed': heritage_data.is_slabbed,
            'grading_service': heritage_data.slab_grade.service.value if heritage_data.slab_grade else None,
            'certification_number': heritage_data.certification_number,
            'obverse_legend': heritage_data.obverse_legend,
            'obverse_description': heritage_data.obverse_description,
            'reverse_legend': heritage_data.reverse_legend,
            'reverse_description': heritage_data.reverse_description,
        }
        
        logger.info(f"Would create Coin: {coin_data}")
        return type('MockCoin', (), {'id': 1, **coin_data})()
    
    def _get_nested_attr(self, obj, path: str):
        """Get nested attribute by dot-separated path"""
        parts = path.split('.')
        value = obj
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        return value


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BATCH PROCESSING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def batch_import_heritage(
    urls: list[str],
    verify_certs: bool = True,
) -> list[dict]:
    """
    Import multiple Heritage lots.
    
    Args:
        urls: List of Heritage lot URLs
        verify_certs: Verify NGC/PCGS certifications
        
    Returns:
        List of import results
    """
    results = []
    
    async with HeritageIntegration() as integration:
        for url in urls:
            try:
                result = await integration.import_from_url(
                    url,
                    verify_certification=verify_certs
                )
                results.append(result)
                logger.info(f"Imported {result['heritage_lot_id']}")
            except Exception as e:
                logger.error(f"Failed to import {url}: {e}")
                results.append({'url': url, 'error': str(e)})
    
    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXAMPLE USAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def example_scrape():
    """Example: Scrape a single lot"""
    url = "https://coins.ha.com/itm/ancients/roman-imperial/roman-imperial-gallienus-sole-reign-ad-253-268-bi-antoninianus-22mm-362-gm-7h-ngc-ms-4-5-4-5/a/61519-25316.s"
    
    coin = await scrape_heritage_lot(url)
    
    print(f"Category: {coin.category}")
    print(f"Ruler: {coin.ruler} ({coin.ruler_title})")
    print(f"Reign: {coin.reign_dates}")
    print(f"Denomination: {coin.metal} {coin.denomination}")
    print(f"Physical: {coin.physical.diameter_mm}mm, {coin.physical.weight_gm}gm, {coin.physical.die_axis_hours}h")
    print(f"Mint: {coin.mint}, {coin.mint_date}")
    
    print(f"\nSlabbed: {coin.is_slabbed}")
    if coin.slab_grade:
        print(f"Grade: {coin.slab_grade.full_grade}")
        print(f"Cert #: {coin.slab_grade.certification_number}")
        print(f"Verify: {coin.slab_grade.verification_url}")
    elif coin.raw_grade:
        print(f"Grade: {coin.raw_grade.full_grade}")
    
    print(f"\nObverse: {coin.obverse_legend}")
    print(f"  {coin.obverse_description}")
    print(f"Reverse: {coin.reverse_legend}")
    print(f"  {coin.reverse_description}")
    
    print(f"\nReferences: {[ref.normalized for ref in coin.references]}")
    print(f"Provenance: {coin.provenance.raw_text}")
    print(f"Collection: {coin.provenance.collection_name}")
    
    if coin.auction:
        print(f"\nAuction: {coin.auction.auction_name}")
        print(f"Lot #: {coin.auction.lot_number}")
        print(f"Sold: {coin.auction.is_sold}")
    
    print(f"\nImages: {len(coin.images)}")
    for img in coin.images:
        print(f"  [{img.source}] {img.image_type}: {img.url[:60]}...")


if __name__ == "__main__":
    asyncio.run(example_scrape())
