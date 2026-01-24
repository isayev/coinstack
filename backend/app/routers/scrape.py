"""API router for auction scraping operations."""

import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import auction as auction_crud
from app.schemas.auction import (
    ScrapeUrlRequest,
    ScrapeBatchRequest,
    ScrapeUrlResponse,
    ScrapeBatchResponse,
    ScrapeJobStatus,
    ScrapeResultOut,
    DetectHouseResponse,
)
from app.services.scrapers.orchestrator import (
    AuctionOrchestrator,
    create_job,
    get_job,
    update_job,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrape", tags=["scrape"])


# Browser scrape request/response models
class BrowserScrapeRequest(BaseModel):
    """Request for browser-based scraping."""
    url: str
    coin_id: Optional[int] = None
    reference_type_id: Optional[int] = None
    headless: bool = True  # Set False to see browser window (debugging)


class BrowserScrapeResponse(BaseModel):
    """Response from browser-based scraping with full numismatic metadata."""
    status: str
    url: str
    auction_house: Optional[str] = None
    title: Optional[str] = None
    
    # Ruler and classification
    ruler: Optional[str] = None
    ruler_title: Optional[str] = None
    reign_dates: Optional[str] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    mint: Optional[str] = None
    struck_dates: Optional[str] = None
    struck_under: Optional[str] = None
    
    # Physical measurements
    weight_g: Optional[float] = None
    diameter_mm: Optional[float] = None
    die_axis: Optional[int] = None
    
    # Descriptions
    obverse_description: Optional[str] = None
    reverse_description: Optional[str] = None
    description: Optional[str] = None
    
    # Condition
    grade: Optional[str] = None
    condition_notes: Optional[str] = None
    
    # References
    references: Optional[list[str]] = None
    
    # Provenance
    provenance: Optional[str] = None
    pedigree_year: Optional[int] = None
    has_provenance: Optional[bool] = None
    
    # Auction info
    hammer_price: Optional[float] = None
    estimate_usd: Optional[int] = None
    auction_name: Optional[str] = None
    lot_number: Optional[int] = None
    is_sold: Optional[bool] = None
    
    # Images
    photos: Optional[list[str]] = None
    
    # Meta
    error: Optional[str] = None
    auction_id: Optional[int] = None
    scraped_at: Optional[str] = None


def get_orchestrator() -> AuctionOrchestrator:
    """Get configured orchestrator instance."""
    settings = get_settings()
    return AuctionOrchestrator(
        timeout=getattr(settings, 'SCRAPER_TIMEOUT', 30.0),
        rate_limit=getattr(settings, 'SCRAPER_RATE_LIMIT', 2.0),
    )


async def _process_scrape(
    orchestrator: AuctionOrchestrator,
    db: Session,
    url: str,
    coin_id: int | None,
    reference_type_id: int | None,
    job_id: str,
):
    """Background task to process a single URL scrape."""
    try:
        update_job(job_id, status="processing")
        
        result = await orchestrator.scrape_url(url)
        
        auction_id = None
        if result.status in ("success", "partial") and result.lot_data:
            # Upsert to database
            auction_data, created = auction_crud.upsert_auction(
                db,
                url=url,
                data=orchestrator.lot_data_to_auction_data(
                    result.lot_data,
                    coin_id=coin_id,
                    reference_type_id=reference_type_id,
                ),
            )
            auction_id = auction_data.id
        
        # Update job with result
        scrape_result = ScrapeResultOut(
            status=result.status,
            url=result.url,
            house=result.house,
            error_message=result.error_message,
            auction_id=auction_id,
            elapsed_ms=result.elapsed_ms,
            title=result.lot_data.title if result.lot_data else None,
            hammer_price=result.lot_data.hammer_price if result.lot_data else None,
            sold=result.lot_data.sold if result.lot_data else None,
        )
        
        update_job(
            job_id,
            status="completed",
            completed_urls=1,
            results=[scrape_result],
            completed_at=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.exception(f"Error processing scrape job {job_id}")
        update_job(
            job_id,
            status="failed",
            error_message=str(e),
            completed_at=datetime.utcnow(),
        )


async def _process_batch_scrape(
    orchestrator: AuctionOrchestrator,
    db: Session,
    urls: list[str],
    coin_id: int | None,
    job_id: str,
):
    """Background task to process batch URL scrape."""
    try:
        update_job(job_id, status="processing")
        
        results = []
        completed = 0
        failed = 0
        
        for url in urls:
            try:
                result = await orchestrator.scrape_url(url)
                
                auction_id = None
                if result.status in ("success", "partial") and result.lot_data:
                    auction_data, created = auction_crud.upsert_auction(
                        db,
                        url=url,
                        data=orchestrator.lot_data_to_auction_data(
                            result.lot_data,
                            coin_id=coin_id,
                        ),
                    )
                    auction_id = auction_data.id
                    completed += 1
                else:
                    failed += 1
                
                results.append(ScrapeResultOut(
                    status=result.status,
                    url=result.url,
                    house=result.house,
                    error_message=result.error_message,
                    auction_id=auction_id,
                    elapsed_ms=result.elapsed_ms,
                    title=result.lot_data.title if result.lot_data else None,
                    hammer_price=result.lot_data.hammer_price if result.lot_data else None,
                    sold=result.lot_data.sold if result.lot_data else None,
                ))
                
                # Update progress
                update_job(
                    job_id,
                    completed_urls=completed,
                    failed_urls=failed,
                    results=results,
                )
                
            except Exception as e:
                logger.exception(f"Error scraping {url}")
                failed += 1
                results.append(ScrapeResultOut(
                    status="error",
                    url=url,
                    error_message=str(e),
                ))
        
        update_job(
            job_id,
            status="completed",
            completed_urls=completed,
            failed_urls=failed,
            results=results,
            completed_at=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.exception(f"Error processing batch scrape job {job_id}")
        update_job(
            job_id,
            status="failed",
            error_message=str(e),
            completed_at=datetime.utcnow(),
        )


@router.post("/url", response_model=ScrapeUrlResponse)
async def scrape_url(
    request: ScrapeUrlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Scrape a single auction URL.
    
    The scraping is performed in the background. Poll /scrape/status/{job_id}
    to check for results.
    """
    orchestrator = get_orchestrator()
    
    # Check if URL is supported
    house = orchestrator.detect_house(request.url)
    if not house:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported auction URL. Supported platforms: Heritage, CNG, Biddr, eBay, Agora",
        )
    
    # Create job
    job = create_job(total_urls=1)
    
    # Start background task
    background_tasks.add_task(
        _process_scrape,
        orchestrator,
        db,
        request.url,
        request.coin_id,
        request.reference_type_id,
        job.job_id,
    )
    
    return ScrapeUrlResponse(
        job_id=job.job_id,
        status="processing",
    )


@router.post("/batch", response_model=ScrapeBatchResponse)
async def scrape_batch(
    request: ScrapeBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Scrape multiple auction URLs.
    
    The scraping is performed in the background. Poll /scrape/status/{job_id}
    to check for results.
    """
    orchestrator = get_orchestrator()
    
    # Validate at least one URL is supported
    supported_urls = [url for url in request.urls if orchestrator.detect_house(url)]
    if not supported_urls:
        raise HTTPException(
            status_code=400,
            detail="No supported auction URLs provided",
        )
    
    # Create job
    job = create_job(total_urls=len(request.urls))
    
    # Start background task
    background_tasks.add_task(
        _process_batch_scrape,
        orchestrator,
        db,
        request.urls,
        request.coin_id,
        job.job_id,
    )
    
    return ScrapeBatchResponse(
        job_id=job.job_id,
        status="processing",
        total_urls=len(request.urls),
    )


@router.get("/status/{job_id}", response_model=ScrapeJobStatus)
def get_scrape_status(job_id: str):
    """Get the status of a scrape job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ScrapeJobStatus(
        job_id=job.job_id,
        status=job.status,
        total_urls=job.total_urls,
        completed_urls=job.completed_urls,
        failed_urls=job.failed_urls,
        results=[
            ScrapeResultOut(
                status=r.status,
                url=r.url,
                house=r.house,
                error_message=r.error_message,
                elapsed_ms=r.elapsed_ms,
            ) for r in job.results
        ] if job.results else [],
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
    )


@router.post("/detect", response_model=DetectHouseResponse)
def detect_house(url: str):
    """Detect which auction house a URL belongs to."""
    orchestrator = get_orchestrator()
    house = orchestrator.detect_house(url)
    
    return DetectHouseResponse(
        url=url,
        house=house,
        supported=house is not None,
    )


@router.post("/coin/{coin_id}/refresh", response_model=ScrapeBatchResponse)
async def refresh_coin_auctions(
    coin_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Re-scrape all auction URLs linked to a coin.
    
    This refreshes the data for all auction records associated with the coin.
    """
    # Get existing auction records for the coin
    auctions = auction_crud.get_auctions_for_coin(db, coin_id)
    
    if not auctions:
        raise HTTPException(
            status_code=404,
            detail="No auction records found for this coin",
        )
    
    urls = [a.url for a in auctions if a.url]
    
    orchestrator = get_orchestrator()
    job = create_job(total_urls=len(urls))
    
    background_tasks.add_task(
        _process_batch_scrape,
        orchestrator,
        db,
        urls,
        coin_id,
        job.job_id,
    )
    
    return ScrapeBatchResponse(
        job_id=job.job_id,
        status="processing",
        total_urls=len(urls),
    )


@router.post("/browser", response_model=BrowserScrapeResponse)
async def browser_scrape(
    request: BrowserScrapeRequest,
    db: Session = Depends(get_db),
):
    """
    Scrape an auction URL using browser automation (Playwright).
    
    This uses a real browser with stealth mode to bypass bot detection.
    Recommended for Heritage and CNG which block simple HTTP requests.
    
    This is a synchronous endpoint - waits for scrape to complete.
    Use for occasional manual scraping, not bulk operations.
    """
    from app.services.scrapers.browser_scraper import (
        scrape_auction_url,
        BrowserConfig,
    )
    
    try:
        config = BrowserConfig(headless=request.headless)
        data = await scrape_auction_url(request.url, config)
        
        # Save ALL metadata to database
        auction_id = None
        if data.get('title') or data.get('hammer_price'):
            # Build comprehensive auction data with all extracted fields
            auction_record = {
                # Auction identification
                'auction_house': data.get('auction_house'),
                'sale_name': data.get('auction_name') or data.get('sale_name'),
                'lot_number': str(data.get('lot_number')) if data.get('lot_number') else None,
                'source_lot_id': data.get('lot_id'),
                'url': request.url,
                
                # Pricing
                'estimate_usd': data.get('estimate_usd'),
                'hammer_price': data.get('hammer_price'),
                'total_price': data.get('total_price_usd'),
                'currency': 'USD',
                'sold': data.get('is_sold', False),
                'bids': data.get('bids'),
                
                # Ruler & classification
                'ruler': data.get('ruler'),
                'ruler_title': data.get('ruler_title'),
                'reign_dates': data.get('reign_dates'),
                'denomination': data.get('denomination'),
                'metal': data.get('metal'),
                'mint': data.get('mint'),
                'struck_dates': data.get('struck_dates'),
                'struck_under': data.get('struck_under'),
                'categories': data.get('categories'),
                
                # Physical measurements
                'weight_g': data.get('weight_g'),
                'diameter_mm': data.get('diameter_mm'),
                'die_axis': data.get('die_axis'),
                
                # Descriptions
                'title': data.get('title'),
                'description': data.get('description'),
                'obverse_description': data.get('obverse_description'),
                'reverse_description': data.get('reverse_description'),
                
                # Condition & grading
                'grade': data.get('grade'),
                'grade_service': data.get('grade_service'),
                'condition_notes': data.get('condition_notes'),
                
                # References
                'catalog_references': data.get('references'),
                'catalog_references_raw': data.get('references_raw'),
                'primary_reference': data.get('references', [None])[0] if data.get('references') else None,
                
                # Provenance
                'provenance_text': data.get('provenance'),
                'pedigree_year': data.get('pedigree_year'),
                'has_provenance': data.get('has_provenance', False),
                
                # Photos
                'photos': data.get('photos'),
                'primary_photo_url': data.get('photos', [None])[0] if data.get('photos') else None,
                
                # Metadata
                'scraped_at': datetime.fromisoformat(data['scraped_at']) if data.get('scraped_at') else datetime.utcnow(),
                'raw_data': data,  # Store full response for debugging
                
                # Links
                'coin_id': request.coin_id,
                'reference_type_id': request.reference_type_id,
            }
            
            auction_data, created = auction_crud.upsert_auction(
                db,
                url=request.url,
                data=auction_record,
            )
            auction_id = auction_data.id
        
        return BrowserScrapeResponse(
            status="success" if data.get('title') else "partial",
            url=request.url,
            auction_house=data.get('auction_house'),
            title=data.get('title'),
            
            # Ruler and classification
            ruler=data.get('ruler'),
            ruler_title=data.get('ruler_title'),
            reign_dates=data.get('reign_dates'),
            denomination=data.get('denomination'),
            metal=data.get('metal'),
            mint=data.get('mint'),
            struck_dates=data.get('struck_dates'),
            struck_under=data.get('struck_under'),
            
            # Physical measurements
            weight_g=data.get('weight_g'),
            diameter_mm=data.get('diameter_mm'),
            die_axis=data.get('die_axis'),
            
            # Descriptions
            obverse_description=data.get('obverse_description'),
            reverse_description=data.get('reverse_description'),
            description=data.get('description', '')[:1000] if data.get('description') else None,
            
            # Condition
            grade=data.get('grade'),
            condition_notes=data.get('condition_notes'),
            
            # References
            references=data.get('references'),
            
            # Provenance
            provenance=data.get('provenance'),
            pedigree_year=data.get('pedigree_year'),
            has_provenance=data.get('has_provenance'),
            
            # Auction info
            hammer_price=data.get('hammer_price'),
            estimate_usd=data.get('estimate_usd'),
            auction_name=data.get('auction_name'),
            lot_number=data.get('lot_number'),
            is_sold=data.get('is_sold'),
            
            # Images
            photos=data.get('photos'),
            
            # Meta
            auction_id=auction_id,
            scraped_at=data.get('scraped_at'),
        )
        
    except Exception as e:
        logger.exception(f"Browser scrape failed for {request.url}")
        return BrowserScrapeResponse(
            status="error",
            url=request.url,
            error=str(e),
        )


@router.post("/browser/batch")
async def browser_scrape_batch(
    urls: list[str],
    coin_id: Optional[int] = None,
    headless: bool = True,
    db: Session = Depends(get_db),
):
    """
    Scrape multiple URLs using browser automation.
    
    Processes URLs sequentially with delays to avoid detection.
    Results are returned when all URLs are processed.
    """
    from app.services.scrapers.browser_scraper import (
        BrowserScraper,
        BrowserConfig,
        HeritagePageParser,
        CNGPageParser,
    )
    
    config = BrowserConfig(headless=headless)
    scraper = BrowserScraper(config)
    results = []
    
    try:
        await scraper.start()
        
        for url in urls:
            try:
                async with scraper.new_page() as page:
                    await scraper._random_delay()
                    response = await page.goto(url, wait_until='networkidle')
                    
                    if response and response.status < 400:
                        html = await page.content()
                        
                        # Parse based on URL
                        if 'ha.com' in url.lower():
                            data = HeritagePageParser.parse(html, url)
                        elif 'cngcoins.com' in url.lower():
                            data = CNGPageParser.parse(html, url)
                        else:
                            data = {'url': url, 'status': 'unsupported'}
                        
                        # Save to database
                        if data.get('title') or data.get('hammer_price'):
                            auction_data, _ = auction_crud.upsert_auction(
                                db,
                                url=url,
                                data={
                                    'auction_house': data.get('auction_house'),
                                    'hammer_price': data.get('hammer_price'),
                                    'title': data.get('title'),
                                    'weight_g': data.get('weight_g'),
                                    'diameter_mm': data.get('diameter_mm'),
                                    'grade': data.get('grade'),
                                    'coin_id': coin_id,
                                    'url': url,
                                },
                            )
                            data['auction_id'] = auction_data.id
                        
                        data['status'] = 'success'
                        results.append(data)
                    else:
                        results.append({
                            'url': url,
                            'status': 'error',
                            'error': f'HTTP {response.status if response else "unknown"}'
                        })
                        
            except Exception as e:
                logger.exception(f"Error scraping {url}")
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
    
    finally:
        await scraper.stop()
    
    return {
        'total': len(urls),
        'success': sum(1 for r in results if r.get('status') == 'success'),
        'failed': sum(1 for r in results if r.get('status') == 'error'),
        'results': results
    }
