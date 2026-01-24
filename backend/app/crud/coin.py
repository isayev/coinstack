"""CRUD operations for coins."""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List, Dict, Any
from app.models import Coin
from app.schemas.coin import CoinCreate, CoinUpdate


def get_coin(db: Session, coin_id: int) -> Optional[Coin]:
    """Get coin by ID."""
    return db.query(Coin).filter(Coin.id == coin_id).first()


def get_coins(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None,
) -> tuple[List[Coin], int]:
    """Get coins with pagination and filters."""
    query = db.query(Coin)
    
    if filters:
        if "category" in filters:
            query = query.filter(Coin.category == filters["category"])
        if "metal" in filters:
            query = query.filter(Coin.metal == filters["metal"])
        if "issuing_authority" in filters:
            query = query.filter(Coin.issuing_authority.ilike(f"%{filters['issuing_authority']}%"))
        if "denomination" in filters:
            query = query.filter(Coin.denomination.ilike(f"%{filters['denomination']}%"))
        if "storage_location" in filters:
            query = query.filter(Coin.storage_location == filters["storage_location"])
        if "acquisition_price_gte" in filters:
            query = query.filter(Coin.acquisition_price >= filters["acquisition_price_gte"])
        if "acquisition_price_lte" in filters:
            query = query.filter(Coin.acquisition_price <= filters["acquisition_price_lte"])
    
    total = query.count()
    coins = query.offset(skip).limit(limit).all()
    
    return coins, total


def create_coin(db: Session, coin: CoinCreate) -> Coin:
    """Create a new coin."""
    coin_data = coin.model_dump(exclude={"references", "provenance_events", "tags"})
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
