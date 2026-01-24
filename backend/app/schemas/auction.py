"""Pydantic schemas for auction and scrape endpoints."""

from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, HttpUrl, Field


# ============================================================================
# Auction Data Schemas
# ============================================================================

class AuctionDataBase(BaseModel):
    """Base schema for auction data."""
    
    auction_house: str = Field(..., description="Auction house name (Heritage, CNG, etc.)")
    sale_name: str | None = Field(None, description="Sale/auction name")
    lot_number: str | None = Field(None, description="Lot number in the sale")
    auction_date: date | None = Field(None, description="Date of the auction")
    url: str = Field(..., description="URL to the auction lot page")
    
    # Pricing
    estimate_low: float | None = Field(None, description="Low estimate")
    estimate_high: float | None = Field(None, description="High estimate")
    hammer_price: float | None = Field(None, description="Hammer price (before premium)")
    total_price: float | None = Field(None, description="Total price including premium")
    currency: str = Field("USD", description="Currency code")
    sold: bool = Field(True, description="Whether the lot sold")
    
    # Grading
    grade: str | None = Field(None, description="Grade (e.g., VF, XF, MS65)")
    grade_service: str | None = Field(None, description="Grading service (NGC, PCGS)")
    certification_number: str | None = Field(None, description="Certification number")
    
    # Coin details
    title: str | None = Field(None, description="Lot title")
    description: str | None = Field(None, description="Lot description")
    weight_g: float | None = Field(None, description="Weight in grams")
    diameter_mm: float | None = Field(None, description="Diameter in mm")
    
    # Photos
    photos: list[str] | None = Field(None, description="List of photo URLs")
    primary_photo_url: str | None = Field(None, description="Primary photo URL")


class AuctionDataCreate(AuctionDataBase):
    """Schema for creating auction data."""
    
    coin_id: int | None = Field(None, description="ID of linked coin (if owned)")
    reference_type_id: int | None = Field(None, description="Reference type ID (for comparables)")


class AuctionDataUpdate(BaseModel):
    """Schema for updating auction data."""
    
    coin_id: int | None = None
    auction_house: str | None = None
    sale_name: str | None = None
    lot_number: str | None = None
    auction_date: date | None = None
    url: str | None = None
    
    estimate_low: float | None = None
    estimate_high: float | None = None
    hammer_price: float | None = None
    total_price: float | None = None
    currency: str | None = None
    sold: bool | None = None
    
    grade: str | None = None
    grade_service: str | None = None
    certification_number: str | None = None
    
    title: str | None = None
    description: str | None = None
    weight_g: float | None = None
    diameter_mm: float | None = None
    
    photos: list[str] | None = None
    primary_photo_url: str | None = None
    reference_type_id: int | None = None


class AuctionDataOut(AuctionDataBase):
    """Schema for auction data output."""
    
    id: int
    coin_id: int | None = None
    reference_type_id: int | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AuctionDataListItem(BaseModel):
    """Abbreviated schema for list views."""
    
    id: int
    auction_house: str
    sale_name: str | None = None
    lot_number: str | None = None
    auction_date: date | None = None
    url: str
    hammer_price: float | None = None
    currency: str = "USD"
    sold: bool = True
    grade: str | None = None
    title: str | None = None
    primary_photo_url: str | None = None
    coin_id: int | None = None
    
    class Config:
        from_attributes = True


class PaginatedAuctions(BaseModel):
    """Paginated auction data response."""
    
    items: list[AuctionDataListItem]
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# Scrape Schemas
# ============================================================================

class ScrapeUrlRequest(BaseModel):
    """Request to scrape a single URL."""
    
    url: str = Field(..., description="Auction URL to scrape")
    coin_id: int | None = Field(None, description="Optional coin ID to link")
    reference_type_id: int | None = Field(None, description="Optional reference type for comparables")


class ScrapeBatchRequest(BaseModel):
    """Request to scrape multiple URLs."""
    
    urls: list[str] = Field(..., description="List of auction URLs to scrape")
    coin_id: int | None = Field(None, description="Optional coin ID to link all results")


class ScrapeResultOut(BaseModel):
    """Result from a scrape operation."""
    
    status: Literal["success", "partial", "not_found", "error", "rate_limited"]
    url: str
    house: str | None = None
    error_message: str | None = None
    auction_id: int | None = Field(None, description="Created/updated auction record ID")
    elapsed_ms: int | None = None
    
    # Extracted data summary
    title: str | None = None
    hammer_price: float | None = None
    sold: bool | None = None


class ScrapeUrlResponse(BaseModel):
    """Response from single URL scrape."""
    
    job_id: str
    status: Literal["processing", "completed", "failed"]
    result: ScrapeResultOut | None = None


class ScrapeBatchResponse(BaseModel):
    """Response from batch scrape."""
    
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    total_urls: int
    completed_urls: int = 0
    failed_urls: int = 0


class ScrapeJobStatus(BaseModel):
    """Status of a scrape job."""
    
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    total_urls: int
    completed_urls: int
    failed_urls: int
    results: list[ScrapeResultOut] = []
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None


class DetectHouseResponse(BaseModel):
    """Response from house detection."""
    
    url: str
    house: str | None = None
    supported: bool = False


# ============================================================================
# Price History Schemas
# ============================================================================

class PriceHistoryOut(BaseModel):
    """Price history record output."""
    
    id: int
    reference_type_id: int
    period_date: date
    period_type: str
    min_price: float | None = None
    max_price: float | None = None
    median_price: float | None = None
    mean_price: float | None = None
    comp_count: int = 0
    sold_count: int = 0
    passed_count: int = 0
    median_price_vf_adj: float | None = None
    
    class Config:
        from_attributes = True


class PriceTrendResponse(BaseModel):
    """Price trend data for a reference type."""
    
    reference_type_id: int
    reference_string: str | None = None
    current_median: float | None = None
    price_change_pct: float | None = None
    comp_count: int = 0
    history: list[PriceHistoryOut] = []


# ============================================================================
# Filter Schemas
# ============================================================================

class AuctionFilters(BaseModel):
    """Filters for auction queries."""
    
    auction_house: str | None = None
    coin_id: int | None = None
    reference_type_id: int | None = None
    sold: bool | None = None
    min_price: float | None = None
    max_price: float | None = None
    date_from: date | None = None
    date_to: date | None = None
    search: str | None = None
