"""Iconography Compositions Router for CoinStack API (Phase 4)."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import IconographyComposition, CompositionCategory
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.iconography_composition_repository import SqlAlchemyIconographyCompositionRepository

router = APIRouter(prefix="/api/v2/iconography/compositions", tags=["Iconography Compositions"])

# Request/Response Schemas
class CompositionCreateRequest(BaseModel):
    composition_name: str = Field(..., max_length=200)
    canonical_description: Optional[str] = None
    category: Optional[str] = None
    composition_json: Optional[str] = None
    reference_system: Optional[str] = None
    reference_numbers: Optional[List[str]] = None

class CompositionResponse(BaseModel):
    id: int
    composition_name: str
    canonical_description: Optional[str] = None
    category: Optional[str] = None
    composition_json: Optional[str] = None
    reference_system: Optional[str] = None
    reference_numbers: List[str] = []
    usage_count: int

# Dependency
def get_composition_repo(db: Session = Depends(get_db)) -> SqlAlchemyIconographyCompositionRepository:
    return SqlAlchemyIconographyCompositionRepository(db)

# Helper
def _to_response(comp: IconographyComposition) -> CompositionResponse:
    return CompositionResponse(
        id=comp.id,
        composition_name=comp.composition_name,
        canonical_description=comp.canonical_description,
        category=comp.category.value if comp.category else None,
        composition_json=comp.composition_json,
        reference_system=comp.reference_system,
        reference_numbers=comp.reference_numbers,
        usage_count=comp.usage_count
    )

# Endpoints
@router.get("", response_model=List[CompositionResponse])
def list_compositions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    repo: SqlAlchemyIconographyCompositionRepository = Depends(get_composition_repo)
):
    if category:
        compositions = repo.list_by_category(category, skip, limit)
    else:
        compositions = repo.list_all(skip, limit)
    return [_to_response(c) for c in compositions]

@router.post("", response_model=CompositionResponse, status_code=status.HTTP_201_CREATED)
def create_composition(
    request: CompositionCreateRequest,
    repo: SqlAlchemyIconographyCompositionRepository = Depends(get_composition_repo)
):
    # Validate category if provided
    category = None
    if request.category:
        try:
            category = CompositionCategory(request.category)
        except ValueError:
            raise HTTPException(400, f"Invalid category: {request.category}")
    
    composition = IconographyComposition(
        composition_name=request.composition_name,
        canonical_description=request.canonical_description,
        category=category,
        composition_json=request.composition_json,
        reference_system=request.reference_system,
        reference_numbers=request.reference_numbers or [],
        usage_count=0,
        elements=[]
    )
    
    created = repo.create(composition)
    return _to_response(created)

@router.get("/search", response_model=List[CompositionResponse])
def search_compositions(
    q: str = Query(..., min_length=1),
    category: Optional[str] = None,
    repo: SqlAlchemyIconographyCompositionRepository = Depends(get_composition_repo)
):
    compositions = repo.search(q, category)
    return [_to_response(c) for c in compositions]

@router.get("/{composition_id}", response_model=CompositionResponse)
def get_composition(
    composition_id: int,
    repo: SqlAlchemyIconographyCompositionRepository = Depends(get_composition_repo)
):
    composition = repo.get_by_id(composition_id)
    if not composition:
        raise HTTPException(404, f"Composition {composition_id} not found")
    return _to_response(composition)

@router.get("/{composition_id}/coins", response_model=List[int])
def get_coins_using_composition(
    composition_id: int,
    repo: SqlAlchemyIconographyCompositionRepository = Depends(get_composition_repo)
):
    coin_ids = repo.get_coins_using_composition(composition_id)
    return coin_ids

@router.delete("/{composition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_composition(
    composition_id: int,
    repo: SqlAlchemyIconographyCompositionRepository = Depends(get_composition_repo)
):
    if not repo.delete(composition_id):
        raise HTTPException(404, f"Composition {composition_id} not found")
