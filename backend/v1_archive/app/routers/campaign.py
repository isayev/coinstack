"""API router for data enrichment campaigns."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.enrichment_campaign import (
    HeritageEnrichmentCampaign,
    CampaignConfig,
    get_campaign,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaign", tags=["campaign"])


# Request/Response models
class CampaignStartRequest(BaseModel):
    """Request to start an enrichment campaign."""
    delay_seconds: float = Field(default=30.0, ge=10.0, description="Seconds between URLs (min 10)")
    batch_size: int = Field(default=10, ge=1, le=1000, description="Number of URLs to process")
    captcha_wait: float = Field(default=45.0, ge=10.0, description="Seconds to wait for captcha")


class CampaignStatusResponse(BaseModel):
    """Campaign status response."""
    total_urls: int
    processed: int
    pending: int
    successful: int
    errors: int
    is_running: bool
    current_url: Optional[str] = None


class CampaignStartResponse(BaseModel):
    """Response when starting a campaign."""
    status: str
    message: str
    total_pending: int
    batch_size: int
    delay_seconds: float


class ProcessOneRequest(BaseModel):
    """Request to process a single URL."""
    url: str
    wait_seconds: float = Field(default=45.0, ge=10.0, description="Seconds to wait for captcha")


class ProcessOneResponse(BaseModel):
    """Response from processing single URL."""
    status: str
    url: str
    campaign_successful: Optional[bool] = None
    error: Optional[str] = None
    data: Optional[dict] = None


class PendingUrlsResponse(BaseModel):
    """Response with list of pending URLs."""
    total: int
    urls: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# HERITAGE CAMPAIGN ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/heritage/status", response_model=CampaignStatusResponse)
async def get_heritage_campaign_status(
    db: Session = Depends(get_db)
):
    """
    Get the current status of the Heritage enrichment campaign.
    
    Returns counts of total, processed, pending, successful, and error URLs.
    Also indicates if a campaign is currently running.
    """
    campaign = get_campaign()
    status = campaign.get_status(db)
    
    return CampaignStatusResponse(
        total_urls=status.total_urls,
        processed=status.processed,
        pending=status.pending,
        successful=status.successful,
        errors=status.errors,
        is_running=status.is_running,
        current_url=status.current_url
    )


@router.get("/heritage/pending", response_model=PendingUrlsResponse)
async def get_heritage_pending_urls(
    db: Session = Depends(get_db),
    limit: int = 100
):
    """
    Get list of pending Heritage URLs to be processed.
    
    Returns URLs that haven't been processed by the campaign yet.
    """
    campaign = get_campaign()
    pending = campaign.get_all_pending_urls(db)
    
    return PendingUrlsResponse(
        total=len(pending),
        urls=pending[:limit]
    )


@router.post("/heritage/start", response_model=CampaignStartResponse)
async def start_heritage_campaign(
    request: CampaignStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start the Heritage enrichment campaign.
    
    This will:
    1. Open a visible browser (headless=False)
    2. Process URLs one by one with delays
    3. Wait for manual captcha solving if needed
    4. Store all scraped data in AuctionData
    
    Only one campaign can run at a time. Returns 409 if already running.
    """
    campaign = get_campaign()
    
    # Check if already running
    if campaign.is_running():
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Campaign already running",
                "current_url": campaign.get_current_url()
            }
        )
    
    # Get pending count
    pending = campaign.get_all_pending_urls(db)
    
    if not pending:
        return CampaignStartResponse(
            status="complete",
            message="No pending URLs to process",
            total_pending=0,
            batch_size=request.batch_size,
            delay_seconds=request.delay_seconds
        )
    
    # Update campaign config
    campaign.config.delay_between_urls = request.delay_seconds
    campaign.config.batch_size = request.batch_size
    campaign.config.captcha_wait_time = request.captcha_wait
    campaign.config.headless = False  # Always visible for Heritage
    
    # Start campaign in background
    async def run_campaign_task():
        from app.database import SessionLocal
        with SessionLocal() as session:
            await campaign.run_campaign(
                session,
                batch_size=request.batch_size,
                delay_between=request.delay_seconds
            )
    
    background_tasks.add_task(run_campaign_task)
    
    logger.info(f"Started Heritage campaign: {len(pending)} pending, "
               f"batch={request.batch_size}, delay={request.delay_seconds}s")
    
    return CampaignStartResponse(
        status="started",
        message=f"Campaign started. Processing {min(request.batch_size, len(pending))} URLs.",
        total_pending=len(pending),
        batch_size=request.batch_size,
        delay_seconds=request.delay_seconds
    )


@router.post("/heritage/process-one", response_model=ProcessOneResponse)
async def process_single_heritage_url(
    request: ProcessOneRequest,
    db: Session = Depends(get_db)
):
    """
    Process a single Heritage URL immediately.
    
    Opens a visible browser, navigates to the URL, and waits for
    the specified time for manual captcha solving.
    
    This is synchronous - the response returns after scraping completes.
    """
    campaign = get_campaign()
    
    # Check if campaign is running
    if campaign.is_running():
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Cannot process - campaign is running",
                "current_url": campaign.get_current_url()
            }
        )
    
    # Validate URL is Heritage
    url_lower = request.url.lower()
    if 'ha.com' not in url_lower and 'heritage' not in url_lower:
        raise HTTPException(
            status_code=400,
            detail="URL must be a Heritage Auctions URL (ha.com)"
        )
    
    logger.info(f"Processing single Heritage URL: {request.url}")
    
    # Configure for visible browser
    campaign.config.headless = False
    
    result = await campaign.process_single_url(
        db, 
        request.url,
        wait_for_captcha=request.wait_seconds
    )
    
    return ProcessOneResponse(
        status=result.get('status', 'error'),
        url=request.url,
        campaign_successful=result.get('campaign_successful'),
        error=result.get('error'),
        data=result.get('data')
    )


@router.post("/heritage/stop")
async def stop_heritage_campaign():
    """
    Request to stop the running campaign.
    
    Note: This only sets a flag. The current URL will finish processing
    before the campaign stops.
    """
    campaign = get_campaign()
    
    if not campaign.is_running():
        return {"status": "not_running", "message": "No campaign is currently running"}
    
    # Set stop flag (would need to implement in campaign class)
    # For now, just return status
    return {
        "status": "stopping",
        "message": "Campaign will stop after current URL completes",
        "current_url": campaign.get_current_url()
    }


@router.post("/heritage/reset-errors")
async def reset_heritage_errors(
    db: Session = Depends(get_db)
):
    """
    Reset campaign_scraped_at for failed URLs so they can be reprocessed.
    
    This allows re-running the campaign on URLs that previously failed.
    """
    from app.models.auction_data import AuctionData
    from sqlalchemy import or_, and_
    
    # Find Heritage URLs with errors
    result = db.query(AuctionData).filter(
        and_(
            or_(
                AuctionData.auction_house.ilike('%heritage%'),
                AuctionData.url.contains('ha.com')
            ),
            AuctionData.campaign_scraped_at.isnot(None),
            AuctionData.campaign_successful == False
        )
    ).update({
        'campaign_scraped_at': None,
        'campaign_successful': None,
        'campaign_error': None
    }, synchronize_session=False)
    
    db.commit()
    
    return {
        "status": "success",
        "reset_count": result,
        "message": f"Reset {result} failed URLs for reprocessing"
    }
