"""Catalog Router - dedicated non-LLM catalog endpoints."""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.infrastructure.services.catalogs.registry import CatalogRegistry
from src.infrastructure.services.catalogs.base import CatalogResult
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.orm import EnrichmentJobModel
from src.infrastructure.services.catalog_bulk_enrich import run_bulk_enrich

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/catalog", tags=["Catalog"])

class CatalogLookupRequest(BaseModel):
    reference: Optional[str] = None
    external_id: Optional[str] = None
    system: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


# --- Bulk enrich (Phase 1 stub; Phase 2 will add real implementation) ---

class BulkEnrichRequest(BaseModel):
    """Request body for bulk catalog enrichment. Matches frontend useCatalog.bulkEnrich."""
    coin_ids: Optional[List[int]] = None
    missing_fields: Optional[List[str]] = None
    reference_system: Optional[str] = None
    category: Optional[str] = None
    dry_run: Optional[bool] = True
    max_coins: Optional[int] = 50


class BulkEnrichResponse(BaseModel):
    """Response after starting bulk enrich. Matches frontend BulkEnrichResponse."""
    job_id: str
    total_coins: int
    status: str
    message: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Job status for polling. Matches frontend JobStatus."""
    job_id: str
    status: str  # "queued" | "running" | "completed" | "failed"
    progress: int
    total: int
    updated: int
    conflicts: int
    not_found: int
    errors: int
    results: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@router.post(
    "/lookup", 
    response_model=CatalogResult,
    summary="Lookup reference in official catalogs",
    description="Perform a real-time lookup. Can search by reference string (reconcile) or by external_id (fetch)."
)
async def lookup_catalog(request: CatalogLookupRequest):
    """
    Lookup a catalog reference or fetch by ID.
    """
    try:
        # Case 1: Fetch by Specific ID (hydration)
        if request.external_id:
            system = request.system
            
            # If system not provided, try to guess from ID
            if not system:
                if "ric" in request.external_id.lower(): system = "ric"
                elif "rrc" in request.external_id.lower(): system = "crawford"
                elif "rpc" in request.external_id.lower(): system = "rpc"
                else: system = "ric" # Default fallback
            
            logger.info(f"Catalog fetch: {request.external_id} (System: {system})")
            return await CatalogRegistry.get_by_id(system, request.external_id)

        # Case 2: Search by Reference String
        if not request.reference:
            raise HTTPException(status_code=400, detail="Either 'reference' or 'external_id' must be provided")

        # Detect system if not provided
        system = request.system
        if not system or system == "auto":
             system = CatalogRegistry.detect_system(request.reference)
        
        if not system:
             # Basic fallback if unknown: try RIC then RPC
             if "RPC" in request.reference.upper():
                 system = "rpc"
             else:
                 system = "ric"

        logger.info(f"Catalog lookup: {request.reference} (System: {system})")
        
        result = await CatalogRegistry.lookup(
            system=system,
            reference=request.reference,
            context=request.context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Catalog lookup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# --- Bulk enrich (Phase 2: real implementation with enrichment_jobs and BackgroundTasks) ---

@router.post(
    "/bulk-enrich",
    response_model=BulkEnrichResponse,
    summary="Start bulk catalog enrichment",
    description="Enqueue bulk catalog enrichment job; poll GET /job/{job_id} for status.",
)
async def bulk_enrich(
    request: BulkEnrichRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job_id = str(uuid.uuid4())
    total = (
        len(request.coin_ids) if (request.coin_ids and len(request.coin_ids) > 0)
        else (request.max_coins or 50)
    )
    job = EnrichmentJobModel(
        id=job_id,
        status="queued",
        total=total,
        progress=0,
        updated=0,
        conflicts=0,
        not_found=0,
        errors=0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    logger.info("Bulk enrich job %s queued (total=%s)", job_id, total)
    background_tasks.add_task(run_bulk_enrich, job_id, request, SessionLocal)
    return BulkEnrichResponse(
        job_id=job_id,
        total_coins=total,
        status="queued",
        message=None,
    )


@router.get(
    "/job/{job_id}",
    response_model=JobStatusResponse,
    summary="Get bulk enrichment job status",
    description="Poll for job progress; status in queued|running|completed|failed.",
)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.get(EnrichmentJobModel, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    results = None
    if job.result_summary:
        try:
            results = json.loads(job.result_summary)
        except Exception:
            results = None
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        total=job.total,
        updated=job.updated,
        conflicts=job.conflicts,
        not_found=job.not_found,
        errors=job.errors,
        results=results,
        error_message=job.error_message,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )
