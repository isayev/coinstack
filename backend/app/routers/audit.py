"""
API router for audit operations.

Provides endpoints for:
- Running audits (single coin, selected coins, all coins)
- Managing discrepancies (list, filter, resolve)
- Managing enrichments (list, apply, reject)
- Downloading auction images
- Getting audit statistics
"""

import math
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.audit import (
    DiscrepancyOut,
    DiscrepancyDetail,
    DiscrepancyResolveRequest,
    BulkResolveRequest,
    PaginatedDiscrepancies,
    DiscrepancyFilters,
    EnrichmentOut,
    EnrichmentDetail,
    EnrichmentApplyRequest,
    EnrichmentRejectRequest,
    PaginatedEnrichments,
    EnrichmentFilters,
    AuditRunCreate,
    AuditRunOut,
    AuditRunProgress,
    AuditSummary,
    CoinAuditSummary,
    ImageDownloadRequest,
    ImageDownloadResult,
)
from app.crud import audit as audit_crud
from app.services.audit import AuditService, EnrichmentService, AuctionImageHandler

router = APIRouter(prefix="/audit", tags=["audit"])


# =============================================================================
# Audit Run Endpoints
# =============================================================================

@router.post("/run", response_model=AuditRunOut)
async def start_audit(
    request: AuditRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a new audit run.
    
    - scope="single": Audit single coin (provide coin_ids with one ID)
    - scope="selected": Audit selected coins (provide coin_ids list)
    - scope="all": Audit all coins with auction data
    
    Returns immediately with audit run ID. Poll /audit/runs/{id} for progress.
    """
    audit_service = AuditService(db)
    
    # Create audit run record
    run = await audit_service.create_audit_run(
        scope=request.scope,
        coin_ids=request.coin_ids,
    )
    
    # Start background task
    if request.scope == "all":
        background_tasks.add_task(
            audit_service.run_full_audit,
            run.id
        )
    elif request.coin_ids:
        background_tasks.add_task(
            audit_service.run_selected_audit,
            request.coin_ids,
            run.id
        )
    
    return run


@router.post("/coin/{coin_id}", response_model=CoinAuditSummary)
async def audit_single_coin(
    coin_id: int,
    db: Session = Depends(get_db),
):
    """
    Audit a single coin immediately (synchronous).
    
    Use for quick audits of individual coins.
    For bulk audits, use POST /audit/run instead.
    """
    audit_service = AuditService(db)
    
    try:
        result = await audit_service.audit_coin(coin_id)
        return CoinAuditSummary(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs", response_model=list[AuditRunOut])
async def list_audit_runs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all audit runs with pagination."""
    runs, _ = audit_crud.get_audit_runs(db, page=page, per_page=per_page)
    return runs


@router.get("/runs/{run_id}", response_model=AuditRunOut)
async def get_audit_run(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Get audit run details including progress."""
    run = audit_crud.get_audit_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    return run


@router.get("/runs/{run_id}/progress", response_model=AuditRunProgress)
async def get_audit_progress(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Get audit run progress for polling."""
    run = audit_crud.get_audit_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    
    return AuditRunProgress(
        id=run.id,
        status=run.status,
        progress_percent=run.progress_percent,
        coins_audited=run.coins_audited,
        total_coins=run.total_coins,
        discrepancies_found=run.discrepancies_found,
        enrichments_found=run.enrichments_found,
    )


# =============================================================================
# Discrepancy Endpoints
# =============================================================================

@router.get("/discrepancies", response_model=PaginatedDiscrepancies)
async def list_discrepancies(
    status: str | None = None,
    field_name: str | None = None,
    source_house: str | None = None,
    trust_level: str | None = None,
    coin_id: int | None = None,
    audit_run_id: int | None = None,
    min_similarity: float | None = None,
    max_similarity: float | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    """
    List discrepancies with filtering and pagination.
    
    Filter options:
    - status: "pending", "accepted", "rejected", "ignored"
    - field_name: Filter by field (e.g., "weight_g", "grade")
    - source_house: Filter by auction house
    - trust_level: "authoritative", "high", "medium", "low"
    - coin_id: Filter by coin
    - min/max_similarity: Filter by similarity score
    
    Response includes extended data:
    - source_url: Link to auction listing
    - auction_images: Array of image URLs from auction
    - coin_primary_image: Primary image path for the coin
    """
    filters = DiscrepancyFilters(
        status=status,
        field_name=field_name,
        source_house=source_house,
        trust_level=trust_level,
        coin_id=coin_id,
        audit_run_id=audit_run_id,
        min_similarity=min_similarity,
        max_similarity=max_similarity,
    )
    
    items, total = audit_crud.get_discrepancies_with_extended_data(
        db,
        filters=filters,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedDiscrepancies(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1,
    )


@router.get("/discrepancies/{discrepancy_id}", response_model=DiscrepancyOut)
async def get_discrepancy(
    discrepancy_id: int,
    db: Session = Depends(get_db),
):
    """Get a single discrepancy by ID with extended auction and coin data."""
    record = audit_crud.get_discrepancy_with_extended_data(db, discrepancy_id)
    if not record:
        raise HTTPException(status_code=404, detail="Discrepancy not found")
    return record


@router.post("/discrepancies/{discrepancy_id}/resolve", response_model=DiscrepancyOut)
async def resolve_discrepancy(
    discrepancy_id: int,
    request: DiscrepancyResolveRequest,
    db: Session = Depends(get_db),
):
    """
    Resolve a discrepancy.
    
    Resolutions:
    - "accepted": Accept auction value, update coin record
    - "rejected": Keep current value
    - "ignored": Skip this discrepancy
    """
    audit_service = AuditService(db)
    
    try:
        record = await audit_service.resolve_discrepancy(
            discrepancy_id,
            request.resolution,
            request.notes,
        )
        return record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/discrepancies/bulk-resolve")
async def bulk_resolve_discrepancies(
    request: BulkResolveRequest,
    db: Session = Depends(get_db),
):
    """Bulk resolve multiple discrepancies."""
    count = audit_crud.bulk_resolve_discrepancies(
        db,
        request.discrepancy_ids,
        request.resolution,
        request.notes,
    )
    
    return {
        "resolved": count,
        "total": len(request.discrepancy_ids),
    }


@router.get("/coin/{coin_id}/discrepancies", response_model=list[DiscrepancyOut])
async def get_coin_discrepancies(
    coin_id: int,
    db: Session = Depends(get_db),
):
    """Get all discrepancies for a specific coin."""
    return audit_crud.get_coin_discrepancies(db, coin_id)


# =============================================================================
# Enrichment Endpoints
# =============================================================================

@router.get("/enrichments", response_model=PaginatedEnrichments)
async def list_enrichments(
    status: str | None = None,
    field_name: str | None = None,
    source_house: str | None = None,
    trust_level: str | None = None,
    coin_id: int | None = None,
    audit_run_id: int | None = None,
    auto_applicable: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    """
    List enrichment suggestions with filtering and pagination.
    
    Filter by auto_applicable=true to see enrichments that can be
    auto-applied based on trust configuration.
    
    Response includes extended data:
    - source_url: Link to auction listing
    - auction_images: Array of image URLs from auction
    - coin_primary_image: Primary image path for the coin
    """
    filters = EnrichmentFilters(
        status=status,
        field_name=field_name,
        source_house=source_house,
        trust_level=trust_level,
        coin_id=coin_id,
        audit_run_id=audit_run_id,
        auto_applicable=auto_applicable,
    )
    
    items, total = audit_crud.get_enrichments_with_extended_data(
        db,
        filters=filters,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    return PaginatedEnrichments(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1,
    )


@router.get("/enrichments/{enrichment_id}", response_model=EnrichmentOut)
async def get_enrichment(
    enrichment_id: int,
    db: Session = Depends(get_db),
):
    """Get a single enrichment by ID with extended auction and coin data."""
    record = audit_crud.get_enrichment_with_extended_data(db, enrichment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Enrichment not found")
    return record


@router.post("/enrichments/{enrichment_id}/apply", response_model=EnrichmentOut)
async def apply_enrichment(
    enrichment_id: int,
    db: Session = Depends(get_db),
):
    """Apply a single enrichment to update the coin."""
    enrichment_service = EnrichmentService(db)
    
    try:
        record = await enrichment_service.apply_enrichment(enrichment_id)
        return record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/enrichments/{enrichment_id}/reject", response_model=EnrichmentOut)
async def reject_enrichment(
    enrichment_id: int,
    reason: str | None = None,
    db: Session = Depends(get_db),
):
    """Reject an enrichment suggestion."""
    enrichment_service = EnrichmentService(db)
    
    try:
        record = await enrichment_service.reject_enrichment(enrichment_id, reason)
        return record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/enrichments/bulk-apply")
async def bulk_apply_enrichments(
    request: EnrichmentApplyRequest,
    db: Session = Depends(get_db),
):
    """Apply multiple enrichments."""
    enrichment_service = EnrichmentService(db)
    result = await enrichment_service.bulk_apply_enrichments(request.enrichment_ids)
    return result


@router.post("/enrichments/bulk-reject")
async def bulk_reject_enrichments(
    request: EnrichmentRejectRequest,
    db: Session = Depends(get_db),
):
    """Reject multiple enrichments."""
    enrichment_service = EnrichmentService(db)
    result = await enrichment_service.bulk_reject_enrichments(
        request.enrichment_ids,
        request.reason,
    )
    return result


@router.post("/enrichments/auto-apply-empty")
async def auto_apply_empty_field_enrichments(
    db: Session = Depends(get_db),
):
    """
    Automatically apply all pending enrichments that fill empty fields.
    
    This is a convenience operation that applies enrichments where the
    current coin field value is null/empty.
    """
    enrichment_service = EnrichmentService(db)
    result = await enrichment_service.apply_all_empty_field_enrichments()
    return result


@router.get("/coin/{coin_id}/enrichments", response_model=list[EnrichmentOut])
async def get_coin_enrichments(
    coin_id: int,
    db: Session = Depends(get_db),
):
    """Get all enrichments for a specific coin."""
    return audit_crud.get_coin_enrichments(db, coin_id)


@router.post("/coin/{coin_id}/auto-enrich")
async def auto_enrich_coin(
    coin_id: int,
    db: Session = Depends(get_db),
):
    """
    Automatically apply all auto-applicable enrichments for a coin.
    
    Only applies enrichments with high trust levels.
    """
    enrichment_service = EnrichmentService(db)
    applied = await enrichment_service.apply_all_auto_enrichments(coin_id)
    
    return {
        "applied": len(applied),
        "enrichments": [EnrichmentOut.model_validate(e) for e in applied],
    }


# =============================================================================
# Image Download Endpoints
# =============================================================================

@router.post("/coin/{coin_id}/download-images", response_model=ImageDownloadResult)
async def download_coin_images(
    coin_id: int,
    request: ImageDownloadRequest | None = None,
    db: Session = Depends(get_db),
):
    """
    Download images from auction data for a coin.
    
    If auction_data_id is provided, downloads from that specific auction.
    Otherwise, downloads from all linked auctions.
    
    Uses perceptual hashing to avoid duplicate downloads.
    """
    image_handler = AuctionImageHandler(db)
    
    if request and request.auction_data_id:
        images = await image_handler.download_auction_images(
            coin_id,
            request.auction_data_id,
        )
        return ImageDownloadResult(
            coin_id=coin_id,
            auctions_processed=1,
            images_downloaded=len(images),
            duplicates_skipped=0,
            errors=0,
        )
    else:
        result = await image_handler.download_all_auction_images(coin_id)
        return ImageDownloadResult(**result)


# =============================================================================
# Statistics Endpoints
# =============================================================================

@router.get("/summary", response_model=AuditSummary)
async def get_audit_summary(
    db: Session = Depends(get_db),
):
    """Get summary statistics for the audit dashboard."""
    audit_service = AuditService(db)
    summary = audit_service.get_audit_summary()
    return AuditSummary(**summary)


@router.get("/stats/discrepancies")
async def get_discrepancy_stats(
    db: Session = Depends(get_db),
):
    """Get detailed discrepancy statistics."""
    return audit_crud.get_discrepancy_stats(db)


@router.get("/stats/enrichments")
async def get_enrichment_stats(
    db: Session = Depends(get_db),
):
    """Get detailed enrichment statistics."""
    return audit_crud.get_enrichment_stats(db)


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get("/fields")
async def get_auditable_fields():
    """Get list of fields that can be audited."""
    from app.services.audit.audit_service import AUDIT_FIELD_MAPPING, ENRICHABLE_FIELDS
    
    return {
        "auditable_fields": list(AUDIT_FIELD_MAPPING.keys()),
        "enrichable_fields": ENRICHABLE_FIELDS,
    }


@router.get("/trust-levels")
async def get_trust_levels():
    """Get trust level configuration."""
    from app.services.audit.trust_config import TrustLevel, TRUST_MATRIX
    
    return {
        "levels": [
            {"value": level.value, "confidence": level.confidence_threshold}
            for level in TrustLevel
        ],
        "matrix_fields": list(TRUST_MATRIX.keys()),
    }


# =============================================================================
# Auto-Merge Endpoints
# =============================================================================

from pydantic import BaseModel, Field
from typing import Optional


class AutoMergePreviewRequest(BaseModel):
    """Request for auto-merge preview."""
    coin_ids: list[int] = Field(..., min_length=1, max_length=100)


class AutoMergeRequest(BaseModel):
    """Request for batch auto-merge."""
    coin_ids: list[int] = Field(..., min_length=1, max_length=100)
    confirmed: bool = False


class SingleMergeRequest(BaseModel):
    """Request for single coin auto-merge."""
    auction_data_id: Optional[int] = None


class VerifyFieldRequest(BaseModel):
    """Request to verify a field."""
    user_note: Optional[str] = None


@router.post("/auto-merge/preview")
async def preview_auto_merge(
    request: AutoMergePreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Preview what auto-merge would do without applying changes.
    
    Returns a dry-run result showing:
    - Fields that would be auto-filled (empty -> has value)
    - Fields that would be auto-updated (trust winner or safe conflict)
    - Fields that would be flagged for review
    - Fields skipped (user-verified)
    """
    from app.services.audit.auto_merge import AutoMergeService
    
    service = AutoMergeService(db)
    results = []
    
    summary = {
        "total_coins": len(request.coin_ids),
        "will_auto_fill": 0,
        "will_auto_update": 0,
        "will_flag": 0,
        "will_skip": 0,
    }
    
    for coin_id in request.coin_ids:
        result = service.merge_auction_to_coin(
            coin_id=coin_id,
            dry_run=True,
        )
        results.append(result.to_dict())
        
        summary["will_auto_fill"] += len(result.auto_filled)
        summary["will_auto_update"] += len(result.auto_updated)
        summary["will_flag"] += len(result.flagged)
        summary["will_skip"] += len(result.skipped)
    
    return {
        "summary": summary,
        "details": results,
    }


@router.post("/auto-merge")
async def batch_auto_merge(
    request: AutoMergeRequest,
    db: Session = Depends(get_db),
):
    """
    Run batch auto-merge on multiple coins.
    
    Safety features:
    - Max 100 coins per batch
    - Requires confirmation for batches > 10 coins
    - Returns batch_id for rollback capability
    
    Use /auto-merge/preview first to see what will change.
    """
    from app.services.audit.auto_merge import AutoMergeService
    from uuid import uuid4
    
    MAX_BATCH_SIZE = 100
    CONFIRM_THRESHOLD = 10
    
    if len(request.coin_ids) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size limited to {MAX_BATCH_SIZE} coins"
        )
    
    # Require confirmation for large batches
    if len(request.coin_ids) > CONFIRM_THRESHOLD and not request.confirmed:
        # Run preview to show what would happen
        service = AutoMergeService(db)
        preview_summary = {
            "will_auto_fill": 0,
            "will_auto_update": 0,
            "will_flag": 0,
        }
        
        for coin_id in request.coin_ids:
            result = service.merge_auction_to_coin(coin_id=coin_id, dry_run=True)
            preview_summary["will_auto_fill"] += len(result.auto_filled)
            preview_summary["will_auto_update"] += len(result.auto_updated)
            preview_summary["will_flag"] += len(result.flagged)
        
        return {
            "requires_confirmation": True,
            "preview": preview_summary,
            "message": f"This will modify {preview_summary['will_auto_fill'] + preview_summary['will_auto_update']} fields across {len(request.coin_ids)} coins. Set confirmed=true to proceed.",
        }
    
    # Run the merge
    service = AutoMergeService(db)
    batch_id = str(uuid4())
    
    results = []
    total_auto_filled = 0
    total_auto_updated = 0
    total_flagged = 0
    total_errors = 0
    
    for coin_id in request.coin_ids:
        result = service.merge_auction_to_coin(
            coin_id=coin_id,
            batch_id=batch_id,
            dry_run=False,
        )
        results.append(result.to_dict())
        
        total_auto_filled += len(result.auto_filled)
        total_auto_updated += len(result.auto_updated)
        total_flagged += len(result.flagged)
        total_errors += len(result.errors)
    
    return {
        "success": True,
        "batch_id": batch_id,
        "summary": {
            "processed": len(results),
            "auto_filled": total_auto_filled,
            "auto_updated": total_auto_updated,
            "flagged": total_flagged,
            "errors": total_errors,
        },
        "rollback_available": True,
        "details": results,
    }


@router.post("/coin/{coin_id}/auto-merge")
async def single_coin_auto_merge(
    coin_id: int,
    request: SingleMergeRequest = None,
    db: Session = Depends(get_db),
):
    """
    Run auto-merge for a single coin.
    
    Optionally specify auction_data_id to merge from specific auction.
    Otherwise uses all linked auction data.
    """
    from app.services.audit.auto_merge import AutoMergeService
    
    service = AutoMergeService(db)
    
    result = service.merge_auction_to_coin(
        coin_id=coin_id,
        auction_data_id=request.auction_data_id if request else None,
        dry_run=False,
    )
    
    if result.errors:
        raise HTTPException(status_code=404, detail=result.errors[0])
    
    return result.to_dict()


@router.post("/rollback/{batch_id}")
async def rollback_batch(
    batch_id: str,
    db: Session = Depends(get_db),
):
    """
    Rollback all changes from a batch auto-merge operation.
    
    This restores all fields to their previous values and records
    the rollback in the field history.
    """
    from app.services.audit.auto_merge import AutoMergeService
    
    service = AutoMergeService(db)
    result = service.rollback_batch(batch_id)
    
    if result.restored_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No changes found for batch {batch_id}"
        )
    
    return result.to_dict()


@router.post("/field/{coin_id}/{field}/verify")
async def verify_field(
    coin_id: int,
    field: str,
    request: VerifyFieldRequest = None,
    db: Session = Depends(get_db),
):
    """
    Mark a field as user-verified.
    
    User-verified fields are protected from auto-merge updates.
    This is useful when you've manually corrected an auction house error.
    """
    from app.services.audit.auto_merge import AutoMergeService
    
    service = AutoMergeService(db)
    success = service.verify_field(
        coin_id=coin_id,
        field=field,
        user_note=request.user_note if request else None,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    
    return {
        "success": True,
        "coin_id": coin_id,
        "field": field,
        "user_verified": True,
    }


@router.delete("/field/{coin_id}/{field}/verify")
async def unverify_field(
    coin_id: int,
    field: str,
    db: Session = Depends(get_db),
):
    """
    Remove user verification from a field.
    
    This allows the field to be updated by auto-merge again.
    """
    from app.services.audit.auto_merge import AutoMergeService
    
    service = AutoMergeService(db)
    success = service.unverify_field(coin_id=coin_id, field=field)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    
    return {
        "success": True,
        "coin_id": coin_id,
        "field": field,
        "user_verified": False,
    }


@router.get("/field-history/{coin_id}")
async def get_field_history(
    coin_id: int,
    field: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """
    Get field change history for a coin.
    
    Optionally filter by specific field.
    """
    from app.models.field_history import FieldHistory
    
    query = db.query(FieldHistory).filter(FieldHistory.coin_id == coin_id)
    
    if field:
        query = query.filter(FieldHistory.field_name == field)
    
    changes = query.order_by(FieldHistory.changed_at.desc()).limit(limit).all()
    
    return [
        {
            "id": c.id,
            "field": c.field_name,
            "old_value": c.old_value.get("value") if c.old_value else None,
            "new_value": c.new_value.get("value") if c.new_value else None,
            "old_source": c.old_source,
            "new_source": c.new_source,
            "change_type": c.change_type,
            "changed_at": c.changed_at.isoformat(),
            "changed_by": c.changed_by,
            "batch_id": c.batch_id,
            "conflict_type": c.conflict_type,
            "reason": c.reason,
        }
        for c in changes
    ]


@router.get("/batches")
async def list_merge_batches(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """
    List recent auto-merge batches for rollback management.
    """
    from app.models.field_history import FieldHistory
    from sqlalchemy import func, distinct
    
    # Get recent batches with stats
    batches = db.query(
        FieldHistory.batch_id,
        func.count(FieldHistory.id).label("changes"),
        func.count(distinct(FieldHistory.coin_id)).label("coins"),
        func.min(FieldHistory.changed_at).label("started_at"),
        func.max(FieldHistory.change_type).label("last_type"),
    ).filter(
        FieldHistory.batch_id.isnot(None),
        FieldHistory.change_type.in_(["auto_fill", "auto_update"]),
    ).group_by(
        FieldHistory.batch_id
    ).order_by(
        func.max(FieldHistory.changed_at).desc()
    ).limit(limit).all()
    
    return [
        {
            "batch_id": b.batch_id,
            "changes": b.changes,
            "coins_affected": b.coins,
            "started_at": b.started_at.isoformat() if b.started_at else None,
            "rollback_available": True,
        }
        for b in batches
    ]
