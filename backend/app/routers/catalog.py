"""Catalog API endpoints for reference lookups and enrichment."""
import asyncio
import uuid
import logging
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Coin, CoinReference, ReferenceType, ReferenceMatchAttempt
from app.schemas.catalog import (
    LookupRequest, LookupResponse, CandidateResponse,
    EnrichRequest, EnrichResponse, EnrichmentDiffResponse, ConflictResponse,
    BulkEnrichRequest, BulkEnrichResponse, JobStatusResponse,
    ReferenceTypeResponse
)
from app.services.reference_parser import parser as reference_parser
from app.services.catalogs.registry import CatalogRegistry
from app.services.catalogs.base import CatalogResult, CatalogPayload
from app.services.diff_enricher import enricher, EnrichmentDiff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/catalog", tags=["catalog"])

# Simple in-memory job store (for personal app; use Redis for production)
_jobs: dict[str, dict] = {}

# Rate limiting
_last_request_time: float = 0
RATE_LIMIT_SECONDS = 1.0  # 1 request per second to external APIs


async def rate_limit():
    """Simple rate limiting for external API calls."""
    global _last_request_time
    now = asyncio.get_event_loop().time()
    elapsed = now - _last_request_time
    if elapsed < RATE_LIMIT_SECONDS:
        await asyncio.sleep(RATE_LIMIT_SECONDS - elapsed)
    _last_request_time = asyncio.get_event_loop().time()


def get_or_create_reference_type(
    db: Session,
    system: str,
    local_ref: str,
    normalized: str
) -> ReferenceType:
    """Get or create a ReferenceType record."""
    # Try to find existing
    ref_type = db.query(ReferenceType).filter(
        ReferenceType.system == system,
        ReferenceType.local_ref_normalized == normalized
    ).first()
    
    if ref_type:
        return ref_type
    
    # Create new
    ref_type = ReferenceType(
        system=system,
        local_ref=local_ref,
        local_ref_normalized=normalized,
        lookup_status="pending"
    )
    db.add(ref_type)
    db.commit()
    db.refresh(ref_type)
    return ref_type


@router.post("/lookup", response_model=LookupResponse)
async def lookup_reference(
    request: LookupRequest,
    db: Session = Depends(get_db)
):
    """
    Lookup a reference in external catalogs.
    
    Returns cached result if fresh, otherwise fetches from API.
    """
    # Determine reference string
    if request.raw_reference:
        raw_ref = request.raw_reference
    elif request.system and request.number:
        vol = f" {request.volume}" if request.volume else ""
        raw_ref = f"{request.system.upper()}{vol} {request.number}"
    else:
        raise HTTPException(status_code=400, detail="Must provide raw_reference or system+number")
    
    # Parse reference
    parsed = reference_parser.parse(raw_ref)
    
    if not parsed.system:
        return LookupResponse(
            status="error",
            error_message=f"Could not parse reference: {raw_ref}"
        )
    
    # Check for cached result
    if parsed.normalized:
        ref_type = db.query(ReferenceType).filter(
            ReferenceType.system == parsed.system,
            ReferenceType.local_ref_normalized == parsed.normalized
        ).first()
        
        if ref_type and ref_type.lookup_status == "success":
            service = CatalogRegistry.get_service(parsed.system)
            if service and service.is_cache_fresh(ref_type.last_lookup):
                # Return cached result
                return LookupResponse(
                    status="success",
                    external_id=ref_type.external_id,
                    external_url=ref_type.external_url,
                    confidence=float(ref_type.lookup_confidence) if ref_type.lookup_confidence else 0,
                    payload=ref_type.payload,
                    reference_type_id=ref_type.id,
                    last_lookup=ref_type.last_lookup,
                    cache_hit=True
                )
    
    # Rate limit before external call
    await rate_limit()
    
    # Lookup from catalog
    result = await CatalogRegistry.lookup(
        system=parsed.system,
        reference=raw_ref,
        context=request.context
    )
    
    # Store result in ReferenceType
    if parsed.normalized:
        ref_type = get_or_create_reference_type(
            db, parsed.system, raw_ref, parsed.normalized
        )
        
        ref_type.lookup_status = result.status
        ref_type.lookup_confidence = result.confidence
        ref_type.last_lookup = datetime.utcnow()
        ref_type.external_id = result.external_id
        ref_type.external_url = result.external_url
        ref_type.error_message = result.error_message
        
        if result.payload:
            ref_type.payload = result.payload
        if result.raw:
            # Store raw JSON-LD for debugging
            pass
        
        db.commit()
        
        # Log the attempt
        attempt = ReferenceMatchAttempt(
            reference_type_id=ref_type.id,
            query_sent=raw_ref,
            context_used=request.context,
            result_status=result.status,
            confidence=result.confidence,
            candidates_returned=len(result.candidates) if result.candidates else 0
        )
        db.add(attempt)
        db.commit()
    
    # Build response
    candidates = None
    if result.candidates:
        candidates = [
            CandidateResponse(
                external_id=c.external_id,
                external_url=c.external_url,
                confidence=c.confidence,
                name=c.name,
                description=c.description
            )
            for c in result.candidates
        ]
    
    return LookupResponse(
        status=result.status,
        external_id=result.external_id,
        external_url=result.external_url,
        confidence=result.confidence,
        candidates=candidates,
        payload=result.payload,
        error_message=result.error_message,
        reference_type_id=ref_type.id if parsed.normalized else None,
        last_lookup=datetime.utcnow(),
        cache_hit=False
    )


@router.post("/enrich/{coin_id}", response_model=EnrichResponse)
async def enrich_coin(
    coin_id: int,
    request: EnrichRequest,
    db: Session = Depends(get_db)
):
    """
    Compute enrichment diff for a coin.
    
    Fetches data from all linked references and computes diff.
    If dry_run=False, applies fills and approved conflicts.
    """
    # Get coin with references
    coin = db.query(Coin).filter(Coin.id == coin_id).first()
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    # Collect catalog data from all references
    all_payloads: list[CatalogPayload] = []
    
    for ref in coin.references:
        # Determine reference string
        if ref.reference_type:
            raw_ref = ref.reference_type.local_ref
            system = ref.reference_type.system
            
            # Use cached payload if available
            if ref.reference_type.payload:
                all_payloads.append(CatalogPayload(**ref.reference_type.payload))
                continue
        elif ref.raw_reference:
            parsed = reference_parser.parse(ref.raw_reference)
            raw_ref = ref.raw_reference
            system = parsed.system
        elif ref.system and ref.number:
            # Use legacy fields (system, volume, number)
            system = ref.system.value if hasattr(ref.system, 'value') else str(ref.system)
            vol_str = f" {ref.volume}" if ref.volume else ""
            raw_ref = f"{system.upper()}{vol_str} {ref.number}"
        else:
            continue
        
        if not system:
            continue
        
        # Rate limit and lookup
        await rate_limit()
        
        # Build context from coin
        context = {
            "ruler": coin.issuing_authority,
            "denomination": coin.denomination,
            "mint": coin.mint.name if coin.mint else None,
            "date_from": coin.mint_year_start,
            "date_to": coin.mint_year_end,
        }
        
        result = await CatalogRegistry.lookup(system, raw_ref, context)
        
        if result.payload:
            all_payloads.append(CatalogPayload(**result.payload))
        elif result.status == "ambiguous" and result.candidates:
            # Try to fetch data from the best candidate
            service = CatalogRegistry.get_service(system)
            if service and result.candidates[0].external_id:
                try:
                    jsonld = await service.fetch_type_data(result.candidates[0].external_id)
                    if jsonld:
                        payload = service.parse_payload(jsonld)
                        all_payloads.append(payload)
                except Exception as e:
                    logger.warning(f"Failed to fetch type data for best candidate: {e}")
    
    if not all_payloads:
        return EnrichResponse(
            success=True,
            coin_id=coin_id,
            diff=EnrichmentDiffResponse(
                fills={},
                conflicts={},
                unchanged=[],
                fill_count=0,
                conflict_count=0,
                unchanged_count=0,
                has_changes=False
            ),
            error="No catalog data found for this coin's references"
        )
    
    # Merge payloads and compute diff
    merged_payload = enricher.merge_multiple_payloads(all_payloads)
    diff = enricher.compute_diff(coin, merged_payload)
    
    # Apply if not dry run
    if not request.dry_run:
        result = enricher.apply_diff(
            db, coin, diff,
            apply_conflicts=request.apply_conflicts,
            dry_run=False
        )
        
        return EnrichResponse(
            success=result.success,
            coin_id=coin_id,
            diff=EnrichmentDiffResponse(
                fills=diff.fills,
                conflicts={k: ConflictResponse(**v.model_dump()) for k, v in diff.conflicts.items()},
                unchanged=diff.unchanged,
                fill_count=diff.fill_count,
                conflict_count=diff.conflict_count,
                unchanged_count=diff.unchanged_count,
                has_changes=diff.has_changes
            ),
            applied_fills=result.applied_fills,
            applied_conflicts=result.applied_conflicts,
            error=result.error
        )
    
    # Return diff for preview
    return EnrichResponse(
        success=True,
        coin_id=coin_id,
        diff=EnrichmentDiffResponse(
            fills=diff.fills,
            conflicts={k: ConflictResponse(**v.model_dump()) for k, v in diff.conflicts.items()},
            unchanged=diff.unchanged,
            fill_count=diff.fill_count,
            conflict_count=diff.conflict_count,
            unchanged_count=diff.unchanged_count,
            has_changes=diff.has_changes
        )
    )


@router.post("/bulk-enrich", response_model=BulkEnrichResponse)
async def bulk_enrich(
    request: BulkEnrichRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Queue bulk enrichment job.
    
    Filters coins based on request parameters and enriches them.
    Returns job_id for status polling.
    """
    # Build query
    query = db.query(Coin)
    
    if request.coin_ids:
        query = query.filter(Coin.id.in_(request.coin_ids))
    
    if request.category:
        from app.models.coin import Category
        try:
            cat = Category(request.category.lower())
            query = query.filter(Coin.category == cat)
        except ValueError:
            pass
    
    # Get coin IDs
    coins = query.limit(request.max_coins).all()
    coin_ids = [c.id for c in coins]
    
    if not coin_ids:
        return BulkEnrichResponse(
            job_id="",
            total_coins=0,
            status="completed",
            message="No coins match the filter criteria"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "total": len(coin_ids),
        "coin_ids": coin_ids,
        "dry_run": request.dry_run,
        "results": [],
        "updated": 0,
        "conflicts": 0,
        "not_found": 0,
        "errors": 0,
        "started_at": None,
        "completed_at": None
    }
    
    # Queue background task
    background_tasks.add_task(
        run_bulk_enrichment,
        job_id=job_id,
        coin_ids=coin_ids,
        dry_run=request.dry_run
    )
    
    return BulkEnrichResponse(
        job_id=job_id,
        total_coins=len(coin_ids),
        status="queued",
        message=f"Queued enrichment for {len(coin_ids)} coins"
    )


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Poll bulk job progress."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _jobs[job_id]
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        total=job["total"],
        updated=job["updated"],
        conflicts=job["conflicts"],
        not_found=job["not_found"],
        errors=job["errors"],
        results=job["results"][-10:] if job["results"] else None,  # Last 10 results
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at")
    )


async def run_bulk_enrichment(
    job_id: str,
    coin_ids: list[int],
    dry_run: bool
):
    """Background task for bulk enrichment."""
    from app.database import SessionLocal
    
    job = _jobs[job_id]
    job["status"] = "running"
    job["started_at"] = datetime.utcnow()
    
    db = SessionLocal()
    
    try:
        for i, coin_id in enumerate(coin_ids):
            job["progress"] = i + 1
            
            try:
                coin = db.query(Coin).filter(Coin.id == coin_id).first()
                if not coin:
                    job["errors"] += 1
                    continue
                
                # Collect payloads from references
                all_payloads: list[CatalogPayload] = []
                
                for ref in coin.references:
                    if ref.reference_type and ref.reference_type.payload:
                        all_payloads.append(CatalogPayload(**ref.reference_type.payload))
                    elif ref.raw_reference:
                        parsed = reference_parser.parse(ref.raw_reference)
                        if parsed.system:
                            await rate_limit()
                            result = await CatalogRegistry.lookup(
                                parsed.system,
                                ref.raw_reference,
                                {"ruler": coin.issuing_authority}
                            )
                            if result.payload:
                                all_payloads.append(CatalogPayload(**result.payload))
                
                if not all_payloads:
                    job["not_found"] += 1
                    job["results"].append({
                        "coin_id": coin_id,
                        "status": "not_found"
                    })
                    continue
                
                # Compute and apply diff
                merged = enricher.merge_multiple_payloads(all_payloads)
                diff = enricher.compute_diff(coin, merged)
                
                if diff.conflict_count > 0:
                    job["conflicts"] += 1
                
                if not dry_run and diff.fill_count > 0:
                    result = enricher.apply_diff(db, coin, diff, dry_run=False)
                    if result.success:
                        job["updated"] += 1
                    else:
                        job["errors"] += 1
                elif diff.fill_count > 0:
                    job["updated"] += 1  # Would have updated
                
                job["results"].append({
                    "coin_id": coin_id,
                    "status": "success",
                    "fills": diff.fill_count,
                    "conflicts": diff.conflict_count
                })
                
            except Exception as e:
                logger.error(f"Bulk enrich error for coin {coin_id}: {e}")
                job["errors"] += 1
                job["results"].append({
                    "coin_id": coin_id,
                    "status": "error",
                    "error": str(e)
                })
            
            # Small delay between coins
            await asyncio.sleep(0.1)
        
        job["status"] = "completed"
        job["completed_at"] = datetime.utcnow()
        
    except Exception as e:
        logger.error(f"Bulk enrichment failed: {e}")
        job["status"] = "failed"
        job["error_message"] = str(e)
    finally:
        db.close()


@router.get("/reference-types", response_model=list[ReferenceTypeResponse])
async def list_reference_types(
    system: str | None = None,
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List reference types with optional filtering."""
    query = db.query(ReferenceType)
    
    if system:
        query = query.filter(ReferenceType.system == system.lower())
    if status:
        query = query.filter(ReferenceType.lookup_status == status)
    
    ref_types = query.order_by(ReferenceType.last_lookup.desc()).limit(limit).all()
    
    return [ReferenceTypeResponse.model_validate(rt) for rt in ref_types]
