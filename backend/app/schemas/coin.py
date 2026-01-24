"""Pydantic schemas for coins."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.coin import Category, Metal


class CoinReferenceOut(BaseModel):
    """Coin reference output schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    system: str
    volume: Optional[str]
    number: str
    is_primary: bool
    plate_coin: bool


class CoinImageOut(BaseModel):
    """Coin image output schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    image_type: str
    file_path: str
    is_primary: bool


class CoinListItem(BaseModel):
    """Compact representation for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    category: Category
    denomination: str
    metal: Metal
    issuing_authority: str
    portrait_subject: Optional[str] = None
    mint_name: Optional[str] = None
    grade: Optional[str] = None
    acquisition_price: Optional[Decimal] = None
    storage_location: Optional[str] = None
    primary_image: Optional[str] = None


class CoinDetail(BaseModel):
    """Full representation with all relations."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    category: Category
    denomination: str
    metal: Metal
    series: Optional[str] = None
    issuing_authority: str
    portrait_subject: Optional[str] = None
    status: Optional[str] = None
    
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None
    mint_year_start: Optional[int] = None
    mint_year_end: Optional[int] = None
    
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    diameter_min_mm: Optional[Decimal] = None
    thickness_mm: Optional[Decimal] = None
    die_axis: Optional[int] = None
    
    obverse_legend: Optional[str] = None
    obverse_legend_expanded: Optional[str] = None
    obverse_description: Optional[str] = None
    obverse_symbols: Optional[str] = None
    
    reverse_legend: Optional[str] = None
    reverse_legend_expanded: Optional[str] = None
    reverse_description: Optional[str] = None
    reverse_symbols: Optional[str] = None
    exergue: Optional[str] = None
    
    mint_id: Optional[int] = None
    mint_name: Optional[str] = None
    
    grade_service: Optional[str] = None
    grade: Optional[str] = None
    strike_quality: Optional[int] = None
    surface_quality: Optional[int] = None
    certification_number: Optional[str] = None
    
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[Decimal] = None
    acquisition_currency: Optional[str] = None
    acquisition_source: Optional[str] = None
    acquisition_url: Optional[str] = None
    
    storage_location: Optional[str] = None
    for_sale: bool = False
    asking_price: Optional[Decimal] = None
    
    rarity: Optional[str] = None
    rarity_notes: Optional[str] = None
    historical_significance: Optional[str] = None
    personal_notes: Optional[str] = None
    
    references: List[CoinReferenceOut] = []
    images: List[CoinImageOut] = []
    tags: List[str] = []


class CoinCreate(BaseModel):
    """Schema for creating a coin."""
    category: Category
    denomination: str
    metal: Metal
    issuing_authority: str
    
    series: Optional[str] = None
    portrait_subject: Optional[str] = None
    status: Optional[str] = None
    
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None
    mint_year_start: Optional[int] = None
    mint_year_end: Optional[int] = None
    
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    diameter_min_mm: Optional[Decimal] = None
    thickness_mm: Optional[Decimal] = None
    die_axis: Optional[int] = None
    
    obverse_legend: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_description: Optional[str] = None
    exergue: Optional[str] = None
    
    mint_id: Optional[int] = None
    
    grade: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[Decimal] = None
    acquisition_currency: str = "USD"
    acquisition_source: Optional[str] = None
    
    storage_location: Optional[str] = None
    
    references: Optional[List[dict]] = []
    tags: Optional[List[str]] = []


class CoinUpdate(BaseModel):
    """Schema for updating (all fields optional)."""
    category: Optional[Category] = None
    denomination: Optional[str] = None
    metal: Optional[Metal] = None
    issuing_authority: Optional[str] = None
    
    series: Optional[str] = None
    portrait_subject: Optional[str] = None
    status: Optional[str] = None
    
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None
    
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    
    obverse_legend: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_description: Optional[str] = None
    
    grade: Optional[str] = None
    acquisition_price: Optional[Decimal] = None
    storage_location: Optional[str] = None
    
    personal_notes: Optional[str] = None


class PaginatedCoins(BaseModel):
    """Paginated coins response."""
    items: List[CoinListItem]
    total: int
    page: int
    per_page: int
    pages: int
