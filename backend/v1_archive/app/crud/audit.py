"""CRUD operations for audit-related models."""

from datetime import datetime
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.discrepancy import DiscrepancyRecord
from app.models.enrichment import EnrichmentRecord
from app.models.audit_run import AuditRun
from app.models.coin import Coin
from app.models.auction_data import AuctionData
from app.models.image import CoinImage
from app.schemas.audit import (
    DiscrepancyFilters,
    EnrichmentFilters,
)


# =============================================================================
# Helper Functions for Extended Data
# =============================================================================

def _build_auction_images(auction_data: AuctionData | None) -> list[str]:
    """Build list of auction image URLs from AuctionData."""
    if not auction_data:
        return []
    
    images = []
    # Add primary photo first if available
    if auction_data.primary_photo_url:
        images.append(auction_data.primary_photo_url)
    
    # Add other photos from JSON field
    if auction_data.photos:
        for photo in auction_data.photos:
            if photo and photo not in images:
                images.append(photo)
    
    return images


def _get_coin_primary_image(db: Session, coin_id: int) -> str | None:
    """Get primary image path for a coin."""
    primary_image = db.query(CoinImage).filter(
        CoinImage.coin_id == coin_id,
        CoinImage.is_primary == True
    ).first()
    
    if primary_image:
        return primary_image.file_path
    
    # Fall back to first image if no primary is set
    first_image = db.query(CoinImage).filter(
        CoinImage.coin_id == coin_id
    ).first()
    
    return first_image.file_path if first_image else None


def _get_coin_primary_images_bulk(db: Session, coin_ids: list[int]) -> dict[int, str | None]:
    """Get primary image paths for multiple coins efficiently."""
    if not coin_ids:
        return {}
    
    # Get primary images
    primary_images = db.query(
        CoinImage.coin_id,
        CoinImage.file_path
    ).filter(
        CoinImage.coin_id.in_(coin_ids),
        CoinImage.is_primary == True
    ).all()
    
    result = {coin_id: path for coin_id, path in primary_images}
    
    # For coins without primary, get any first image
    missing_coin_ids = [cid for cid in coin_ids if cid not in result]
    if missing_coin_ids:
        first_images = db.query(
            CoinImage.coin_id,
            func.min(CoinImage.file_path).label('file_path')
        ).filter(
            CoinImage.coin_id.in_(missing_coin_ids)
        ).group_by(CoinImage.coin_id).all()
        
        for coin_id, path in first_images:
            result[coin_id] = path
    
    return result


def _get_coin_details_bulk(db: Session, coin_ids: list[int]) -> dict[int, dict]:
    """Get coin details (ruler, denomination, metal, grade, category, etc.) for multiple coins."""
    if not coin_ids:
        return {}
    
    coins = db.query(
        Coin.id,
        Coin.issuing_authority,
        Coin.denomination,
        Coin.metal,
        Coin.grade,
        Coin.category,
        Coin.mint_year_start,
        Coin.mint_year_end,
        Coin.is_circa,
    ).filter(Coin.id.in_(coin_ids)).all()
    
    result = {}
    for coin in coins:
        result[coin.id] = {
            "ruler": coin.issuing_authority,
            "denomination": coin.denomination,
            "metal": coin.metal.value if coin.metal else None,
            "grade": coin.grade,
            "category": coin.category.value if coin.category else None,
            "mint_year_start": coin.mint_year_start,
            "mint_year_end": coin.mint_year_end,
            "is_circa": coin.is_circa,
        }
    
    return result


# =============================================================================
# Discrepancy CRUD
# =============================================================================

def get_discrepancy(db: Session, discrepancy_id: int) -> DiscrepancyRecord | None:
    """Get a single discrepancy by ID."""
    return db.query(DiscrepancyRecord).filter(
        DiscrepancyRecord.id == discrepancy_id
    ).first()


def get_discrepancy_with_extended_data(db: Session, discrepancy_id: int) -> dict | None:
    """Get a single discrepancy with extended auction and coin data."""
    record = get_discrepancy(db, discrepancy_id)
    if not record:
        return None
    
    # Get auction data
    auction_data = None
    if record.auction_data_id:
        auction_data = db.query(AuctionData).filter(
            AuctionData.id == record.auction_data_id
        ).first()
    
    # Get coin primary image
    coin_primary_image = _get_coin_primary_image(db, record.coin_id)
    
    # Build result dict from ORM model
    result = {
        "id": record.id,
        "coin_id": record.coin_id,
        "auction_data_id": record.auction_data_id,
        "audit_run_id": record.audit_run_id,
        "field_name": record.field_name,
        "current_value": record.current_value,
        "auction_value": record.auction_value,
        "normalized_current": record.normalized_current,
        "normalized_auction": record.normalized_auction,
        "similarity": record.similarity,
        "difference_type": record.difference_type,
        "comparison_notes": record.comparison_notes,
        "source_house": record.source_house,
        "trust_level": record.trust_level,
        "auto_acceptable": record.auto_acceptable,
        "status": record.status,
        "resolved_at": record.resolved_at,
        "resolution": record.resolution,
        "resolution_notes": record.resolution_notes,
        "created_at": record.created_at,
        # Extended data
        "source_url": auction_data.url if auction_data else None,
        "auction_images": _build_auction_images(auction_data),
        "coin_primary_image": coin_primary_image,
    }
    
    return result


def get_discrepancies(
    db: Session,
    filters: DiscrepancyFilters | None = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[DiscrepancyRecord], int]:
    """
    Get paginated discrepancy records with filtering.
    
    Returns:
        Tuple of (items, total_count)
    """
    query = db.query(DiscrepancyRecord)
    
    if filters:
        if filters.status:
            query = query.filter(DiscrepancyRecord.status == filters.status)
        if filters.field_name:
            query = query.filter(DiscrepancyRecord.field_name == filters.field_name)
        if filters.source_house:
            query = query.filter(DiscrepancyRecord.source_house.ilike(f"%{filters.source_house}%"))
        if filters.trust_level:
            query = query.filter(DiscrepancyRecord.trust_level == filters.trust_level)
        if filters.coin_id:
            query = query.filter(DiscrepancyRecord.coin_id == filters.coin_id)
        if filters.audit_run_id:
            query = query.filter(DiscrepancyRecord.audit_run_id == filters.audit_run_id)
        if filters.min_similarity is not None:
            query = query.filter(DiscrepancyRecord.similarity >= filters.min_similarity)
        if filters.max_similarity is not None:
            query = query.filter(DiscrepancyRecord.similarity <= filters.max_similarity)
    
    total = query.count()
    
    # Sorting
    sort_column = getattr(DiscrepancyRecord, sort_by, DiscrepancyRecord.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Pagination
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    return items, total


def get_discrepancies_with_extended_data(
    db: Session,
    filters: DiscrepancyFilters | None = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[dict], int]:
    """
    Get paginated discrepancy records with extended auction and coin data.
    
    Returns:
        Tuple of (items with extended data, total_count)
    """
    items, total = get_discrepancies(db, filters, page, per_page, sort_by, sort_order)
    
    if not items:
        return [], total
    
    # Collect unique coin_ids and auction_data_ids
    coin_ids = list(set(item.coin_id for item in items))
    auction_data_ids = list(set(item.auction_data_id for item in items if item.auction_data_id))
    
    # Bulk fetch coin primary images
    coin_images = _get_coin_primary_images_bulk(db, coin_ids)
    
    # Bulk fetch coin details
    coin_details = _get_coin_details_bulk(db, coin_ids)
    
    # Bulk fetch auction data
    auction_data_map = {}
    if auction_data_ids:
        auction_records = db.query(AuctionData).filter(
            AuctionData.id.in_(auction_data_ids)
        ).all()
        auction_data_map = {ad.id: ad for ad in auction_records}
    
    # Build result list with extended data
    results = []
    for record in items:
        auction_data = auction_data_map.get(record.auction_data_id)
        coin_detail = coin_details.get(record.coin_id, {})
        
        result = {
            "id": record.id,
            "coin_id": record.coin_id,
            "auction_data_id": record.auction_data_id,
            "audit_run_id": record.audit_run_id,
            "field_name": record.field_name,
            "current_value": record.current_value,
            "auction_value": record.auction_value,
            "normalized_current": record.normalized_current,
            "normalized_auction": record.normalized_auction,
            "similarity": record.similarity,
            "difference_type": record.difference_type,
            "comparison_notes": record.comparison_notes,
            "source_house": record.source_house,
            "trust_level": record.trust_level,
            "auto_acceptable": record.auto_acceptable,
            "status": record.status,
            "resolved_at": record.resolved_at,
            "resolution": record.resolution,
            "resolution_notes": record.resolution_notes,
            "created_at": record.created_at,
            # Extended data
            "source_url": auction_data.url if auction_data else None,
            "auction_images": _build_auction_images(auction_data),
            "coin_primary_image": coin_images.get(record.coin_id),
            # Coin details
            "coin_ruler": coin_detail.get("ruler"),
            "coin_denomination": coin_detail.get("denomination"),
            "coin_metal": coin_detail.get("metal"),
            "coin_grade": coin_detail.get("grade"),
            "coin_category": coin_detail.get("category"),
            "coin_mint_year_start": coin_detail.get("mint_year_start"),
            "coin_mint_year_end": coin_detail.get("mint_year_end"),
            "coin_is_circa": coin_detail.get("is_circa"),
        }
        results.append(result)
    
    return results, total


def get_coin_discrepancies(db: Session, coin_id: int) -> list[DiscrepancyRecord]:
    """Get all discrepancies for a coin."""
    return db.query(DiscrepancyRecord).filter(
        DiscrepancyRecord.coin_id == coin_id
    ).order_by(DiscrepancyRecord.created_at.desc()).all()


def get_pending_discrepancies_count(db: Session) -> int:
    """Get count of pending discrepancies."""
    return db.query(DiscrepancyRecord).filter(
        DiscrepancyRecord.status == "pending"
    ).count()


def resolve_discrepancy(
    db: Session,
    discrepancy_id: int,
    resolution: str,
    notes: str | None = None,
) -> DiscrepancyRecord | None:
    """Resolve a discrepancy."""
    record = get_discrepancy(db, discrepancy_id)
    if not record:
        return None
    
    record.status = resolution
    record.resolution = resolution
    record.resolved_at = datetime.utcnow()
    record.resolution_notes = notes
    
    db.commit()
    db.refresh(record)
    return record


def bulk_resolve_discrepancies(
    db: Session,
    discrepancy_ids: list[int],
    resolution: str,
    notes: str | None = None,
) -> int:
    """Bulk resolve discrepancies. Returns count resolved."""
    count = db.query(DiscrepancyRecord).filter(
        DiscrepancyRecord.id.in_(discrepancy_ids)
    ).update({
        "status": resolution,
        "resolution": resolution,
        "resolved_at": datetime.utcnow(),
        "resolution_notes": notes,
    }, synchronize_session=False)
    
    db.commit()
    return count


# =============================================================================
# Enrichment CRUD
# =============================================================================

def get_enrichment(db: Session, enrichment_id: int) -> EnrichmentRecord | None:
    """Get a single enrichment by ID."""
    return db.query(EnrichmentRecord).filter(
        EnrichmentRecord.id == enrichment_id
    ).first()


def get_enrichment_with_extended_data(db: Session, enrichment_id: int) -> dict | None:
    """Get a single enrichment with extended auction and coin data."""
    record = get_enrichment(db, enrichment_id)
    if not record:
        return None
    
    # Get auction data
    auction_data = None
    if record.auction_data_id:
        auction_data = db.query(AuctionData).filter(
            AuctionData.id == record.auction_data_id
        ).first()
    
    # Get coin primary image
    coin_primary_image = _get_coin_primary_image(db, record.coin_id)
    
    # Build result dict from ORM model
    result = {
        "id": record.id,
        "coin_id": record.coin_id,
        "auction_data_id": record.auction_data_id,
        "audit_run_id": record.audit_run_id,
        "field_name": record.field_name,
        "suggested_value": record.suggested_value,
        "source_house": record.source_house,
        "trust_level": record.trust_level,
        "confidence": record.confidence,
        "auto_applicable": record.auto_applicable,
        "status": record.status,
        "applied": record.applied,
        "applied_at": record.applied_at,
        "rejection_reason": record.rejection_reason,
        "created_at": record.created_at,
        # Extended data
        "source_url": auction_data.url if auction_data else None,
        "auction_images": _build_auction_images(auction_data),
        "coin_primary_image": coin_primary_image,
    }
    
    return result


def get_enrichments(
    db: Session,
    filters: EnrichmentFilters | None = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[EnrichmentRecord], int]:
    """
    Get paginated enrichment records with filtering.
    
    Returns:
        Tuple of (items, total_count)
    """
    query = db.query(EnrichmentRecord)
    
    if filters:
        if filters.status:
            query = query.filter(EnrichmentRecord.status == filters.status)
        if filters.field_name:
            query = query.filter(EnrichmentRecord.field_name == filters.field_name)
        if filters.source_house:
            query = query.filter(EnrichmentRecord.source_house.ilike(f"%{filters.source_house}%"))
        if filters.trust_level:
            query = query.filter(EnrichmentRecord.trust_level == filters.trust_level)
        if filters.coin_id:
            query = query.filter(EnrichmentRecord.coin_id == filters.coin_id)
        if filters.audit_run_id:
            query = query.filter(EnrichmentRecord.audit_run_id == filters.audit_run_id)
        if filters.auto_applicable is not None:
            query = query.filter(EnrichmentRecord.auto_applicable == filters.auto_applicable)
    
    total = query.count()
    
    # Sorting
    sort_column = getattr(EnrichmentRecord, sort_by, EnrichmentRecord.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Pagination
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    return items, total


def get_enrichments_with_extended_data(
    db: Session,
    filters: EnrichmentFilters | None = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[dict], int]:
    """
    Get paginated enrichment records with extended auction and coin data.
    
    Returns:
        Tuple of (items with extended data, total_count)
    """
    items, total = get_enrichments(db, filters, page, per_page, sort_by, sort_order)
    
    if not items:
        return [], total
    
    # Collect unique coin_ids and auction_data_ids
    coin_ids = list(set(item.coin_id for item in items))
    auction_data_ids = list(set(item.auction_data_id for item in items if item.auction_data_id))
    
    # Bulk fetch coin primary images
    coin_images = _get_coin_primary_images_bulk(db, coin_ids)
    
    # Bulk fetch coin details
    coin_details = _get_coin_details_bulk(db, coin_ids)
    
    # Bulk fetch auction data
    auction_data_map = {}
    if auction_data_ids:
        auction_records = db.query(AuctionData).filter(
            AuctionData.id.in_(auction_data_ids)
        ).all()
        auction_data_map = {ad.id: ad for ad in auction_records}
    
    # Build result list with extended data
    results = []
    for record in items:
        auction_data = auction_data_map.get(record.auction_data_id)
        coin_detail = coin_details.get(record.coin_id, {})
        
        result = {
            "id": record.id,
            "coin_id": record.coin_id,
            "auction_data_id": record.auction_data_id,
            "audit_run_id": record.audit_run_id,
            "field_name": record.field_name,
            "suggested_value": record.suggested_value,
            "source_house": record.source_house,
            "trust_level": record.trust_level,
            "confidence": record.confidence,
            "auto_applicable": record.auto_applicable,
            "status": record.status,
            "applied": record.applied,
            "applied_at": record.applied_at,
            "rejection_reason": record.rejection_reason,
            "created_at": record.created_at,
            # Extended data
            "source_url": auction_data.url if auction_data else None,
            "auction_images": _build_auction_images(auction_data),
            "coin_primary_image": coin_images.get(record.coin_id),
            # Coin details
            "coin_ruler": coin_detail.get("ruler"),
            "coin_denomination": coin_detail.get("denomination"),
            "coin_metal": coin_detail.get("metal"),
            "coin_grade": coin_detail.get("grade"),
            "coin_category": coin_detail.get("category"),
            "coin_mint_year_start": coin_detail.get("mint_year_start"),
            "coin_mint_year_end": coin_detail.get("mint_year_end"),
            "coin_is_circa": coin_detail.get("is_circa"),
        }
        results.append(result)
    
    return results, total


def get_coin_enrichments(db: Session, coin_id: int) -> list[EnrichmentRecord]:
    """Get all enrichments for a coin."""
    return db.query(EnrichmentRecord).filter(
        EnrichmentRecord.coin_id == coin_id
    ).order_by(EnrichmentRecord.created_at.desc()).all()


def get_pending_enrichments_count(db: Session) -> int:
    """Get count of pending enrichments."""
    return db.query(EnrichmentRecord).filter(
        EnrichmentRecord.status == "pending"
    ).count()


def apply_enrichment(db: Session, enrichment_id: int) -> EnrichmentRecord | None:
    """Mark an enrichment as applied."""
    record = get_enrichment(db, enrichment_id)
    if not record:
        return None
    
    record.status = "applied"
    record.applied = True
    record.applied_at = datetime.utcnow()
    
    db.commit()
    db.refresh(record)
    return record


def reject_enrichment(
    db: Session,
    enrichment_id: int,
    reason: str | None = None,
) -> EnrichmentRecord | None:
    """Reject an enrichment."""
    record = get_enrichment(db, enrichment_id)
    if not record:
        return None
    
    record.status = "rejected"
    record.rejection_reason = reason
    
    db.commit()
    db.refresh(record)
    return record


# =============================================================================
# Audit Run CRUD
# =============================================================================

def get_audit_run(db: Session, run_id: int) -> AuditRun | None:
    """Get a single audit run by ID."""
    return db.query(AuditRun).filter(AuditRun.id == run_id).first()


def get_audit_runs(
    db: Session,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[AuditRun], int]:
    """Get paginated audit runs."""
    query = db.query(AuditRun)
    total = query.count()
    
    items = query.order_by(AuditRun.started_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    return items, total


def get_running_audit_runs(db: Session) -> list[AuditRun]:
    """Get currently running audit runs."""
    return db.query(AuditRun).filter(
        AuditRun.status == "running"
    ).all()


def create_audit_run(
    db: Session,
    scope: str,
    coin_ids: list[int] | None = None,
) -> AuditRun:
    """Create a new audit run."""
    # Count total coins
    if scope == "all":
        total = db.query(Coin).count()
    elif coin_ids:
        total = len(coin_ids)
    else:
        total = 0
    
    run = AuditRun(
        scope=scope,
        coin_ids=coin_ids,
        total_coins=total,
        status="running",
    )
    
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_audit_run_progress(
    db: Session,
    run_id: int,
    coins_audited: int | None = None,
    discrepancies_found: int | None = None,
    enrichments_found: int | None = None,
    coins_with_issues: int | None = None,
) -> AuditRun | None:
    """Update audit run progress."""
    run = get_audit_run(db, run_id)
    if not run:
        return None
    
    if coins_audited is not None:
        run.coins_audited = coins_audited
    if discrepancies_found is not None:
        run.discrepancies_found = discrepancies_found
    if enrichments_found is not None:
        run.enrichments_found = enrichments_found
    if coins_with_issues is not None:
        run.coins_with_issues = coins_with_issues
    
    db.commit()
    db.refresh(run)
    return run


def complete_audit_run(
    db: Session,
    run_id: int,
    status: str = "completed",
    error_message: str | None = None,
) -> AuditRun | None:
    """Mark an audit run as complete."""
    run = get_audit_run(db, run_id)
    if not run:
        return None
    
    run.status = status
    run.completed_at = datetime.utcnow()
    run.error_message = error_message
    
    db.commit()
    db.refresh(run)
    return run


# =============================================================================
# Statistics
# =============================================================================

def get_discrepancy_stats(db: Session) -> dict:
    """Get discrepancy statistics for dashboard."""
    # By status
    status_counts = db.query(
        DiscrepancyRecord.status,
        func.count(DiscrepancyRecord.id)
    ).group_by(DiscrepancyRecord.status).all()
    
    # By trust level (pending only)
    trust_counts = db.query(
        DiscrepancyRecord.trust_level,
        func.count(DiscrepancyRecord.id)
    ).filter(
        DiscrepancyRecord.status == "pending"
    ).group_by(DiscrepancyRecord.trust_level).all()
    
    # By field (pending only)
    field_counts = db.query(
        DiscrepancyRecord.field_name,
        func.count(DiscrepancyRecord.id)
    ).filter(
        DiscrepancyRecord.status == "pending"
    ).group_by(DiscrepancyRecord.field_name).all()
    
    # By source (pending only)
    source_counts = db.query(
        DiscrepancyRecord.source_house,
        func.count(DiscrepancyRecord.id)
    ).filter(
        DiscrepancyRecord.status == "pending"
    ).group_by(DiscrepancyRecord.source_house).all()
    
    return {
        "by_status": {s: c for s, c in status_counts},
        "by_trust": {t: c for t, c in trust_counts},
        "by_field": {f: c for f, c in field_counts},
        "by_source": {s: c for s, c in source_counts},
    }


def get_enrichment_stats(db: Session) -> dict:
    """Get enrichment statistics for dashboard."""
    # By status
    status_counts = db.query(
        EnrichmentRecord.status,
        func.count(EnrichmentRecord.id)
    ).group_by(EnrichmentRecord.status).all()
    
    # By field (pending only)
    field_counts = db.query(
        EnrichmentRecord.field_name,
        func.count(EnrichmentRecord.id)
    ).filter(
        EnrichmentRecord.status == "pending"
    ).group_by(EnrichmentRecord.field_name).all()
    
    return {
        "by_status": {s: c for s, c in status_counts},
        "by_field": {f: c for f, c in field_counts},
    }
