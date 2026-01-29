from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Any
from datetime import datetime
import hashlib
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.repositories import ICoinRepository
from src.domain.audit import AuditEngine, ExternalAuctionData
from src.domain.strategies.grade_strategy import GradeStrategy
from src.domain.strategies.attribution_strategy import AttributionStrategy
from src.domain.strategies.physics_strategy import PhysicsStrategy
from src.domain.strategies.date_strategy import DateStrategy
from src.domain.enrichment import EnrichmentApplication
from src.infrastructure.web.dependencies import get_db, get_coin_repo, get_apply_enrichment_service
from src.application.services.apply_enrichment import ApplyEnrichmentService
from src.domain.coin import Metal, Category, GradingState, GradeService, CoinImage, Dimensions, Attribution, GradingDetails, AcquisitionDetails
from src.infrastructure.persistence.orm import CoinModel, AuctionDataModel

router = APIRouter(prefix="/api/v2/audit", tags=["audit"])

# --- Enrichments list API (Phase 5) ---

def _synthetic_id(coin_id: int, auction_data_id: int, field_name: str) -> int:
    """Deterministic numeric id for computed enrichment opportunities."""
    raw = f"{coin_id}_{auction_data_id}_{field_name}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:8], 16) % (2**31 - 1)

def _empty(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return (v or "").strip() == ""
    return False

def _non_empty(v: Any) -> bool:
    return not _empty(v)

class EnrichmentResponse(BaseModel):
    """Single enrichment opportunity - matches frontend Enrichment shape."""
    id: int
    coin_id: int
    auction_data_id: Optional[int] = None
    audit_run_id: Optional[int] = None
    field_name: str
    suggested_value: str
    source_house: str
    trust_level: str = "medium"
    confidence: Optional[float] = 0.8
    auto_applicable: bool = True
    status: str = "pending"
    applied: bool = False
    applied_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str
    source_url: Optional[str] = None
    auction_images: List[str] = Field(default_factory=list)

class EnrichmentsListResponse(BaseModel):
    items: List[EnrichmentResponse]
    total: int
    page: int
    per_page: int
    pages: int

class EnrichmentApplyBody(BaseModel):
    coin_id: int
    field_name: str
    value: str

class EnrichmentBulkApplyBody(BaseModel):
    applications: List[EnrichmentApplyBody]

class DiscrepancyResponse(BaseModel):
    field: str
    current_value: str
    auction_value: str
    confidence: float
    source: str

class AuditResultResponse(BaseModel):
    coin_id: int
    has_issues: bool
    discrepancies: List[DiscrepancyResponse]

class ApplyEnrichmentRequest(BaseModel):
    field: str
    value: str


@router.get("/enrichments", response_model=EnrichmentsListResponse)
def list_enrichments(
    status: Optional[str] = Query(None, description="pending | applied | rejected | ignored"),
    trust_level: Optional[str] = Query(None),
    coin_id: Optional[int] = Query(None),
    auto_applicable: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List enrichment opportunities: coin field empty and auction_data has value.
    Computed on the fly from coins that have linked auction_data. No new table for MVP.
    """
    q = (
        db.query(AuctionDataModel, CoinModel)
        .join(CoinModel, AuctionDataModel.coin_id == CoinModel.id)
        .where(AuctionDataModel.coin_id.isnot(None))
    )
    if coin_id is not None:
        q = q.where(AuctionDataModel.coin_id == coin_id)

    rows = q.all()
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    opportunities: List[EnrichmentResponse] = []

    # Map (auction_field_name, coin_attr_path) for "empty coin / non-empty auction" opportunities
    field_checks = [
        ("issuer", lambda c, a: (c.issuer, a.issuer)),
        ("mint", lambda c, a: (c.mint, a.mint)),
        ("year_start", lambda c, a: (c.year_start, a.year_start)),
        ("year_end", lambda c, a: (c.year_end, a.year_end)),
        ("grade", lambda c, a: (c.grade, a.grade)),
    ]

    for auction_row, coin_row in rows:
        for fname, get_vals in field_checks:
            coin_val, auction_val = get_vals(coin_row, auction_row)
            if _empty(coin_val) and _non_empty(auction_val):
                sug = str(auction_val).strip() if auction_val is not None else ""
                if not sug:
                    continue
                eid = _synthetic_id(coin_row.id, auction_row.id, fname)
                # Respect status filter: MVP only has "pending" (computed on the fly)
                if status is not None and status not in ("pending", "all", ""):
                    continue
                if trust_level is not None and trust_level != "medium":
                    continue  # we use "medium" for all from auction_data
                if auto_applicable is not None and not auto_applicable:
                    continue  # all ours are auto_applicable=True when coin is empty
                auction_images: List[str] = []
                if getattr(auction_row, "primary_image_url", None):
                    auction_images.append(auction_row.primary_image_url or "")
                opportunities.append(
                    EnrichmentResponse(
                        id=eid,
                        coin_id=coin_row.id,
                        auction_data_id=auction_row.id,
                        audit_run_id=None,
                        field_name=fname,
                        suggested_value=sug,
                        source_house=auction_row.source or "Auction",
                        trust_level="medium",
                        confidence=0.8,
                        auto_applicable=True,
                        status="pending",
                        applied=False,
                        applied_at=None,
                        rejection_reason=None,
                        created_at=now_iso,
                        source_url=getattr(auction_row, "url", None),
                        auction_images=auction_images,
                    )
                )

    total = len(opportunities)
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    items = opportunities[start : start + per_page]
    return EnrichmentsListResponse(items=items, total=total, page=page, per_page=per_page, pages=pages)


@router.post("/enrichments/bulk-apply")
def bulk_apply_enrichments(
    body: EnrichmentBulkApplyBody,
    service: ApplyEnrichmentService = Depends(get_apply_enrichment_service),
):
    """Apply multiple enrichments by (coin_id, field_name, value)."""
    applications = [
        EnrichmentApplication(
            coin_id=a.coin_id,
            field_name=a.field_name,
            new_value=a.value,
            source_type="audit",
            source_id=None,
        )
        for a in body.applications
    ]
    results = service.apply_batch(applications)
    applied = sum(1 for r in results if r.success)
    return {"applied": applied}


@router.post("/enrichments/apply")
def apply_one_enrichment(
    body: EnrichmentApplyBody,
    service: ApplyEnrichmentService = Depends(get_apply_enrichment_service),
):
    """Apply a single enrichment by (coin_id, field_name, value)."""
    app = EnrichmentApplication(
        coin_id=body.coin_id,
        field_name=body.field_name,
        new_value=body.value,
        source_type="audit",
        source_id=None,
    )
    result = service.apply(app)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Apply failed")
    return {"status": "success", "field": result.field_name, "new_value": result.new_value}


@router.post("/enrichments/auto-apply-empty")
def auto_apply_empty_enrichments(
    service: ApplyEnrichmentService = Depends(get_apply_enrichment_service),
    db: Session = Depends(get_db),
):
    """
    Apply all pending enrichments where coin field is empty (server-side).
    Fetches opportunities and applies them in one go.
    """
    q = (
        db.query(AuctionDataModel, CoinModel)
        .join(CoinModel, AuctionDataModel.coin_id == CoinModel.id)
        .where(AuctionDataModel.coin_id.isnot(None))
    )
    rows = q.all()
    applications: List[EnrichmentApplication] = []
    field_checks = [
        ("issuer", lambda c, a: (c.issuer, a.issuer)),
        ("mint", lambda c, a: (c.mint, a.mint)),
        ("year_start", lambda c, a: (c.year_start, a.year_start)),
        ("year_end", lambda c, a: (c.year_end, a.year_end)),
        ("grade", lambda c, a: (c.grade, a.grade)),
    ]
    for auction_row, coin_row in rows:
        for fname, get_vals in field_checks:
            coin_val, auction_val = get_vals(coin_row, auction_row)
            if _empty(coin_val) and _non_empty(auction_val):
                sug = str(auction_val).strip() if auction_val is not None else ""
                if sug:
                    applications.append(
                        EnrichmentApplication(
                            coin_id=coin_row.id,
                            field_name=fname,
                            new_value=sug,
                            source_type="audit",
                            source_id=str(auction_row.id),
                        )
                    )
    results = service.apply_batch(applications)
    applied = sum(1 for r in results if r.success)
    return {"applied": applied, "applied_by_field": {}}


@router.get("/{coin_id}", response_model=AuditResultResponse)
def audit_coin(
    coin_id: int,
    repo: ICoinRepository = Depends(get_coin_repo)
):
    coin = repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
        
    # Mock data for demonstration if coin is ID 1 or has no price
    external_data = []
    if coin.attribution.issuer.lower() == "augustus" or coin.acquisition is None:
        external_data.append(ExternalAuctionData(
            source="Heritage",
            lot_number="12345",
            grade="XF", 
            issuer="Augustus",
            weight_g=3.85 if (coin.dimensions.weight_g is None or coin.dimensions.weight_g == 0) else coin.dimensions.weight_g + 1
        ))

    engine = AuditEngine([
        GradeStrategy(),
        AttributionStrategy(),
        PhysicsStrategy(),
        DateStrategy()
    ])
    
    all_discrepancies = []
    for data in external_data:
        results = engine.run(coin, data)
        all_discrepancies.extend(results)
        
    return AuditResultResponse(
        coin_id=coin_id,
        has_issues=len(all_discrepancies) > 0,
        discrepancies=[
            DiscrepancyResponse(
                field=d.field,
                current_value=d.current_value,
                auction_value=d.auction_value,
                confidence=d.confidence,
                source=d.source
            ) for d in all_discrepancies
        ]
    )

@router.post("/{coin_id}/apply", status_code=status.HTTP_200_OK)
def apply_enrichment(
    coin_id: int,
    request: ApplyEnrichmentRequest,
    service: ApplyEnrichmentService = Depends(get_apply_enrichment_service),
):
    application = EnrichmentApplication(
        coin_id=coin_id,
        field_name=request.field,
        new_value=request.value,
        source_type="audit",
        source_id=None,
    )
    result = service.apply(application)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Apply failed")
    return {"status": "success", "field": result.field_name, "new_value": result.new_value}