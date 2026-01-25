from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from src.domain.repositories import ICoinRepository
from src.domain.audit import AuditEngine, ExternalAuctionData
from src.domain.strategies.grade_strategy import GradeStrategy
from src.domain.strategies.attribution_strategy import AttributionStrategy
from src.domain.strategies.physics_strategy import PhysicsStrategy
from src.domain.strategies.date_strategy import DateStrategy
from src.infrastructure.web.dependencies import get_coin_repo
from src.domain.coin import Metal, Category, GradingState, GradeService, CoinImage, Dimensions, Attribution, GradingDetails, AcquisitionDetails

router = APIRouter(prefix="/api/v2/audit", tags=["audit"])

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
            weight_g=3.85 if coin.dimensions.weight_g == 0 else coin.dimensions.weight_g + 1
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
    repo: ICoinRepository = Depends(get_coin_repo)
):
    coin = repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    # Very simplified enrichment application
    # In a real app, this would use an 'EnrichCoinUseCase'
    try:
        # We need to map the field string to the actual property update
        # Since domain objects are frozen, we'd ideally have a .copy(updates) method
        # For this skeleton, we'll re-instantiate or mutate if possible
        
        # This is complex because fields are nested. 
        # For the demo, let's just show it's possible.
        
        field = request.field
        val = request.value
        
        # Mapping logic (Simplified)
        if field == "grade":
            new_grading = GradingDetails(
                grading_state=coin.grading.grading_state,
                grade=val,
                service=coin.grading.service
            )
            # Reconstruct coin
            from dataclasses import replace
            updated_coin = replace(coin, grading=new_grading)
            repo.save(updated_coin)
            
        return {"status": "success", "field": field, "new_value": val}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))