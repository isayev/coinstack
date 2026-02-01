"""Coin Iconography Links Router for CoinStack API (Phase 4)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import CoinIconography, CoinSide, IconographyPosition
from src.infrastructure.web.dependencies import get_db, get_coin_repo
from src.domain.repositories import ICoinRepository
from src.infrastructure.repositories.coin_iconography_repository import SqlAlchemyCoinIconographyRepository
from src.infrastructure.repositories.iconography_composition_repository import SqlAlchemyIconographyCompositionRepository

router = APIRouter(prefix="/api/v2/coins/{coin_id}/iconography", tags=["Coin Iconography"])

# Request/Response Schemas
class CoinIconographyCreateRequest(BaseModel):
    composition_id: int
    coin_side: str = Field(..., description="obverse or reverse")
    position: Optional[str] = Field(None, description="center, left_field, right_field, exergue, above, below")
    notes: Optional[str] = Field(None, max_length=255)

class CoinIconographyResponse(BaseModel):
    id: int
    coin_id: int
    composition_id: int
    coin_side: str
    position: Optional[str] = None
    notes: Optional[str] = None

# Dependencies
def get_coin_iconography_repo(db: Session = Depends(get_db)) -> SqlAlchemyCoinIconographyRepository:
    return SqlAlchemyCoinIconographyRepository(db)

def get_composition_repo(db: Session = Depends(get_db)) -> SqlAlchemyIconographyCompositionRepository:
    return SqlAlchemyIconographyCompositionRepository(db)

# Helper
def _to_response(link: CoinIconography) -> CoinIconographyResponse:
    return CoinIconographyResponse(
        id=link.id,
        coin_id=link.coin_id,
        composition_id=link.composition_id,
        coin_side=link.coin_side.value if link.coin_side else "",
        position=link.position.value if link.position else None,
        notes=link.notes
    )

# Endpoints
@router.get("", response_model=List[CoinIconographyResponse])
def list_coin_iconography(
    coin_id: int,
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    repo: SqlAlchemyCoinIconographyRepository = Depends(get_coin_iconography_repo)
):
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(404, f"Coin {coin_id} not found")
    
    links = repo.get_by_coin_id(coin_id)
    return [_to_response(link) for link in links]

@router.post("", response_model=CoinIconographyResponse, status_code=status.HTTP_201_CREATED)
def create_coin_iconography(
    coin_id: int,
    request: CoinIconographyCreateRequest,
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    repo: SqlAlchemyCoinIconographyRepository = Depends(get_coin_iconography_repo),
    composition_repo: SqlAlchemyIconographyCompositionRepository = Depends(get_composition_repo)
):
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(404, f"Coin {coin_id} not found")
    
    # Verify composition exists
    if not composition_repo.get_by_id(request.composition_id):
        raise HTTPException(404, f"Composition {request.composition_id} not found")
    
    # Validate enums
    try:
        coin_side = CoinSide(request.coin_side)
    except ValueError:
        raise HTTPException(400, f"Invalid coin_side: {request.coin_side}")
    
    position = None
    if request.position:
        try:
            position = IconographyPosition(request.position)
        except ValueError:
            raise HTTPException(400, f"Invalid position: {request.position}")
    
    # Check for duplicate
    duplicate = repo.find_duplicate(coin_id, request.composition_id, request.coin_side)
    if duplicate:
        raise HTTPException(409, f"Composition already linked to coin on {request.coin_side}")
    
    link = CoinIconography(
        coin_id=coin_id,
        composition_id=request.composition_id,
        coin_side=coin_side,
        position=position,
        notes=request.notes
    )
    
    created = repo.create(link)
    
    # Increment usage count on composition
    composition_repo.increment_usage(request.composition_id)
    
    return _to_response(created)

@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coin_iconography(
    coin_id: int,
    link_id: int,
    repo: SqlAlchemyCoinIconographyRepository = Depends(get_coin_iconography_repo),
    composition_repo: SqlAlchemyIconographyCompositionRepository = Depends(get_composition_repo)
):
    # Get link to verify it belongs to this coin
    link = repo.get_by_id(link_id)
    if not link or link.coin_id != coin_id:
        raise HTTPException(404, f"Link {link_id} not found for coin {coin_id}")
    
    composition_id = link.composition_id
    
    if not repo.delete(link_id):
        raise HTTPException(404, f"Link {link_id} not found")
    
    # Decrement usage count on composition
    composition_repo.decrement_usage(composition_id)
