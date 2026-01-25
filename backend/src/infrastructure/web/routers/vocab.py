from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from src.infrastructure.persistence.database import get_db, SessionLocal
from src.infrastructure.persistence.models_vocab import IssuerModel, IssuerAliasModel
from src.infrastructure.services.vocab_normalizer import VocabNormalizer, NormalizationResult
from src.infrastructure.services.vocab_sync import VocabSyncService

router = APIRouter(prefix="/api/vocab", tags=["vocabulary"])

# --- Response Models ---
class IssuerResponse(BaseModel):
    id: int
    canonical_name: str
    nomisma_id: str
    issuer_type: Optional[str]
    reign_start: Optional[int]
    reign_end: Optional[int]

class NormalizationResponse(BaseModel):
    success: bool
    canonical_id: Optional[int]
    canonical_name: Optional[str]
    method: Optional[str]
    confidence: float
    needs_review: bool

class SyncResponse(BaseModel):
    status: str
    message: str

class ListResponse(BaseModel):
    items: List[IssuerResponse]
    total: int
    page: int
    per_page: int

# --- Endpoints ---

@router.get("/issuers", response_model=ListResponse)
def list_issuers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(IssuerModel)
    
    if search:
        # Simple search for now
        query = query.filter(IssuerModel.canonical_name.ilike(f"%{search}%"))
        
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return ListResponse(
        items=[IssuerResponse(
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

@router.post("/normalize/issuer", response_model=NormalizationResponse)
def normalize_issuer_endpoint(
    raw: str,
    db: Session = Depends(get_db)
):
    normalizer = VocabNormalizer(db)
    result = normalizer.normalize_issuer(raw)
    
    return NormalizationResponse(
        success=result.success,
        canonical_id=result.canonical_id,
        canonical_name=result.canonical_name,
        method=result.method.value if result.method else None,
        confidence=result.confidence,
        needs_review=result.needs_review
    )

@router.post("/sync/nomisma", status_code=status.HTTP_202_ACCEPTED, response_model=SyncResponse)
async def trigger_sync_nomisma(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    background_tasks.add_task(run_sync)
    return SyncResponse(status="started", message="Nomisma sync started in background")

async def run_sync():
    # Use a fresh session for background task
    db = SessionLocal()
    try:
        service = VocabSyncService(db)
        await service.sync_nomisma_issuers()
    finally:
        db.close()
