"""CRUD operations for coins."""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, asc, desc, func, nulls_last, nulls_first
from typing import Optional, List, Dict, Any, Literal
from app.models import Coin
from app.schemas.coin import CoinCreate, CoinUpdate


# Supported sort fields mapping
SORT_FIELDS = {
    "year": Coin.mint_year_start,
    "name": Coin.issuing_authority,
    "denomination": Coin.denomination,
    "metal": Coin.metal,
    "category": Coin.category,
    "grade": Coin.grade,
    "price": Coin.acquisition_price,
    "acquired": Coin.acquisition_date,
    "created": Coin.created_at,
    "value": Coin.estimated_value_usd,
    "weight": Coin.weight_g,
    "rarity": Coin.rarity,
}


def get_coin(db: Session, coin_id: int) -> Optional[Coin]:
    """Get coin by ID."""
    return db.query(Coin).filter(Coin.id == coin_id).first()


def get_coins(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: str = "year",
    sort_dir: Literal["asc", "desc"] = "asc",
) -> tuple[List[Coin], int]:
    """Get coins with pagination, filters, and sorting."""
    query = db.query(Coin)
    
    if filters:
        if "category" in filters and filters["category"]:
            query = query.filter(Coin.category == filters["category"])
        if "sub_category" in filters and filters["sub_category"]:
            query = query.filter(Coin.sub_category == filters["sub_category"])
        if "metal" in filters and filters["metal"]:
            query = query.filter(Coin.metal == filters["metal"])
        if "issuing_authority" in filters and filters["issuing_authority"]:
            query = query.filter(Coin.issuing_authority.ilike(f"%{filters['issuing_authority']}%"))
        if "denomination" in filters and filters["denomination"]:
            query = query.filter(Coin.denomination.ilike(f"%{filters['denomination']}%"))
        if "mint_name" in filters and filters["mint_name"]:
            query = query.filter(Coin.mint_name.ilike(f"%{filters['mint_name']}%"))
        if "storage_location" in filters and filters["storage_location"]:
            # Support prefix matching for storage locations like "Velv1" matching "Velv1-1-1"
            query = query.filter(Coin.storage_location.ilike(f"{filters['storage_location']}%"))
        if "acquisition_price_gte" in filters:
            query = query.filter(Coin.acquisition_price >= filters["acquisition_price_gte"])
        if "acquisition_price_lte" in filters:
            query = query.filter(Coin.acquisition_price <= filters["acquisition_price_lte"])
        # Date range filters
        if "mint_year_gte" in filters:
            query = query.filter(Coin.mint_year_start >= filters["mint_year_gte"])
        if "mint_year_lte" in filters:
            query = query.filter(Coin.mint_year_end <= filters["mint_year_lte"])
        # New filters for refactored schema
        if "is_circa" in filters and filters["is_circa"] is not None:
            query = query.filter(Coin.is_circa == filters["is_circa"])
        if "is_test_cut" in filters and filters["is_test_cut"] is not None:
            query = query.filter(Coin.is_test_cut == filters["is_test_cut"])
        if "rarity" in filters and filters["rarity"]:
            query = query.filter(Coin.rarity == filters["rarity"])
        if "grade" in filters and filters["grade"]:
            query = query.filter(Coin.grade.ilike(f"%{filters['grade']}%"))
        # Ruler search (supports dynasty synonym expansion)
        if "rulers" in filters and filters["rulers"]:
            query = query.filter(Coin.issuing_authority.in_(filters["rulers"]))
    
    total = query.count()
    
    # Apply sorting
    sort_column = SORT_FIELDS.get(sort_by, Coin.mint_year_start)
    if sort_dir == "desc":
        query = query.order_by(nulls_last(desc(sort_column)))
    else:
        query = query.order_by(nulls_last(asc(sort_column)))
    
    # Add secondary sort by ID for stable ordering
    query = query.order_by(Coin.id)
    
    coins = query.offset(skip).limit(limit).all()
    
    return coins, total


def get_coin_ids_sorted(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: str = "year",
    sort_dir: Literal["asc", "desc"] = "asc",
) -> List[int]:
    """Get sorted list of coin IDs matching filters (for navigation)."""
    query = db.query(Coin.id)
    
    if filters:
        if "category" in filters and filters["category"]:
            query = query.filter(Coin.category == filters["category"])
        if "sub_category" in filters and filters["sub_category"]:
            query = query.filter(Coin.sub_category == filters["sub_category"])
        if "metal" in filters and filters["metal"]:
            query = query.filter(Coin.metal == filters["metal"])
        if "issuing_authority" in filters and filters["issuing_authority"]:
            query = query.filter(Coin.issuing_authority.ilike(f"%{filters['issuing_authority']}%"))
        if "denomination" in filters and filters["denomination"]:
            query = query.filter(Coin.denomination.ilike(f"%{filters['denomination']}%"))
        if "mint_name" in filters and filters["mint_name"]:
            query = query.filter(Coin.mint_name.ilike(f"%{filters['mint_name']}%"))
        if "storage_location" in filters and filters["storage_location"]:
            query = query.filter(Coin.storage_location.ilike(f"{filters['storage_location']}%"))
        if "acquisition_price_gte" in filters:
            query = query.filter(Coin.acquisition_price >= filters["acquisition_price_gte"])
        if "acquisition_price_lte" in filters:
            query = query.filter(Coin.acquisition_price <= filters["acquisition_price_lte"])
        if "mint_year_gte" in filters:
            query = query.filter(Coin.mint_year_start >= filters["mint_year_gte"])
        if "mint_year_lte" in filters:
            query = query.filter(Coin.mint_year_end <= filters["mint_year_lte"])
        if "is_circa" in filters and filters["is_circa"] is not None:
            query = query.filter(Coin.is_circa == filters["is_circa"])
        if "is_test_cut" in filters and filters["is_test_cut"] is not None:
            query = query.filter(Coin.is_test_cut == filters["is_test_cut"])
        if "rarity" in filters and filters["rarity"]:
            query = query.filter(Coin.rarity == filters["rarity"])
        if "grade" in filters and filters["grade"]:
            query = query.filter(Coin.grade.ilike(f"%{filters['grade']}%"))
        if "rulers" in filters and filters["rulers"]:
            query = query.filter(Coin.issuing_authority.in_(filters["rulers"]))
    
    # Apply sorting
    sort_column = SORT_FIELDS.get(sort_by, Coin.mint_year_start)
    if sort_dir == "desc":
        query = query.order_by(nulls_last(desc(sort_column)))
    else:
        query = query.order_by(nulls_last(asc(sort_column)))
    
    query = query.order_by(Coin.id)
    
    return [row[0] for row in query.all()]


def create_coin(db: Session, coin: CoinCreate) -> Coin:
    """Create a new coin."""
    # Exclude nested objects that need separate handling
    coin_data = coin.model_dump(exclude={"references", "countermarks", "tags"})
    db_coin = Coin(**coin_data)
    db.add(db_coin)
    db.commit()
    db.refresh(db_coin)
    return db_coin


def update_coin(db: Session, coin_id: int, coin_update: CoinUpdate) -> Optional[Coin]:
    """Update a coin."""
    db_coin = get_coin(db, coin_id)
    if not db_coin:
        return None
    
    update_data = coin_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_coin, field, value)
    
    db.commit()
    db.refresh(db_coin)
    return db_coin


def delete_coin(db: Session, coin_id: int) -> bool:
    """Delete a coin."""
    db_coin = get_coin(db, coin_id)
    if not db_coin:
        return False
    
    db.delete(db_coin)
    db.commit()
    return True
