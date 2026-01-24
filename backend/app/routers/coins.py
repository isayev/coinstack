"""Coins API router - Clean refactored endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal, List
from app.database import get_db
from app.crud import get_coin, get_coins, create_coin, update_coin, delete_coin, get_coin_ids_sorted
from app.schemas.coin import (
    CoinListItem,
    CoinDetail,
    CoinCreate,
    CoinUpdate,
    PaginatedCoins,
    CoinReferenceOut,
    ReferenceTypeOut,
    CoinImageOut,
    CountermarkOut,
    ProvenanceEventOut,
    AuctionDataOut,
)
from app.models.coin import Category, Metal

router = APIRouter(prefix="/coins", tags=["coins"])


def coin_to_list_item(coin) -> CoinListItem:
    """Convert a Coin model to CoinListItem schema."""
    # Get primary image
    primary_image = None
    for img in coin.images:
        if img.is_primary:
            primary_image = img.file_path
            break
    if not primary_image and coin.images:
        primary_image = coin.images[0].file_path
    
    return CoinListItem(
        id=coin.id,
        category=coin.category,
        sub_category=coin.sub_category,
        denomination=coin.denomination,
        metal=coin.metal,
        issuing_authority=coin.issuing_authority,
        portrait_subject=coin.portrait_subject,
        mint_name=coin.mint.name if coin.mint else None,
        mint_year_start=coin.mint_year_start,
        mint_year_end=coin.mint_year_end,
        is_circa=coin.is_circa,
        is_test_cut=coin.is_test_cut,
        rarity=coin.rarity,
        grade=coin.grade,
        acquisition_price=coin.acquisition_price,
        estimated_value_usd=coin.estimated_value_usd,
        storage_location=coin.storage_location,
        primary_image=primary_image,
    )


def coin_to_detail(coin) -> CoinDetail:
    """Convert a Coin model to CoinDetail schema."""
    # Build references with ReferenceType
    references = []
    for ref in coin.references:
        ref_type_out = None
        if ref.reference_type:
            ref_type_out = ReferenceTypeOut(
                id=ref.reference_type.id,
                system=ref.reference_type.system,
                local_ref=ref.reference_type.local_ref,
                volume=ref.reference_type.volume,
                number=ref.reference_type.number,
                edition=ref.reference_type.edition,
                external_id=ref.reference_type.external_id,
                external_url=ref.reference_type.external_url,
                lookup_status=ref.reference_type.lookup_status,
                lookup_confidence=ref.reference_type.lookup_confidence,
            )
        
        references.append(CoinReferenceOut(
            id=ref.id,
            reference_type_id=ref.reference_type_id,
            is_primary=ref.is_primary,
            plate_coin=ref.plate_coin,
            position=ref.position.value if ref.position else None,
            variant_notes=ref.variant_notes,
            page=ref.page,
            plate=ref.plate,
            note_number=ref.note_number,
            reference_type=ref_type_out,
        ))
    
    # Build images
    images = [
        CoinImageOut(
            id=img.id,
            image_type=img.image_type.value,
            file_path=img.file_path,
            is_primary=img.is_primary,
        )
        for img in coin.images
    ]
    
    # Build countermarks
    countermarks = [
        CountermarkOut(
            id=cm.id,
            countermark_type=cm.countermark_type.value if cm.countermark_type else None,
            description=cm.description,
            expanded=cm.expanded,
            placement=cm.placement.value if cm.placement else None,
            position=cm.position,
            condition=cm.condition.value if cm.condition else None,
            authority=cm.authority,
            date_applied=cm.date_applied,
            image_url=cm.image_url,
            notes=cm.notes,
        )
        for cm in coin.countermarks
    ]
    
    # Build provenance events
    provenance_events = [
        ProvenanceEventOut(
            id=pe.id,
            event_type=pe.event_type.value if pe.event_type else None,
            event_date=pe.event_date,
            auction_house=pe.auction_house,
            sale_series=pe.sale_series,
            sale_number=pe.sale_number,
            lot_number=pe.lot_number,
            catalog_reference=pe.catalog_reference,
            hammer_price=pe.hammer_price,
            buyers_premium_pct=pe.buyers_premium_pct,
            total_price=pe.total_price,
            currency=pe.currency,
            dealer_name=pe.dealer_name,
            collection_name=pe.collection_name,
            url=pe.url,
            receipt_available=pe.receipt_available,
            notes=pe.notes,
        )
        for pe in coin.provenance_events
    ]
    
    # Build auction data
    auction_data = [
        AuctionDataOut(
            id=ad.id,
            auction_house=ad.auction_house,
            sale_name=ad.sale_name,
            lot_number=ad.lot_number,
            auction_date=ad.auction_date,
            url=ad.url,
            estimate_low=ad.estimate_low,
            estimate_high=ad.estimate_high,
            hammer_price=ad.hammer_price,
            total_price=ad.total_price,
            currency=ad.currency,
            sold=ad.sold,
            grade=ad.grade,
            title=ad.title,
            primary_photo_url=ad.primary_photo_url,
        )
        for ad in coin.auction_data
    ]
    
    return CoinDetail(
        id=coin.id,
        created_at=coin.created_at,
        updated_at=coin.updated_at,
        
        # Classification
        category=coin.category,
        sub_category=coin.sub_category,
        denomination=coin.denomination,
        metal=coin.metal,
        series=coin.series,
        
        # People
        issuing_authority=coin.issuing_authority,
        portrait_subject=coin.portrait_subject,
        status=coin.status,
        
        # Chronology
        reign_start=coin.reign_start,
        reign_end=coin.reign_end,
        mint_year_start=coin.mint_year_start,
        mint_year_end=coin.mint_year_end,
        is_circa=coin.is_circa,
        dating_certainty=coin.dating_certainty.value if coin.dating_certainty else None,
        dating_notes=coin.dating_notes,
        
        # Physical
        weight_g=coin.weight_g,
        diameter_mm=coin.diameter_mm,
        diameter_min_mm=coin.diameter_min_mm,
        thickness_mm=coin.thickness_mm,
        die_axis=coin.die_axis,
        orientation=coin.orientation.value if coin.orientation else None,
        is_test_cut=coin.is_test_cut,
        
        # Design
        obverse_legend=coin.obverse_legend,
        obverse_legend_expanded=coin.obverse_legend_expanded,
        obverse_description=coin.obverse_description,
        obverse_symbols=coin.obverse_symbols,
        reverse_legend=coin.reverse_legend,
        reverse_legend_expanded=coin.reverse_legend_expanded,
        reverse_description=coin.reverse_description,
        reverse_symbols=coin.reverse_symbols,
        exergue=coin.exergue,
        
        # Mint
        mint_id=coin.mint_id,
        mint_name=coin.mint.name if coin.mint else None,
        officina=coin.officina,
        
        # Grading
        grade_service=coin.grade_service.value if coin.grade_service else None,
        grade=coin.grade,
        strike_quality=coin.strike_quality,
        surface_quality=coin.surface_quality,
        certification_number=coin.certification_number,
        eye_appeal=coin.eye_appeal,
        toning_description=coin.toning_description,
        style_notes=coin.style_notes,
        
        # Acquisition
        acquisition_date=coin.acquisition_date,
        acquisition_price=coin.acquisition_price,
        acquisition_currency=coin.acquisition_currency,
        acquisition_source=coin.acquisition_source,
        acquisition_url=coin.acquisition_url,
        
        # Valuation
        estimate_low=coin.estimate_low,
        estimate_high=coin.estimate_high,
        estimated_value_usd=coin.estimated_value_usd,
        insured_value=coin.insured_value,
        
        # Storage
        holder_type=coin.holder_type.value if coin.holder_type else None,
        storage_location=coin.storage_location,
        for_sale=coin.for_sale,
        asking_price=coin.asking_price,
        
        # Research
        rarity=coin.rarity.value if coin.rarity else None,
        rarity_notes=coin.rarity_notes,
        historical_significance=coin.historical_significance,
        die_match_notes=coin.die_match_notes,
        personal_notes=coin.personal_notes,
        provenance_notes=coin.provenance_notes,
        
        # Die study
        die_study_obverse_id=coin.die_study_obverse_id,
        die_study_reverse_id=coin.die_study_reverse_id,
        die_study_group=coin.die_study_group,
        
        # Relations
        references=references,
        images=images,
        tags=[tag.tag for tag in coin.tags],
        countermarks=countermarks,
        provenance_events=provenance_events,
        auction_data=auction_data,
    )


@router.get("", response_model=PaginatedCoins)
async def list_coins(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("year", description="Sort: year, name, denomination, metal, category, grade, price, acquired, created, value"),
    sort_dir: Literal["asc", "desc"] = Query("asc"),
    category: Optional[Category] = None,
    sub_category: Optional[str] = None,
    metal: Optional[Metal] = None,
    issuing_authority: Optional[str] = None,
    denomination: Optional[str] = None,
    storage_location: Optional[str] = None,
    acquisition_price_gte: Optional[float] = None,
    acquisition_price_lte: Optional[float] = None,
    mint_year_gte: Optional[int] = None,
    mint_year_lte: Optional[int] = None,
    grade: Optional[str] = None,
    rarity: Optional[str] = None,
    is_circa: Optional[bool] = None,
    is_test_cut: Optional[bool] = None,
    is_year_unknown: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """List coins with pagination, filters, and sorting."""
    filters = {}
    if category:
        filters["category"] = category
    if sub_category:
        filters["sub_category"] = sub_category
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
    if mint_year_gte:
        filters["mint_year_gte"] = mint_year_gte
    if mint_year_lte:
        filters["mint_year_lte"] = mint_year_lte
    if grade:
        filters["grade"] = grade
    if rarity:
        filters["rarity"] = rarity
    if is_circa is not None:
        filters["is_circa"] = is_circa
    if is_test_cut is not None:
        filters["is_test_cut"] = is_test_cut
    if is_year_unknown is not None:
        filters["is_year_unknown"] = is_year_unknown
    
    skip = (page - 1) * per_page
    coins, total = get_coins(db, skip=skip, limit=per_page, filters=filters, sort_by=sort_by, sort_dir=sort_dir)
    
    items = [coin_to_list_item(coin) for coin in coins]
    pages = (total + per_page - 1) // per_page
    
    return PaginatedCoins(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{coin_id}", response_model=CoinDetail)
async def get_coin_detail_endpoint(coin_id: int, db: Session = Depends(get_db)):
    """Get coin detail by ID."""
    coin = get_coin(db, coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    return coin_to_detail(coin)


@router.get("/{coin_id}/navigation")
async def get_coin_navigation(
    coin_id: int,
    sort_by: str = Query("year"),
    sort_dir: Literal["asc", "desc"] = Query("asc"),
    category: Optional[Category] = None,
    sub_category: Optional[str] = None,
    metal: Optional[Metal] = None,
    issuing_authority: Optional[str] = None,
    denomination: Optional[str] = None,
    storage_location: Optional[str] = None,
    acquisition_price_gte: Optional[float] = None,
    acquisition_price_lte: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Get navigation info (prev/next coin IDs) based on current sort/filter."""
    filters = {}
    if category:
        filters["category"] = category
    if sub_category:
        filters["sub_category"] = sub_category
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
    
    coin_ids = get_coin_ids_sorted(db, filters=filters, sort_by=sort_by, sort_dir=sort_dir)
    
    try:
        current_index = coin_ids.index(coin_id)
    except ValueError:
        return {
            "prev_id": None,
            "next_id": None,
            "current_index": None,
            "total": len(coin_ids),
        }
    
    prev_id = coin_ids[current_index - 1] if current_index > 0 else None
    next_id = coin_ids[current_index + 1] if current_index < len(coin_ids) - 1 else None
    
    return {
        "prev_id": prev_id,
        "next_id": next_id,
        "current_index": current_index + 1,
        "total": len(coin_ids),
    }


@router.post("", response_model=CoinDetail, status_code=201)
async def create_coin_endpoint(coin: CoinCreate, db: Session = Depends(get_db)):
    """Create a new coin."""
    db_coin = create_coin(db, coin)
    return coin_to_detail(db_coin)


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
    return coin_to_detail(db_coin)


@router.delete("/{coin_id}", status_code=204)
async def delete_coin_endpoint(coin_id: int, db: Session = Depends(get_db)):
    """Delete a coin."""
    success = delete_coin(db, coin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Coin not found")
    return None
