"""
Stats Router - Collection Dashboard Statistics API

Provides aggregated statistics for the collection dashboard:
- Total coins and portfolio value
- Collection health (data completeness)
- Distribution by category, metal, grade, certification
- Distribution by ruler (issuer)
- Year distribution
- Acquisition timeline
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, extract
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.persistence.orm import CoinModel, CoinImageModel

router = APIRouter(prefix="/api/v2/stats", tags=["stats"])


# --- Response Models ---

class CategoryDistribution(BaseModel):
    category: str
    count: int
    color: str  # CSS variable name


class MetalDistribution(BaseModel):
    metal: str
    symbol: str
    count: int


class GradeDistribution(BaseModel):
    grade: str
    count: int
    numeric: Optional[int] = None


class CertificationDistribution(BaseModel):
    service: str  # "NGC", "PCGS", "Raw"
    count: int


class RulerDistribution(BaseModel):
    ruler: str
    ruler_id: Optional[int] = None
    count: int
    reign_start: Optional[int] = None


class YearDistribution(BaseModel):
    year: int
    count: int


class AcquisitionMonth(BaseModel):
    month: str  # "2024-01"
    count: int
    value_usd: Optional[float] = None


class HealthMetrics(BaseModel):
    overall_pct: int
    total_coins: int
    with_images: int
    with_attribution: int  # has issuer
    with_references: int  # has obverse/reverse legends
    with_provenance: int  # has acquisition_source
    with_values: int  # has acquisition_price


class FilterContext(BaseModel):
    applied_filters: List[dict]
    filtered_count: int
    filtered_value_usd: Optional[float] = None


class RarityDistribution(BaseModel):
    rarity: str
    count: int


class StatsSummaryResponse(BaseModel):
    # Totals
    total_coins: int
    total_value_usd: Optional[float] = None
    
    # Health
    health: HealthMetrics
    
    # Distributions
    by_category: List[CategoryDistribution]
    by_metal: List[MetalDistribution]
    by_grade: List[GradeDistribution]
    by_certification: List[CertificationDistribution]
    by_ruler: List[RulerDistribution]
    by_year: List[YearDistribution]
    by_rarity: List[RulerDistribution] = []  # Typo fix: List[RarityDistribution] actually, but I defined it above.
                                             # Wait, I should use RarityDistribution
    by_rarity: List[RarityDistribution] = []

    # Acquisition timeline
    acquisitions: List[AcquisitionMonth]
    
    # Filter context (only present when filters applied)
    filter_context: Optional[FilterContext] = None


# --- Category Color Mapping ---

CATEGORY_COLORS = {
    "imperial": "--cat-imperial",
    "republic": "--cat-republic",
    "provincial": "--cat-provincial",
    "greek": "--cat-greek",
    "byzantine": "--cat-byzantine",
    "celtic": "--cat-other",
    "judaean": "--cat-other",
    "other": "--cat-other",
}

# --- Metal Symbol Mapping ---

METAL_SYMBOLS = {
    "gold": "Au",
    "silver": "Ag",
    "bronze": "AE",
    "copper": "Cu",
    "billon": "BI",
    "electrum": "EL",
    "orichalcum": "OR",
    "brass": "BR",
    "lead": "PB",
    "ae": "AE",
    "ar": "Ag",
    "au": "Au",
}

# --- Grade Numeric Mapping ---

GRADE_NUMERIC = {
    "P": 1, "Poor": 1,
    "FR": 2, "Fair": 2,
    "AG": 3,
    "G": 6, "Good": 6,
    "VG": 10,
    "F": 15, "Fine": 15,
    "VF": 30,
    "EF": 45, "XF": 45,
    "AU": 55,
    "MS": 65, "Mint State": 65,
    "FDC": 70,
}


def _apply_filters(query, filters: dict):
    """Apply optional filters to query."""
    if filters.get("category"):
        query = query.filter(func.lower(CoinModel.category) == filters["category"].lower())
    if filters.get("metal"):
        query = query.filter(func.lower(CoinModel.metal) == filters["metal"].lower())
    if filters.get("grade"):
        query = query.filter(func.upper(CoinModel.grade).like(f"%{filters['grade'].upper()}%"))
    if filters.get("issuer"):
        query = query.filter(CoinModel.issuer.ilike(f"%{filters['issuer']}%"))
    # Use "is not None" so year_gte=0 or year_lte=0 (BC/AD boundary) is applied, not treated as falsy
    if filters.get("year_gte") is not None:
        query = query.filter(CoinModel.year_start >= filters["year_gte"])
    if filters.get("year_lte") is not None:
        query = query.filter(CoinModel.year_start <= filters["year_lte"])
    return query


@router.get("/summary", response_model=StatsSummaryResponse)
async def get_stats_summary(
    db: Session = Depends(get_db),
    # Optional filters
    category: Optional[str] = Query(None, description="Filter by category"),
    metal: Optional[str] = Query(None, description="Filter by metal"),
    grade: Optional[str] = Query(None, description="Filter by grade"),
    issuer: Optional[str] = Query(None, description="Filter by issuer/ruler"),
    year_gte: Optional[int] = Query(None, description="Minimum year"),
    year_lte: Optional[int] = Query(None, description="Maximum year"),
):
    """
    Get comprehensive collection statistics for the dashboard.
    
    Returns aggregated data including:
    - Total coins and portfolio value
    - Collection health metrics (data completeness)
    - Distributions by category, metal, grade, certification, ruler, year
    - Acquisition timeline (monthly)
    
    All distributions can be filtered by optional query parameters.
    """
    
    filters = {
        "category": category,
        "metal": metal,
        "grade": grade,
        "issuer": issuer,
        "year_gte": year_gte,
        "year_lte": year_lte,
    }
    has_filters = any(v is not None for v in filters.values())
    
    # Base query
    base_query = db.query(CoinModel)
    if has_filters:
        base_query = _apply_filters(base_query, filters)
    
    # --- Total Count and Value ---
    total_count = base_query.count()
    
    total_value_result = base_query.with_entities(
        func.sum(CoinModel.acquisition_price)
    ).scalar()
    total_value = float(total_value_result) if total_value_result else None
    
    # --- Health Metrics (always computed on full collection) ---
    full_count = db.query(CoinModel).count()
    
    # Count coins with images (subquery)
    coins_with_images = db.query(CoinImageModel.coin_id).distinct().count()
    
    # Count coins with various attributes
    with_attribution = db.query(CoinModel).filter(
        CoinModel.issuer.isnot(None),
        CoinModel.issuer != "",
        CoinModel.issuer != "Unknown"
    ).count()
    
    with_references = db.query(CoinModel).filter(
        and_(
            CoinModel.obverse_legend.isnot(None),
            CoinModel.obverse_legend != ""
        )
    ).count()
    
    with_provenance = db.query(CoinModel).filter(
        and_(
            CoinModel.acquisition_source.isnot(None),
            CoinModel.acquisition_source != ""
        )
    ).count()
    
    with_values = db.query(CoinModel).filter(
        CoinModel.acquisition_price.isnot(None),
        CoinModel.acquisition_price > 0
    ).count()
    
    # Calculate overall health percentage
    if full_count > 0:
        # Weight: images=30%, attribution=25%, references=20%, provenance=15%, values=10%
        health_score = (
            (coins_with_images / full_count * 30) +
            (with_attribution / full_count * 25) +
            (with_references / full_count * 20) +
            (with_provenance / full_count * 15) +
            (with_values / full_count * 10)
        )
        overall_pct = int(health_score)
    else:
        overall_pct = 0
    
    health = HealthMetrics(
        overall_pct=overall_pct,
        total_coins=full_count,
        with_images=coins_with_images,
        with_attribution=with_attribution,
        with_references=with_references,
        with_provenance=with_provenance,
        with_values=with_values,
    )
    
    # --- Category Distribution ---
    category_query = base_query.with_entities(
        func.lower(CoinModel.category).label("category"),
        func.count().label("count")
    ).group_by(func.lower(CoinModel.category)).order_by(func.count().desc())
    
    by_category = [
        CategoryDistribution(
            category=row.category or "unknown",
            count=row.count,
            color=CATEGORY_COLORS.get(row.category.lower() if row.category else "other", "--cat-other")
        )
        for row in category_query.all()
    ]
    
    # --- Metal Distribution ---
    metal_query = base_query.with_entities(
        func.lower(CoinModel.metal).label("metal"),
        func.count().label("count")
    ).group_by(func.lower(CoinModel.metal)).order_by(func.count().desc())
    
    by_metal = [
        MetalDistribution(
            metal=row.metal or "unknown",
            symbol=METAL_SYMBOLS.get(row.metal.lower() if row.metal else "", "??"),
            count=row.count
        )
        for row in metal_query.all()
    ]
    
    # --- Grade Distribution ---
    grade_query = base_query.with_entities(
        CoinModel.grade,
        func.count().label("count")
    ).filter(CoinModel.grade.isnot(None)).group_by(CoinModel.grade).order_by(func.count().desc())
    
    by_grade = []
    for row in grade_query.all():
        grade_str = row.grade or "Unknown"
        # Extract base grade (e.g., "VF" from "VF 35")
        base_grade = grade_str.split()[0].upper() if grade_str else "Unknown"
        numeric = GRADE_NUMERIC.get(base_grade)
        by_grade.append(GradeDistribution(
            grade=grade_str,
            count=row.count,
            numeric=numeric
        ))
    
    # --- Certification Distribution ---
    # Count by grade_service (NGC, PCGS, or null/Raw)
    cert_query = base_query.with_entities(
        case(
            (CoinModel.grade_service.isnot(None), func.upper(CoinModel.grade_service)),
            else_="Raw"
        ).label("service"),
        func.count().label("count")
    ).group_by("service").order_by(func.count().desc())
    
    by_certification = [
        CertificationDistribution(service=row.service, count=row.count)
        for row in cert_query.all()
    ]
    
    # --- Ruler Distribution ---
    ruler_query = base_query.with_entities(
        CoinModel.issuer,
        CoinModel.issuer_id,
        func.count().label("count"),
        func.min(CoinModel.year_start).label("reign_start")
    ).filter(
        CoinModel.issuer.isnot(None),
        CoinModel.issuer != "",
        CoinModel.issuer != "Unknown"
    ).group_by(
        CoinModel.issuer, CoinModel.issuer_id
    ).order_by(func.count().desc()).limit(20)
    
    by_ruler = [
        RulerDistribution(
            ruler=row.issuer,
            ruler_id=row.issuer_id,
            count=row.count,
            reign_start=row.reign_start
        )
        for row in ruler_query.all()
    ]
    
    # --- Year Distribution ---
    year_query = base_query.with_entities(
        CoinModel.year_start.label("year"),
        func.count().label("count")
    ).filter(
        CoinModel.year_start.isnot(None)
    ).group_by(CoinModel.year_start).order_by(CoinModel.year_start)
    
    by_year = [
        YearDistribution(year=row.year, count=row.count)
        for row in year_query.all()
    ]
    
    # --- Acquisition Timeline (last 24 months) ---
    # Group by month
    acq_query = base_query.with_entities(
        func.strftime("%Y-%m", CoinModel.acquisition_date).label("month"),
        func.count().label("count"),
        func.sum(CoinModel.acquisition_price).label("value")
    ).filter(
        CoinModel.acquisition_date.isnot(None)
    ).group_by("month").order_by("month").limit(24)
    
    acquisitions = [
        AcquisitionMonth(
            month=row.month,
            count=row.count,
            value_usd=float(row.value) if row.value else None
        )
        for row in acq_query.all()
    ]
    
    # --- Rarity Distribution ---
    rarity_query = base_query.with_entities(
        CoinModel.rarity,
        func.count().label("count")
    ).filter(CoinModel.rarity.isnot(None), CoinModel.rarity != "").group_by(CoinModel.rarity).order_by(func.count().desc())

    by_rarity = [
        {"rarity": row.rarity, "count": row.count}
        for row in rarity_query.all()
    ]

    # --- Filter Context ---
    filter_context = None
    if has_filters:
        applied = [{"field": k, "value": v} for k, v in filters.items() if v is not None]
        filter_context = FilterContext(
            applied_filters=applied,
            filtered_count=total_count,
            filtered_value_usd=total_value
        )
    
    return StatsSummaryResponse(
        total_coins=total_count,
        total_value_usd=total_value,
        health=health,
        by_category=by_category,
        by_metal=by_metal,
        by_grade=by_grade,
        by_certification=by_certification,
        by_ruler=by_ruler,
        by_year=by_year,
        by_rarity=by_rarity,  # New field
        acquisitions=acquisitions,
        filter_context=filter_context,
    )