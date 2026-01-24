"""Coins API router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.crud import get_coin, get_coins, create_coin, update_coin, delete_coin
from app.schemas.coin import (
    CoinListItem,
    CoinDetail,
    CoinCreate,
    CoinUpdate,
    PaginatedCoins,
    CoinReferenceOut,
    CoinImageOut,
)
from app.models.coin import Category, Metal

router = APIRouter(prefix="/coins", tags=["coins"])


@router.get("", response_model=PaginatedCoins)
async def list_coins(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[Category] = None,
    metal: Optional[Metal] = None,
    issuing_authority: Optional[str] = None,
    denomination: Optional[str] = None,
    storage_location: Optional[str] = None,
    acquisition_price_gte: Optional[float] = None,
    acquisition_price_lte: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """List coins with pagination and filters."""
    filters = {}
    if category:
        filters["category"] = category
    if metal:
        filters["metal"] = metal
    if issuing_authority:
        filters["issuing_authority"] = issuing_authority
    if denomination:
        filters["denomination"] = denomination
    if storage_location:
        filters["storage_location"] = storage_location
    if acquisition_price_gte:
        filters["acquisition_price_gte"] = acquisition_price_gte
    if acquisition_price_lte:
        filters["acquisition_price_lte"] = acquisition_price_lte
    
    skip = (page - 1) * per_page
    coins, total = get_coins(db, skip=skip, limit=per_page, filters=filters)
    
    # Convert to list items
    items = []
    for coin in coins:
        item = CoinListItem(
            id=coin.id,
            category=coin.category,
            denomination=coin.denomination,
            metal=coin.metal,
            issuing_authority=coin.issuing_authority,
            portrait_subject=coin.portrait_subject,
            mint_name=coin.mint.name if coin.mint else None,
            grade=coin.grade,
            acquisition_price=coin.acquisition_price,
            storage_location=coin.storage_location,
        )
        items.append(item)
    
    pages = (total + per_page - 1) // per_page
    
    return PaginatedCoins(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{coin_id}", response_model=CoinDetail)
async def get_coin_detail(coin_id: int, db: Session = Depends(get_db)):
    """Get coin detail by ID."""
    coin = get_coin(db, coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    # Convert to detail schema
    detail = CoinDetail(
        id=coin.id,
        created_at=coin.created_at,
        updated_at=coin.updated_at,
        category=coin.category,
        denomination=coin.denomination,
        metal=coin.metal,
        series=coin.series,
        issuing_authority=coin.issuing_authority,
        portrait_subject=coin.portrait_subject,
        status=coin.status,
        reign_start=coin.reign_start,
        reign_end=coin.reign_end,
        mint_year_start=coin.mint_year_start,
        mint_year_end=coin.mint_year_end,
        weight_g=coin.weight_g,
        diameter_mm=coin.diameter_mm,
        diameter_min_mm=coin.diameter_min_mm,
        thickness_mm=coin.thickness_mm,
        die_axis=coin.die_axis,
        obverse_legend=coin.obverse_legend,
        obverse_legend_expanded=coin.obverse_legend_expanded,
        obverse_description=coin.obverse_description,
        obverse_symbols=coin.obverse_symbols,
        reverse_legend=coin.reverse_legend,
        reverse_legend_expanded=coin.reverse_legend_expanded,
        reverse_description=coin.reverse_description,
        reverse_symbols=coin.reverse_symbols,
        exergue=coin.exergue,
        mint_id=coin.mint_id,
        mint_name=coin.mint.name if coin.mint else None,
        grade_service=coin.grade_service.value if coin.grade_service else None,
        grade=coin.grade,
        strike_quality=coin.strike_quality,
        surface_quality=coin.surface_quality,
        certification_number=coin.certification_number,
        acquisition_date=coin.acquisition_date,
        acquisition_price=coin.acquisition_price,
        acquisition_currency=coin.acquisition_currency,
        acquisition_source=coin.acquisition_source,
        acquisition_url=coin.acquisition_url,
        storage_location=coin.storage_location,
        for_sale=coin.for_sale,
        asking_price=coin.asking_price,
        rarity=coin.rarity.value if coin.rarity else None,
        rarity_notes=coin.rarity_notes,
        historical_significance=coin.historical_significance,
        personal_notes=coin.personal_notes,
        references=[
            CoinReferenceOut(
                id=ref.id,
                system=ref.system.value,
                volume=ref.volume,
                number=ref.number,
                is_primary=ref.is_primary,
                plate_coin=ref.plate_coin,
            )
            for ref in coin.references
        ],
        images=[
            CoinImageOut(
                id=img.id,
                image_type=img.image_type.value,
                file_path=img.file_path,
                is_primary=img.is_primary,
            )
            for img in coin.images
        ],
        tags=[tag.tag for tag in coin.tags],
    )
    
    return detail


@router.post("", response_model=CoinDetail, status_code=201)
async def create_coin_endpoint(coin: CoinCreate, db: Session = Depends(get_db)):
    """Create a new coin."""
    db_coin = create_coin(db, coin)
    return await get_coin_detail(db_coin.id, db)


@router.put("/{coin_id}", response_model=CoinDetail)
async def update_coin_endpoint(
    coin_id: int,
    coin_update: CoinUpdate,
    db: Session = Depends(get_db),
):
    """Update a coin."""
    db_coin = update_coin(db, coin_id, coin_update)
    if not db_coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return await get_coin_detail(coin_id, db)


@router.delete("/{coin_id}", status_code=204)
async def delete_coin_endpoint(coin_id: int, db: Session = Depends(get_db)):
    """Delete a coin."""
    success = delete_coin(db, coin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Coin not found")
    return None
