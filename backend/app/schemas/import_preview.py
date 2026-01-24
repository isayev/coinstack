"""Pydantic schemas for import preview - URL scraping, NGC lookup, and import confirmation."""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Literal, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class FieldConfidence(str, Enum):
    """Confidence level for parsed fields."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImageSource(str, Enum):
    """Source of coin image."""
    HERITAGE = "heritage"
    CNG = "cng"
    NGC_PHOTOVISION = "ngc_photovision"
    EBAY = "ebay"
    BIDDR = "biddr"
    ROMA = "roma"
    AGORA = "agora"
    UPLOADED = "uploaded"


class ImageType(str, Enum):
    """Type of coin image."""
    OBVERSE = "obverse"
    REVERSE = "reverse"
    SLAB_FRONT = "slab_front"
    SLAB_BACK = "slab_back"
    DETAIL = "detail"
    COMBINED = "combined"  # Obverse and reverse in single image


class MatchReason(str, Enum):
    """Reason for duplicate match."""
    EXACT_SOURCE = "exact_source"    # Same source_id (lot number, cert)
    NGC_CERT = "ngc_cert"            # Same NGC certification number
    PHYSICAL_MATCH = "physical_match" # Similar weight/diameter + ruler


# ============================================================================
# IMAGE SCHEMAS
# ============================================================================

class ImagePreview(BaseModel):
    """Preview data for a coin image."""
    url: str
    source: ImageSource
    image_type: ImageType = ImageType.COMBINED
    thumbnail_url: Optional[str] = None
    local_path: Optional[str] = None  # After download
    width: Optional[int] = None
    height: Optional[int] = None


# ============================================================================
# DUPLICATE DETECTION SCHEMAS
# ============================================================================

class CoinSummary(BaseModel):
    """Summary of a coin for duplicate detection display."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str  # Composed from issuing_authority + denomination
    thumbnail: Optional[str] = None
    source_id: Optional[str] = None  # Original import source ID
    source_type: Optional[str] = None
    match_reason: MatchReason
    match_confidence: Optional[float] = None  # 0-1 for fuzzy matches
    
    # Quick identifiers
    issuing_authority: Optional[str] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    weight_g: Optional[Decimal] = None
    grade: Optional[str] = None


# ============================================================================
# COIN PREVIEW DATA
# ============================================================================

class CoinPreviewData(BaseModel):
    """
    All coin fields for preview/edit before import.
    
    This mirrors CoinCreate but with all fields optional for partial data.
    """
    
    # Classification
    category: Optional[str] = None  # greek, republic, imperial, etc.
    sub_category: Optional[str] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    series: Optional[str] = None
    
    # People
    issuing_authority: Optional[str] = None
    portrait_subject: Optional[str] = None
    status: Optional[str] = None  # "As Caesar", "As Augustus"
    
    # Chronology
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None
    mint_year_start: Optional[int] = None
    mint_year_end: Optional[int] = None
    is_circa: Optional[bool] = None
    dating_certainty: Optional[str] = None
    dating_notes: Optional[str] = None
    
    # Physical attributes
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    diameter_min_mm: Optional[Decimal] = None
    thickness_mm: Optional[Decimal] = None
    die_axis: Optional[int] = None
    is_test_cut: Optional[bool] = None
    
    # Design - Obverse
    obverse_legend: Optional[str] = None
    obverse_legend_expanded: Optional[str] = None
    obverse_description: Optional[str] = None
    obverse_symbols: Optional[str] = None
    
    # Design - Reverse
    reverse_legend: Optional[str] = None
    reverse_legend_expanded: Optional[str] = None
    reverse_description: Optional[str] = None
    reverse_symbols: Optional[str] = None
    exergue: Optional[str] = None
    
    # Mint
    mint_name: Optional[str] = None
    mint_id: Optional[int] = None
    officina: Optional[str] = None
    
    # Grading
    grade_service: Optional[str] = None  # ngc, pcgs, self, dealer
    grade: Optional[str] = None
    strike_quality: Optional[int] = None  # 1-5 for NGC
    surface_quality: Optional[int] = None  # 1-5 for NGC
    certification_number: Optional[str] = None
    eye_appeal: Optional[str] = None
    toning_description: Optional[str] = None
    style_notes: Optional[str] = None
    surface_issues: Optional[List[str]] = None
    
    # Acquisition
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[Decimal] = None
    acquisition_currency: Optional[str] = "USD"
    acquisition_source: Optional[str] = None
    acquisition_url: Optional[str] = None
    
    # Valuation
    estimate_low: Optional[Decimal] = None
    estimate_high: Optional[Decimal] = None
    estimated_value_usd: Optional[Decimal] = None
    
    # Storage
    holder_type: Optional[str] = None
    storage_location: Optional[str] = None
    for_sale: Optional[bool] = False
    
    # Research
    rarity: Optional[str] = None
    rarity_notes: Optional[str] = None
    historical_significance: Optional[str] = None
    personal_notes: Optional[str] = None
    provenance_notes: Optional[str] = None
    
    # Images
    images: List[ImagePreview] = []
    
    # Catalog references (as strings for preview)
    references: List[str] = []  # ["RIC II 756", "BMC 123"]
    
    # Auction-specific data
    auction_house: Optional[str] = None
    sale_name: Optional[str] = None
    lot_number: Optional[str] = None
    auction_date: Optional[date] = None
    hammer_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None  # Including buyer's premium
    currency: Optional[str] = "USD"
    sold: Optional[bool] = None
    
    # Raw description from source
    title: Optional[str] = None
    description: Optional[str] = None


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class URLImportRequest(BaseModel):
    """Request to import from auction URL."""
    url: str = Field(..., description="Auction listing URL")


class NGCImportRequest(BaseModel):
    """Request to import from NGC certificate."""
    cert_number: str = Field(..., description="NGC certification number (7-10 digits)")
    
    @field_validator('cert_number')
    @classmethod
    def validate_cert_format(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Certificate number must contain only digits")
        if not (7 <= len(v) <= 10):
            raise ValueError("Certificate number must be 7-10 digits")
        return v


class DuplicateCheckRequest(BaseModel):
    """Request to check for duplicates."""
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    ngc_cert: Optional[str] = None
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    issuing_authority: Optional[str] = None
    denomination: Optional[str] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ImportPreviewResponse(BaseModel):
    """Response from URL scrape or NGC lookup."""
    
    # Status
    success: bool
    error: Optional[str] = None
    error_code: Optional[str] = None  # rate_limit, not_found, parse_error, unsupported_url, timeout
    retry_after: Optional[int] = None  # Seconds until retry allowed
    manual_entry_suggested: bool = False
    
    # Source info
    source_type: Optional[str] = None  # heritage, cng, ngc, ebay, etc.
    source_id: Optional[str] = None  # Lot number, cert number
    source_url: Optional[str] = None
    
    # Coin data
    coin_data: Optional[CoinPreviewData] = None
    
    # Field-level confidence for UI highlighting
    field_confidence: dict[str, FieldConfidence] = {}
    
    # Duplicate detection results
    similar_coins: List[CoinSummary] = []
    
    # Enrichment availability
    detected_references: List[str] = []  # ["RIC II 756", "BMC 123"]
    enrichment_available: bool = False
    
    # Original data for debugging/reset
    raw_data: Optional[dict] = None


class DuplicateCheckResponse(BaseModel):
    """Response from duplicate check."""
    has_duplicates: bool
    similar_coins: List[CoinSummary] = []


# ============================================================================
# IMPORT CONFIRMATION
# ============================================================================

class CoinImportConfirm(BaseModel):
    """Data for final import confirmation."""
    
    # Edited coin data
    coin_data: CoinPreviewData
    
    # Source tracking
    source_type: str
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    raw_data: Optional[dict] = None
    
    # Price tracking for auction imports
    track_price_history: bool = False
    sold_price_usd: Optional[Decimal] = None
    auction_date: Optional[date] = None
    auction_house: Optional[str] = None
    lot_number: Optional[str] = None
    
    # Duplicate handling
    merge_with_coin_id: Optional[int] = None  # If merging with existing


class ImportConfirmResponse(BaseModel):
    """Response from import confirmation."""
    success: bool
    coin_id: Optional[int] = None
    error: Optional[str] = None
    merged: bool = False  # True if merged with existing coin


# ============================================================================
# BATCH IMPORT
# ============================================================================

class BatchURLImportRequest(BaseModel):
    """Request to batch import multiple URLs."""
    urls: List[str] = Field(..., min_length=1, max_length=50)


class BatchImportStatus(BaseModel):
    """Status of a batch import job."""
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    total: int
    completed: int = 0
    failed: int = 0
    results: List[ImportPreviewResponse] = []


# ============================================================================
# NGC SPECIFIC
# ============================================================================

class NGCCertificateData(BaseModel):
    """Data from NGC certificate lookup."""
    cert_number: str
    grade: Optional[str] = None  # "MS", "AU", "XF", etc.
    strike_score: Optional[str] = None  # "4/5", "5/5"
    surface_score: Optional[str] = None  # "3/5", "4/5"
    numeric_grade: Optional[int] = None  # 1-70 scale
    designation: Optional[str] = None  # "Choice", "Fine Style"
    description: Optional[str] = None  # Coin description from NGC
    
    # Images
    images: List[ImagePreview] = []
    
    # Verification
    verified: bool = False
    verification_url: Optional[str] = None
    
    # Additional metadata
    coin_type: Optional[str] = None
    date_graded: Optional[date] = None
