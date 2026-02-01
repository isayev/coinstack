"""Iconography Elements Router for CoinStack API (Phase 4)."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import IconographyElement, IconographyCategory
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.iconography_element_repository import SqlAlchemyIconographyElementRepository

router = APIRouter(prefix="/api/v2/iconography/elements", tags=["Iconography Elements"])

# Request/Response Schemas
class ElementCreateRequest(BaseModel):
    canonical_name: str = Field(..., max_length=100)
    display_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = None

class ElementResponse(BaseModel):
    id: int
    canonical_name: str
    display_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: List[str] = []
    usage_count: int

# Dependency
def get_element_repo(db: Session = Depends(get_db)) -> SqlAlchemyIconographyElementRepository:
    return SqlAlchemyIconographyElementRepository(db)

# Helper
def _to_response(element: IconographyElement) -> ElementResponse:
    return ElementResponse(
        id=element.id,
        canonical_name=element.canonical_name,
        display_name=element.display_name,
        category=element.category.value if element.category else None,
        description=element.description,
        aliases=element.aliases,
        usage_count=element.usage_count
    )

# Endpoints
@router.get("", response_model=List[ElementResponse])
def list_elements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    repo: SqlAlchemyIconographyElementRepository = Depends(get_element_repo)
):
    if category:
        elements = repo.list_by_category(category, skip, limit)
    else:
        elements = repo.list_all(skip, limit)
    return [_to_response(e) for e in elements]

@router.post("", response_model=ElementResponse, status_code=status.HTTP_201_CREATED)
def create_element(
    request: ElementCreateRequest,
    repo: SqlAlchemyIconographyElementRepository = Depends(get_element_repo)
):
    # Validate category if provided
    category = None
    if request.category:
        try:
            category = IconographyCategory(request.category)
        except ValueError:
            raise HTTPException(400, f"Invalid category: {request.category}")
    
    element = IconographyElement(
        canonical_name=request.canonical_name,
        display_name=request.display_name or "",
        category=category,
        description=request.description,
        aliases=request.aliases or [],
        usage_count=0
    )
    
    try:
        created = repo.create(element)
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(409, f"Element '{request.canonical_name}' already exists")
        raise
    
    return _to_response(created)

@router.get("/search", response_model=List[ElementResponse])
def search_elements(
    q: str = Query(..., min_length=1),
    category: Optional[str] = None,
    repo: SqlAlchemyIconographyElementRepository = Depends(get_element_repo)
):
    elements = repo.search(q, category)
    return [_to_response(e) for e in elements]

@router.get("/{element_id}", response_model=ElementResponse)
def get_element(
    element_id: int,
    repo: SqlAlchemyIconographyElementRepository = Depends(get_element_repo)
):
    element = repo.get_by_id(element_id)
    if not element:
        raise HTTPException(404, f"Element {element_id} not found")
    return _to_response(element)

@router.delete("/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_element(
    element_id: int,
    repo: SqlAlchemyIconographyElementRepository = Depends(get_element_repo)
):
    if not repo.delete(element_id):
        raise HTTPException(404, f"Element {element_id} not found")
