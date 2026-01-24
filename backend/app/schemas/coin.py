"""Pydantic schemas for coins - Clean refactored schema."""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal
from app.models.coin import Category, Metal, Orientation, DatingCertainty, GradeService, HolderType, Rarity
from app.models.reference import ReferencePosition


# ============================================================================
# REFERENCE TYPE SCHEMAS
# ============================================================================

class ReferenceTypeOut(BaseModel):
    """Reference type output schema - catalog type data."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    system: str
    local_ref: str
    volume: Optional[str] = None
    number: Optional[str] = None
    edition: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    lookup_status: Optional[str] = None
    lookup_confidence: Optional[Decimal] = None


class CoinReferenceOut(BaseModel):
    """Coin reference output schema - links to ReferenceType."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    reference_type_id: int
    is_primary: bool
    plate_coin: bool
    position: Optional[str] = None
    variant_notes: Optional[str] = None
    page: Optional[str] = None
    plate: Optional[str] = None
    note_number: Optional[str] = None
    
    # Nested reference type
    reference_type: Optional[ReferenceTypeOut] = None


class CoinReferenceCreate(BaseModel):
    """Schema for creating a coin reference."""
    reference_type_id: int
    is_primary: bool = False
    plate_coin: bool = False
    position: Optional[str] = "both"
    variant_notes: Optional[str] = None
    page: Optional[str] = None
    plate: Optional[str] = None
    note_number: Optional[str] = None


# ============================================================================
# IMAGE SCHEMAS
# ============================================================================

class CoinImageOut(BaseModel):
    """Coin image output schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    image_type: str
    file_path: str
    is_primary: bool


# ============================================================================
# COUNTERMARK SCHEMAS
# ============================================================================

class CountermarkOut(BaseModel):
    """Countermark output schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    countermark_type: str
    description: str
    expanded: Optional[str] = None
    placement: str
    position: Optional[str] = None
    condition: Optional[str] = None
    authority: Optional[str] = None
    date_applied: Optional[str] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None


class CountermarkCreate(BaseModel):
    """Schema for creating a countermark."""
    countermark_type: str
    description: str
    expanded: Optional[str] = None
    placement: str
    position: Optional[str] = None
    condition: str = "clear"
    authority: Optional[str] = None
    date_applied: Optional[str] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None


# ============================================================================
# AUCTION DATA SCHEMAS
# ============================================================================

class AuctionDataOut(BaseModel):
    """Auction data output schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    auction_house: str
    sale_name: Optional[str] = None
    lot_number: Optional[str] = None
    auction_date: Optional[date] = None
    url: str
    estimate_low: Optional[Decimal] = None
    estimate_high: Optional[Decimal] = None
    hammer_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    currency: str = "USD"
    sold: bool = True
    grade: Optional[str] = None
    title: Optional[str] = None
    primary_photo_url: Optional[str] = None


class AuctionDataCreate(BaseModel):
    """Schema for creating auction data."""
    auction_house: str
    sale_name: Optional[str] = None
    lot_number: Optional[str] = None
    auction_date: Optional[date] = None
    url: str
    estimate_low: Optional[Decimal] = None
    estimate_high: Optional[Decimal] = None
    hammer_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    currency: str = "USD"
    sold: bool = True
    grade: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    primary_photo_url: Optional[str] = None


# ============================================================================
# PROVENANCE SCHEMAS
# ============================================================================

class ProvenanceEventOut(BaseModel):
    """Provenance event output schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_type: str
    event_date: Optional[date] = None
    auction_house: Optional[str] = None
    sale_series: Optional[str] = None
    sale_number: Optional[str] = None
    lot_number: Optional[str] = None
    catalog_reference: Optional[str] = None
    hammer_price: Optional[Decimal] = None
    buyers_premium_pct: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    currency: Optional[str] = None
    dealer_name: Optional[str] = None
    collection_name: Optional[str] = None
    url: Optional[str] = None
    receipt_available: bool = False
    notes: Optional[str] = None


class ProvenanceEventCreate(BaseModel):
    """Schema for creating a provenance event."""
    event_type: str
    event_date: Optional[date] = None
    auction_house: Optional[str] = None
    sale_series: Optional[str] = None
    sale_number: Optional[str] = None
    lot_number: Optional[str] = None
    catalog_reference: Optional[str] = None
    hammer_price: Optional[Decimal] = None
    buyers_premium_pct: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    currency: Optional[str] = None
    dealer_name: Optional[str] = None
    collection_name: Optional[str] = None
    url: Optional[str] = None
    receipt_available: bool = False
    notes: Optional[str] = None


# ============================================================================
# COIN LIST/DETAIL SCHEMAS
# ============================================================================

class CoinListItem(BaseModel):
    """Compact representation for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    category: Category
    sub_category: Optional[str] = None
    denomination: str
    metal: Metal
    issuing_authority: str
    portrait_subject: Optional[str] = None
    mint_name: Optional[str] = None
    mint_year_start: Optional[int] = None
    mint_year_end: Optional[int] = None
    is_circa: Optional[bool] = None
    is_test_cut: Optional[bool] = None
    rarity: Optional[Rarity] = None
    grade: Optional[str] = None
    acquisition_price: Optional[Decimal] = None
    estimated_value_usd: Optional[Decimal] = None
    storage_location: Optional[str] = None
    primary_image: Optional[str] = None


class CoinDetail(BaseModel):
    """Full representation with all relations."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Classification
    category: Category
    sub_category: Optional[str] = None
    denomination: str
    metal: Metal
    series: Optional[str] = None
    
    # People
    issuing_authority: str
    portrait_subject: Optional[str] = None
    status: Optional[str] = None
    
    # Chronology
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None
    mint_year_start: Optional[int] = None
    mint_year_end: Optional[int] = None
    is_circa: bool = False
    dating_certainty: Optional[str] = None
    dating_notes: Optional[str] = None
    
    # Physical
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    diameter_min_mm: Optional[Decimal] = None
    thickness_mm: Optional[Decimal] = None
    die_axis: Optional[int] = None
    orientation: Optional[str] = None
    is_test_cut: bool = False
    
    # Design: Obverse
    obverse_legend: Optional[str] = None
    obverse_legend_expanded: Optional[str] = None
    obverse_description: Optional[str] = None
    obverse_symbols: Optional[str] = None
    
    # Design: Reverse
    reverse_legend: Optional[str] = None
    reverse_legend_expanded: Optional[str] = None
    reverse_description: Optional[str] = None
    reverse_symbols: Optional[str] = None
    exergue: Optional[str] = None
    
    # Mint
    mint_id: Optional[int] = None
    mint_name: Optional[str] = None
    officina: Optional[str] = None
    
    # Grading
    grade_service: Optional[str] = None
    grade: Optional[str] = None
    strike_quality: Optional[int] = None
    surface_quality: Optional[int] = None
    certification_number: Optional[str] = None
    eye_appeal: Optional[str] = None
    toning_description: Optional[str] = None
    style_notes: Optional[str] = None
    
    # Acquisition
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[Decimal] = None
    acquisition_currency: Optional[str] = None
    acquisition_source: Optional[str] = None
    acquisition_url: Optional[str] = None
    
    # Valuation
    estimate_low: Optional[Decimal] = None
    estimate_high: Optional[Decimal] = None
    estimated_value_usd: Optional[Decimal] = None
    insured_value: Optional[Decimal] = None
    
    # Storage
    holder_type: Optional[str] = None
    storage_location: Optional[str] = None
    for_sale: bool = False
    asking_price: Optional[Decimal] = None
    
    # Research
    rarity: Optional[str] = None
    rarity_notes: Optional[str] = None
    historical_significance: Optional[str] = None
    die_match_notes: Optional[str] = None
    personal_notes: Optional[str] = None
    provenance_notes: Optional[str] = None
    
    # Die study
    die_study_obverse_id: Optional[int] = None
    die_study_reverse_id: Optional[int] = None
    die_study_group: Optional[str] = None
    
    # Relations
    references: List[CoinReferenceOut] = []
    images: List[CoinImageOut] = []
    tags: List[str] = []
    countermarks: List[CountermarkOut] = []
    provenance_events: List[ProvenanceEventOut] = []
    auction_data: List[AuctionDataOut] = []


# ============================================================================
# COIN CREATE/UPDATE SCHEMAS
# ============================================================================

class CoinCreate(BaseModel):
    """Schema for creating a coin."""
    # Required
    category: Category
    denomination: str
    metal: Metal
    issuing_authority: str
    
    # Classification
    sub_category: Optional[str] = None
    series: Optional[str] = None
    
    # People
    portrait_subject: Optional[str] = None
    status: Optional[str] = None
    
    # Chronology
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None
    mint_year_start: Optional[int] = None
    mint_year_end: Optional[int] = None
    is_circa: bool = False
    dating_certainty: Optional[str] = None
    dating_notes: Optional[str] = None
    
    # Physical
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    diameter_min_mm: Optional[Decimal] = None
    thickness_mm: Optional[Decimal] = None
    die_axis: Optional[int] = Field(None, ge=0, le=12)
    orientation: Optional[str] = None
    is_test_cut: bool = False
    
    # Design
    obverse_legend: Optional[str] = None
    obverse_legend_expanded: Optional[str] = None
    obverse_description: Optional[str] = None
    obverse_symbols: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_legend_expanded: Optional[str] = None
    reverse_description: Optional[str] = None
    reverse_symbols: Optional[str] = None
    exergue: Optional[str] = None
    
    # Mint
    mint_id: Optional[int] = None
    officina: Optional[str] = None
    
    # Grading
    grade_service: Optional[str] = None
    grade: Optional[str] = None
    strike_quality: Optional[int] = None
    surface_quality: Optional[int] = None
    certification_number: Optional[str] = None
    eye_appeal: Optional[str] = None
    toning_description: Optional[str] = None
    style_notes: Optional[str] = None
    
    # Acquisition
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[Decimal] = None
    acquisition_currency: str = "USD"
    acquisition_source: Optional[str] = None
    acquisition_url: Optional[str] = None
    
    # Valuation
    estimate_low: Optional[Decimal] = None
    estimate_high: Optional[Decimal] = None
    estimated_value_usd: Optional[Decimal] = None
    insured_value: Optional[Decimal] = None
    
    # Storage
    holder_type: Optional[str] = None
    storage_location: Optional[str] = None
    for_sale: bool = False
    asking_price: Optional[Decimal] = None
    
    # Research
    rarity: Optional[str] = None
    rarity_notes: Optional[str] = None
    historical_significance: Optional[str] = None
    die_match_notes: Optional[str] = None
    personal_notes: Optional[str] = None
    provenance_notes: Optional[str] = None
    
    # Die study
    die_study_obverse_id: Optional[int] = None
    die_study_reverse_id: Optional[int] = None
    die_study_group: Optional[str] = None
    
    # Nested creates
    references: Optional[List[CoinReferenceCreate]] = []
    countermarks: Optional[List[CountermarkCreate]] = []
    tags: Optional[List[str]] = []


class CoinUpdate(BaseModel):
    """Schema for updating (all fields optional)."""
    # Classification
    category: Optional[Category] = None
    sub_category: Optional[str] = None
    denomination: Optional[str] = None
    metal: Optional[Metal] = None
    series: Optional[str] = None
    
    # People
    issuing_authority: Optional[str] = None
    portrait_subject: Optional[str] = None
    status: Optional[str] = None
    
    # Chronology
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None
    mint_year_start: Optional[int] = None
    mint_year_end: Optional[int] = None
    is_circa: Optional[bool] = None
    dating_certainty: Optional[str] = None
    dating_notes: Optional[str] = None
    
    # Physical
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    diameter_min_mm: Optional[Decimal] = None
    thickness_mm: Optional[Decimal] = None
    die_axis: Optional[int] = Field(None, ge=0, le=12)
    orientation: Optional[str] = None
    is_test_cut: Optional[bool] = None
    
    # Design
    obverse_legend: Optional[str] = None
    obverse_legend_expanded: Optional[str] = None
    obverse_description: Optional[str] = None
    obverse_symbols: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_legend_expanded: Optional[str] = None
    reverse_description: Optional[str] = None
    reverse_symbols: Optional[str] = None
    exergue: Optional[str] = None
    
    # Mint
    mint_id: Optional[int] = None
    officina: Optional[str] = None
    
    # Grading
    grade_service: Optional[str] = None
    grade: Optional[str] = None
    strike_quality: Optional[int] = None
    surface_quality: Optional[int] = None
    certification_number: Optional[str] = None
    eye_appeal: Optional[str] = None
    toning_description: Optional[str] = None
    style_notes: Optional[str] = None
    
    # Acquisition
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[Decimal] = None
    acquisition_currency: Optional[str] = None
    acquisition_source: Optional[str] = None
    acquisition_url: Optional[str] = None
    
    # Valuation
    estimate_low: Optional[Decimal] = None
    estimate_high: Optional[Decimal] = None
    estimated_value_usd: Optional[Decimal] = None
    insured_value: Optional[Decimal] = None
    
    # Storage
    holder_type: Optional[str] = None
    storage_location: Optional[str] = None
    for_sale: Optional[bool] = None
    asking_price: Optional[Decimal] = None
    
    # Research
    rarity: Optional[str] = None
    rarity_notes: Optional[str] = None
    historical_significance: Optional[str] = None
    die_match_notes: Optional[str] = None
    personal_notes: Optional[str] = None
    provenance_notes: Optional[str] = None
    
    # Die study
    die_study_obverse_id: Optional[int] = None
    die_study_reverse_id: Optional[int] = None
    die_study_group: Optional[str] = None


# ============================================================================
# PAGINATION
# ============================================================================

class PaginatedCoins(BaseModel):
    """Paginated coins response."""
    items: List[CoinListItem]
    total: int
    page: int
    per_page: int
    pages: int


# ============================================================================
# LEGEND EXPANSION SCHEMAS
# ============================================================================

class LegendExpansionRequest(BaseModel):
    """Request to expand a legend."""
    legend: str
    use_llm_fallback: bool = True


class LegendExpansionResponse(BaseModel):
    """Legend expansion result."""
    original: str
    expanded: str
    method: str  # "dictionary", "llm", "partial"
    confidence: float
    unknown_terms: List[str]
    expansion_map: dict
