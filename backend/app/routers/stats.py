"""Statistics API router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from decimal import Decimal
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models.coin import Coin, Category, Metal

router = APIRouter(prefix="/stats", tags=["statistics"])


class CategoryStat(BaseModel):
    """Category statistics."""
    category: str
    count: int
    total_value: float


class MetalStat(BaseModel):
    """Metal statistics."""
    metal: str
    count: int
    total_value: float
    total_weight: float = 0.0


class RulerStat(BaseModel):
    """Ruler/issuing authority statistics."""
    ruler: str
    count: int
    total_value: float


class StorageStat(BaseModel):
    """Storage location statistics."""
    location: str
    count: int


class PriceRangeStat(BaseModel):
    """Price range distribution."""
    range: str
    count: int


class GradeStat(BaseModel):
    """Grade statistics."""
    tier: str
    count: int


class RarityStat(BaseModel):
    """Rarity statistics."""
    rarity: str
    count: int


class YearRange(BaseModel):
    """Year range."""
    min: int | None
    max: int | None


class CollectionStats(BaseModel):
    """Complete collection statistics."""
    total_coins: int
    total_value: float
    average_price: float
    median_price: float
    highest_value_coin: float
    lowest_value_coin: float
    by_category: List[CategoryStat]
    by_metal: List[MetalStat]
    top_rulers: List[RulerStat]
    by_storage: List[StorageStat]
    price_distribution: List[PriceRangeStat]
    # New fields for sidebar filters
    metal_counts: dict
    category_counts: dict
    grade_counts: dict
    rarity_counts: dict
    year_range: YearRange


@router.get("", response_model=CollectionStats)
async def get_collection_stats(db: Session = Depends(get_db)):
    """Get comprehensive collection statistics."""
    
    # Basic counts and totals
    total_coins = db.query(func.count(Coin.id)).scalar() or 0
    total_value = db.query(func.sum(Coin.acquisition_price)).scalar() or Decimal(0)
    avg_price = db.query(func.avg(Coin.acquisition_price)).scalar() or Decimal(0)
    
    # Get all prices for median calculation
    prices = db.query(Coin.acquisition_price).filter(
        Coin.acquisition_price.isnot(None)
    ).order_by(Coin.acquisition_price).all()
    prices = [float(p[0]) for p in prices if p[0]]
    
    median_price = 0.0
    if prices:
        n = len(prices)
        median_price = prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) / 2
    
    # Highest and lowest
    highest = db.query(func.max(Coin.acquisition_price)).scalar() or Decimal(0)
    lowest = db.query(func.min(Coin.acquisition_price)).filter(
        Coin.acquisition_price > 0
    ).scalar() or Decimal(0)
    
    # By category
    category_stats = db.query(
        Coin.category,
        func.count(Coin.id).label("count"),
        func.coalesce(func.sum(Coin.acquisition_price), 0).label("total")
    ).group_by(Coin.category).all()
    
    by_category = [
        CategoryStat(
            category=stat[0].value if stat[0] else "unknown",
            count=stat[1],
            total_value=float(stat[2] or 0)
        )
        for stat in category_stats
    ]
    
    # By metal (with weight)
    metal_stats = db.query(
        Coin.metal,
        func.count(Coin.id).label("count"),
        func.coalesce(func.sum(Coin.acquisition_price), 0).label("total"),
        func.coalesce(func.sum(Coin.weight_g), 0).label("weight")
    ).group_by(Coin.metal).all()
    
    by_metal = [
        MetalStat(
            metal=stat[0].value if stat[0] else "unknown",
            count=stat[1],
            total_value=float(stat[2] or 0),
            total_weight=float(stat[3] or 0)
        )
        for stat in metal_stats
    ]
    
    # Top rulers by count
    ruler_stats = db.query(
        Coin.issuing_authority,
        func.count(Coin.id).label("count"),
        func.coalesce(func.sum(Coin.acquisition_price), 0).label("total")
    ).group_by(Coin.issuing_authority).order_by(
        func.count(Coin.id).desc()
    ).limit(10).all()
    
    top_rulers = [
        RulerStat(
            ruler=stat[0] or "Unknown",
            count=stat[1],
            total_value=float(stat[2] or 0)
        )
        for stat in ruler_stats
    ]
    
    # By storage location
    storage_stats = db.query(
        Coin.storage_location,
        func.count(Coin.id).label("count")
    ).group_by(Coin.storage_location).order_by(
        func.count(Coin.id).desc()
    ).all()
    
    by_storage = [
        StorageStat(
            location=stat[0] or "Unassigned",
            count=stat[1]
        )
        for stat in storage_stats
    ]
    
    # Price distribution (buckets)
    price_ranges = [
        ("$0-50", 0, 50),
        ("$50-100", 50, 100),
        ("$100-200", 100, 200),
        ("$200-500", 200, 500),
        ("$500-1000", 500, 1000),
        ("$1000+", 1000, 999999),
    ]
    
    price_distribution = []
    for label, low, high in price_ranges:
        count = db.query(func.count(Coin.id)).filter(
            Coin.acquisition_price >= low,
            Coin.acquisition_price < high
        ).scalar() or 0
        price_distribution.append(PriceRangeStat(range=label, count=count))
    
    # Build count dictionaries for sidebar filters
    metal_counts = {stat.metal: stat.count for stat in by_metal}
    category_counts = {stat.category: stat.count for stat in by_category}
    
    # Count by grade (parse grade string to tier)
    grade_counts = {}
    grade_query = db.query(Coin.grade, func.count(Coin.id)).group_by(Coin.grade).all()
    for grade, count in grade_query:
        if grade:
            # Map grade to tier
            g = grade.upper().replace(" ", "")
            tier = "other"
            if any(x in g for x in ["P", "FR", "AG"]):
                tier = "poor"
            elif any(x in g for x in ["G", "VG"]) and "AG" not in g:
                tier = "good"
            elif any(x in g for x in ["F", "VF"]) and "EF" not in g:
                tier = "fine"
            elif any(x in g for x in ["EF", "XF"]):
                tier = "ef"
            elif "AU" in g and "AUG" not in g:
                tier = "au"
            elif any(x in g for x in ["MS", "FDC", "UNC"]):
                tier = "ms"
            grade_counts[tier] = grade_counts.get(tier, 0) + count
    
    # Count by rarity
    rarity_counts = {}
    rarity_query = db.query(Coin.rarity, func.count(Coin.id)).group_by(Coin.rarity).all()
    for rarity, count in rarity_query:
        if rarity:
            rarity_counts[rarity.value] = count
    
    # Year range
    min_year = db.query(func.min(Coin.mint_year_start)).scalar()
    max_year = db.query(func.max(Coin.mint_year_end)).scalar()
    if max_year is None:
        max_year = db.query(func.max(Coin.mint_year_start)).scalar()
    
    return CollectionStats(
        total_coins=total_coins,
        total_value=float(total_value),
        average_price=float(avg_price),
        median_price=median_price,
        highest_value_coin=float(highest),
        lowest_value_coin=float(lowest),
        by_category=by_category,
        by_metal=by_metal,
        top_rulers=top_rulers,
        by_storage=by_storage,
        price_distribution=price_distribution,
        metal_counts=metal_counts,
        category_counts=category_counts,
        grade_counts=grade_counts,
        rarity_counts=rarity_counts,
        year_range=YearRange(min=min_year, max=max_year),
    )
