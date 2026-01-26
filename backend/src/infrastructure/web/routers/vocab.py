"""
Vocabulary API Router (V3)

This module provides the REST API endpoints for the unified controlled vocabulary system.
Supports search, normalization, sync, bulk operations, and review queue management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging

from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.web.dependencies import get_db, get_vocab_repo
from src.infrastructure.repositories.vocab_repository import SqlAlchemyVocabRepository
from src.domain.vocab import VocabType, IVocabRepository

# Legacy imports for backward compatibility
from src.infrastructure.persistence.models_vocab import IssuerModel, IssuerAliasModel
from src.infrastructure.services.vocab_normalizer import VocabNormalizer
from src.infrastructure.services.vocab_sync import VocabSyncService

logger = logging.getLogger(__name__)

# Create routers - one for V2 (new) and keep legacy for backward compatibility
router = APIRouter(prefix="/api/v2/vocab", tags=["Vocabulary V3"])
legacy_router = APIRouter(prefix="/api/vocab", tags=["Vocabulary (Legacy)"])


# =============================================================================
# V3 Response/Request Models
# =============================================================================

class VocabTermResponse(BaseModel):
    """Response model for a vocabulary term."""
    id: int
    vocab_type: str
    canonical_name: str
    nomisma_uri: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NormalizeRequest(BaseModel):
    """Request model for normalization."""
    raw: str = Field(..., min_length=1, description="Raw text to normalize")
    vocab_type: str = Field(..., description="Vocabulary type (issuer, mint, denomination, dynasty)")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class NormalizeResponse(BaseModel):
    """Response model for normalization result."""
    success: bool
    term: Optional[VocabTermResponse] = None
    method: str = ""
    confidence: float = 0.0
    needs_review: bool = False
    alternatives: List[VocabTermResponse] = Field(default_factory=list)


class SyncResponse(BaseModel):
    """Response model for sync operations."""
    status: str
    vocab_type: str
    added: int = 0
    unchanged: int = 0
    errors: int = 0


class BulkNormalizeRequest(BaseModel):
    """Request model for bulk normalization."""
    coin_ids: Optional[List[int]] = None
    vocab_types: List[str] = Field(default=["issuer", "mint", "denomination"])


class ReviewQueueItem(BaseModel):
    """Response model for review queue item."""
    id: int
    coin_id: int
    field_name: str
    raw_value: str
    vocab_term_id: Optional[int] = None
    confidence: Optional[float] = None
    method: Optional[str] = None
    suggested_name: Optional[str] = None


# =============================================================================
# V3 API Endpoints
# =============================================================================

@router.get("/search/{vocab_type}", response_model=List[VocabTermResponse])
def search_vocab(
    vocab_type: str,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """
    Search vocabulary terms using FTS5 full-text search.
    
    Supports prefix matching (e.g., "Aug" matches "Augustus").
    Results are cached for 1 hour.
    """
    try:
        vtype = VocabType(vocab_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid vocab_type. Must be one of: {[t.value for t in VocabType]}"
        )
    
    terms = repo.search(vtype, q, limit)
    
    return [VocabTermResponse(
        id=t.id,
        vocab_type=t.vocab_type.value,
        canonical_name=t.canonical_name,
        nomisma_uri=t.nomisma_uri,
        metadata=t.metadata or {}
    ) for t in terms]


@router.get("/terms/{vocab_type}", response_model=List[VocabTermResponse])
def list_vocab_terms(
    vocab_type: str,
    limit: int = Query(100, ge=1, le=1000),
    repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """List all vocabulary terms of a given type."""
    try:
        vtype = VocabType(vocab_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid vocab_type. Must be one of: {[t.value for t in VocabType]}"
        )
    
    terms = repo.get_all(vtype, limit)
    
    return [VocabTermResponse(
        id=t.id,
        vocab_type=t.vocab_type.value,
        canonical_name=t.canonical_name,
        nomisma_uri=t.nomisma_uri,
        metadata=t.metadata or {}
    ) for t in terms]


@router.get("/terms/{vocab_type}/{term_id}", response_model=VocabTermResponse)
def get_vocab_term(
    vocab_type: str,
    term_id: int,
    repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """Get a specific vocabulary term by ID."""
    term = repo.get_by_id(term_id)
    
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    if term.vocab_type.value != vocab_type:
        raise HTTPException(status_code=404, detail="Term not found for this vocab_type")
    
    return VocabTermResponse(
        id=term.id,
        vocab_type=term.vocab_type.value,
        canonical_name=term.canonical_name,
        nomisma_uri=term.nomisma_uri,
        metadata=term.metadata or {}
    )


@router.post("/normalize", response_model=NormalizeResponse)
def normalize_vocab(
    req: NormalizeRequest,
    repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """
    Normalize raw text to a canonical vocabulary term.
    
    Uses a chain of matching strategies:
    1. Exact match (case-sensitive) → confidence 1.0
    2. Case-insensitive exact match → confidence 0.98
    3. Alias match → confidence 0.97
    4. FTS5 fuzzy match → confidence 0.80-0.99
    5. Nomisma reconciliation API → confidence 0.85
    
    Returns needs_review=True if confidence < 0.92 or no match found.
    """
    try:
        vtype = VocabType(req.vocab_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid vocab_type. Must be one of: {[t.value for t in VocabType]}"
        )
    
    result = repo.normalize(req.raw, vtype, req.context)
    
    term_resp = None
    if result.term:
        term_resp = VocabTermResponse(
            id=result.term.id,
            vocab_type=result.term.vocab_type.value,
            canonical_name=result.term.canonical_name,
            nomisma_uri=result.term.nomisma_uri,
            metadata=result.term.metadata or {}
        )
    
    alternatives = []
    for alt in result.alternatives:
        alternatives.append(VocabTermResponse(
            id=alt.id,
            vocab_type=alt.vocab_type.value,
            canonical_name=alt.canonical_name,
            nomisma_uri=alt.nomisma_uri,
            metadata=alt.metadata or {}
        ))
    
    return NormalizeResponse(
        success=result.success,
        term=term_resp,
        method=result.method,
        confidence=result.confidence,
        needs_review=result.needs_review,
        alternatives=alternatives
    )


@router.post("/sync/{vocab_type}", response_model=SyncResponse)
def sync_nomisma(
    vocab_type: str,
    repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """
    Sync vocabulary from Nomisma SPARQL endpoint.
    
    Only supports issuer, mint, and denomination types.
    This is a synchronous operation that may take 30-60 seconds.
    """
    try:
        vtype = VocabType(vocab_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid vocab_type. Must be one of: {[t.value for t in VocabType]}"
        )
    
    if vtype not in (VocabType.ISSUER, VocabType.MINT, VocabType.DENOMINATION):
        raise HTTPException(
            status_code=400,
            detail=f"Sync only supported for: issuer, mint, denomination"
        )
    
    try:
        stats = repo.sync_nomisma(vtype)
        # Note: Transaction is auto-committed by get_db dependency
        
        return SyncResponse(
            status="complete",
            vocab_type=vocab_type,
            added=stats.get("added", 0),
            unchanged=stats.get("unchanged", 0),
            errors=stats.get("errors", 0)
        )
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
def bulk_normalize(
    req: BulkNormalizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Bulk normalize coins (runs in background).
    
    If coin_ids is None, normalizes all coins.
    Returns immediately with a status message.
    """
    background_tasks.add_task(
        run_bulk_normalize, 
        req.coin_ids, 
        req.vocab_types
    )
    
    return {
        "status": "started",
        "message": "Bulk normalization started in background",
        "coin_ids": req.coin_ids,
        "vocab_types": req.vocab_types
    }


@router.get("/review", response_model=List[ReviewQueueItem])
def get_review_queue(
    status_filter: str = Query("pending_review", alias="status"),
    limit: int = Query(50, ge=1, le=200),
    repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """Get items needing manual review."""
    items = repo.get_review_queue(status_filter, limit)
    
    return [ReviewQueueItem(**item) for item in items]


@router.post("/review/{assignment_id}/approve")
def approve_review(
    assignment_id: int,
    repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """Approve a pending vocabulary assignment."""
    repo.approve_assignment(assignment_id)
    # Note: Transaction is auto-committed by get_db dependency
    return {"status": "approved", "id": assignment_id}


@router.post("/review/{assignment_id}/reject")
def reject_review(
    assignment_id: int,
    repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """Reject a pending vocabulary assignment."""
    repo.reject_assignment(assignment_id)
    # Note: Transaction is auto-committed by get_db dependency
    return {"status": "rejected", "id": assignment_id}


# =============================================================================
# Background Tasks
# =============================================================================

def run_bulk_normalize(coin_ids: Optional[List[int]], vocab_types: List[str]):
    """Background task for bulk normalization."""
    db = SessionLocal()
    try:
        repo = SqlAlchemyVocabRepository(db)
        
        # Get coins to normalize
        if coin_ids:
            # Use parameterized query to prevent SQL injection
            placeholders = ",".join([f":id_{i}" for i in range(len(coin_ids))])
            params = {f"id_{i}": cid for i, cid in enumerate(coin_ids)}
            query = text(f"SELECT id, issuer, mint FROM coins_v2 WHERE id IN ({placeholders})")
            result = db.execute(query, params)
        else:
            query = text("SELECT id, issuer, mint FROM coins_v2")
            result = db.execute(query)
        coins = result.fetchall()
        
        stats = {"processed": 0, "matched": 0, "review": 0, "failed": 0}
        
        field_map = {
            "issuer": ("issuer", VocabType.ISSUER, "issuer_term_id"),
            "mint": ("mint", VocabType.MINT, "mint_term_id"),
        }
        
        for coin_row in coins:
            coin_id = coin_row[0]
            
            for vtype_str in vocab_types:
                if vtype_str not in field_map:
                    continue
                
                raw_field, vtype, fk_field = field_map[vtype_str]
                raw_value = getattr(coin_row, raw_field, None) if hasattr(coin_row, raw_field) else coin_row[1 if raw_field == "issuer" else 2]
                
                if not raw_value:
                    continue
                
                try:
                    norm_result = repo.normalize(raw_value, vtype, {"coin_id": coin_id})
                    
                    # Record assignment
                    repo.record_assignment(coin_id, vtype_str, raw_value, norm_result)
                    
                    if norm_result.success and not norm_result.needs_review:
                        # Update coin FK
                        db.execute(
                            text(f"UPDATE coins_v2 SET {fk_field} = :term_id WHERE id = :coin_id"),
                            {"term_id": norm_result.term.id, "coin_id": coin_id}
                        )
                        stats["matched"] += 1
                    elif norm_result.needs_review:
                        stats["review"] += 1
                    else:
                        stats["failed"] += 1
                        
                except Exception as e:
                    logger.error(f"Error normalizing coin {coin_id} {vtype_str}: {e}")
                    stats["failed"] += 1
            
            stats["processed"] += 1
        
        db.commit()
        logger.info(f"Bulk normalize complete: {stats}")
        
    except Exception as e:
        logger.error(f"Bulk normalize failed: {e}")
        db.rollback()
    finally:
        db.close()


# =============================================================================
# Legacy Endpoints (Backward Compatibility)
# =============================================================================

# Legacy response models
class LegacyIssuerResponse(BaseModel):
    id: int
    canonical_name: str
    nomisma_id: str
    issuer_type: Optional[str]
    reign_start: Optional[int]
    reign_end: Optional[int]

class LegacyNormalizationResponse(BaseModel):
    success: bool
    canonical_id: Optional[int]
    canonical_name: Optional[str]
    method: Optional[str]
    confidence: float
    needs_review: bool

class LegacySyncResponse(BaseModel):
    status: str
    message: str

class LegacyListResponse(BaseModel):
    items: List[LegacyIssuerResponse]
    total: int
    page: int
    per_page: int


@legacy_router.get("/issuers", response_model=LegacyListResponse)
def legacy_list_issuers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Legacy endpoint - list issuers from old schema."""
    query = db.query(IssuerModel)
    
    if search:
        query = query.filter(IssuerModel.canonical_name.ilike(f"%{search}%"))
        
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return LegacyListResponse(
        items=[LegacyIssuerResponse(
            id=i.id,
            canonical_name=i.canonical_name,
            nomisma_id=i.nomisma_id,
            issuer_type=i.issuer_type,
            reign_start=i.reign_start,
            reign_end=i.reign_end
        ) for i in items],
        total=total,
        page=page,
        per_page=per_page
    )


@legacy_router.post("/normalize/issuer", response_model=LegacyNormalizationResponse)
def legacy_normalize_issuer(
    raw: str,
    db: Session = Depends(get_db)
):
    """Legacy endpoint - normalize issuer using old normalizer."""
    normalizer = VocabNormalizer(db)
    result = normalizer.normalize_issuer(raw)
    
    return LegacyNormalizationResponse(
        success=result.success,
        canonical_id=result.canonical_id,
        canonical_name=result.canonical_name,
        method=result.method.value if result.method else None,
        confidence=result.confidence,
        needs_review=result.needs_review
    )


@legacy_router.post("/sync/nomisma/issuers", status_code=status.HTTP_202_ACCEPTED, response_model=LegacySyncResponse)
async def legacy_sync_issuers(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Legacy endpoint - sync issuers from Nomisma."""
    background_tasks.add_task(run_legacy_sync_issuers)
    return LegacySyncResponse(status="started", message="Nomisma issuers sync started in background")


@legacy_router.post("/sync/nomisma/mints", status_code=status.HTTP_202_ACCEPTED, response_model=LegacySyncResponse)
async def legacy_sync_mints(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Legacy endpoint - sync mints from Nomisma."""
    background_tasks.add_task(run_legacy_sync_mints)
    return LegacySyncResponse(status="started", message="Nomisma mints sync started in background")


async def run_legacy_sync_issuers():
    """Background task for legacy issuer sync."""
    db = SessionLocal()
    try:
        service = VocabSyncService(db)
        await service.sync_nomisma_issuers()
    finally:
        db.close()


async def run_legacy_sync_mints():
    """Background task for legacy mint sync."""
    db = SessionLocal()
    try:
        service = VocabSyncService(db)
        await service.sync_nomisma_mints()
    finally:
        db.close()
