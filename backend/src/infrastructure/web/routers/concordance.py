"""
Reference Concordance API Router.

Manages cross-reference linking between equivalent catalog references.
Example: RIC 207 = RSC 112 = BMC 298 = Cohen 169
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.reference_concordance_repository import (
    SqlAlchemyConcordanceRepository,
)

router = APIRouter(prefix="/api/v2/concordance", tags=["concordance"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ConcordanceEntryResponse(BaseModel):
    """Single concordance entry response."""

    id: int
    concordance_group_id: str
    reference_type_id: int
    confidence: float = 1.0
    source: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConcordanceGroupResponse(BaseModel):
    """Concordance group with all linked references."""

    group_id: str
    entries: List[ConcordanceEntryResponse]
    total_count: int


class CreateConcordanceGroupRequest(BaseModel):
    """Request to create a new concordance group."""

    reference_type_ids: List[int] = Field(
        ..., min_length=2, description="At least 2 reference types to link"
    )
    source: str = Field(default="user", description="Source of concordance data")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class AddToConcordanceGroupRequest(BaseModel):
    """Request to add a reference to an existing concordance group."""

    reference_type_id: int
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class EquivalentReferencesResponse(BaseModel):
    """Response with equivalent reference IDs."""

    reference_type_id: int
    equivalent_ids: List[int]
    total_count: int


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/group/{group_id}", response_model=ConcordanceGroupResponse)
def get_concordance_group(
    group_id: str,
    db: Session = Depends(get_db),
):
    """Get all entries in a concordance group."""
    repo = SqlAlchemyConcordanceRepository(db)
    entries = repo.get_by_group_id(group_id)

    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concordance group {group_id} not found",
        )

    return ConcordanceGroupResponse(
        group_id=group_id,
        entries=[
            ConcordanceEntryResponse(
                id=e.id or 0,
                concordance_group_id=e.concordance_group_id,
                reference_type_id=e.reference_type_id,
                confidence=e.confidence,
                source=e.source,
                notes=e.notes,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total_count=len(entries),
    )


@router.get("/reference/{reference_type_id}", response_model=List[ConcordanceEntryResponse])
def get_concordances_for_reference(
    reference_type_id: int,
    db: Session = Depends(get_db),
):
    """Get all concordance entries for a specific reference type."""
    repo = SqlAlchemyConcordanceRepository(db)
    entries = repo.get_by_reference_type_id(reference_type_id)

    return [
        ConcordanceEntryResponse(
            id=e.id or 0,
            concordance_group_id=e.concordance_group_id,
            reference_type_id=e.reference_type_id,
            confidence=e.confidence,
            source=e.source,
            notes=e.notes,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.get("/reference/{reference_type_id}/equivalents", response_model=EquivalentReferencesResponse)
def get_equivalent_references(
    reference_type_id: int,
    db: Session = Depends(get_db),
):
    """Find all reference types equivalent to the given reference."""
    repo = SqlAlchemyConcordanceRepository(db)
    equivalent_ids = repo.find_equivalent_references(reference_type_id)

    return EquivalentReferencesResponse(
        reference_type_id=reference_type_id,
        equivalent_ids=equivalent_ids,
        total_count=len(equivalent_ids),
    )


@router.post("/group", response_model=ConcordanceGroupResponse, status_code=status.HTTP_201_CREATED)
def create_concordance_group(
    request: CreateConcordanceGroupRequest,
    db: Session = Depends(get_db),
):
    """Create a new concordance group linking multiple reference types."""
    repo = SqlAlchemyConcordanceRepository(db)

    group_id = repo.create_group(
        reference_type_ids=request.reference_type_ids,
        source=request.source,
        confidence=request.confidence,
        notes=request.notes,
    )

    entries = repo.get_by_group_id(group_id)

    return ConcordanceGroupResponse(
        group_id=group_id,
        entries=[
            ConcordanceEntryResponse(
                id=e.id or 0,
                concordance_group_id=e.concordance_group_id,
                reference_type_id=e.reference_type_id,
                confidence=e.confidence,
                source=e.source,
                notes=e.notes,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total_count=len(entries),
    )


@router.post("/group/{group_id}/add", response_model=ConcordanceEntryResponse, status_code=status.HTTP_201_CREATED)
def add_to_concordance_group(
    group_id: str,
    request: AddToConcordanceGroupRequest,
    db: Session = Depends(get_db),
):
    """Add a reference type to an existing concordance group."""
    repo = SqlAlchemyConcordanceRepository(db)

    # Verify group exists
    existing = repo.get_by_group_id(group_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concordance group {group_id} not found",
        )

    # Check if reference is already in group
    for entry in existing:
        if entry.reference_type_id == request.reference_type_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Reference type {request.reference_type_id} already in group",
            )

    from src.domain.coin import ReferenceConcordance

    new_entry = repo.create(
        ReferenceConcordance(
            concordance_group_id=group_id,
            reference_type_id=request.reference_type_id,
            confidence=request.confidence,
            source="user",
            notes=request.notes,
        )
    )

    return ConcordanceEntryResponse(
        id=new_entry.id or 0,
        concordance_group_id=new_entry.concordance_group_id,
        reference_type_id=new_entry.reference_type_id,
        confidence=new_entry.confidence,
        source=new_entry.source,
        notes=new_entry.notes,
        created_at=new_entry.created_at,
    )


@router.delete("/entry/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concordance_entry(
    entry_id: int,
    db: Session = Depends(get_db),
):
    """Delete a single concordance entry."""
    repo = SqlAlchemyConcordanceRepository(db)

    if not repo.delete(entry_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concordance entry {entry_id} not found",
        )


@router.delete("/group/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concordance_group(
    group_id: str,
    db: Session = Depends(get_db),
):
    """Delete an entire concordance group."""
    repo = SqlAlchemyConcordanceRepository(db)

    count = repo.delete_group(group_id)
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concordance group {group_id} not found",
        )
