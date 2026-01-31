"""
External Catalog Links API Router.

Manages links to external online catalog databases like OCRE, Nomisma, CRRO, RPC Online.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.external_catalog_link_repository import (
    SqlAlchemyExternalCatalogLinkRepository,
)
from src.domain.coin import ExternalCatalogLink

router = APIRouter(prefix="/api/v2/external-links", tags=["external-links"])


# =============================================================================
# Constants
# =============================================================================

VALID_CATALOG_SOURCES = [
    "ocre",        # Online Coins of the Roman Empire
    "nomisma",     # Nomisma.org
    "crro",        # Coinage of the Roman Republic Online
    "rpc_online",  # Roman Provincial Coinage Online
    "acsearch",    # ACSearch coin database
    "coinproject", # CoinProject database
    "wildwinds",   # Wildwinds ancient coin database
]


# =============================================================================
# Request/Response Models
# =============================================================================


class ExternalLinkResponse(BaseModel):
    """External catalog link response."""

    id: int
    reference_type_id: int
    catalog_source: str
    external_id: str
    external_url: Optional[str] = None
    external_data: Optional[str] = None  # JSON string
    last_synced_at: Optional[datetime] = None
    sync_status: str = "pending"

    class Config:
        from_attributes = True


class CreateExternalLinkRequest(BaseModel):
    """Request to create a new external catalog link."""

    reference_type_id: int
    catalog_source: str = Field(
        ..., description=f"One of: {', '.join(VALID_CATALOG_SOURCES)}"
    )
    external_id: str = Field(..., min_length=1)
    external_url: Optional[str] = None


class UpdateExternalLinkRequest(BaseModel):
    """Request to update an external catalog link."""

    external_id: Optional[str] = None
    external_url: Optional[str] = None
    external_data: Optional[str] = None
    sync_status: Optional[str] = None


class SyncExternalLinkRequest(BaseModel):
    """Request to mark a link as synced with data."""

    external_data: Optional[str] = None  # JSON metadata from source


class ExternalLinksListResponse(BaseModel):
    """Response with list of external links."""

    links: List[ExternalLinkResponse]
    total_count: int


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/reference/{reference_type_id}", response_model=ExternalLinksListResponse)
def get_external_links_for_reference(
    reference_type_id: int,
    db: Session = Depends(get_db),
):
    """Get all external links for a reference type."""
    repo = SqlAlchemyExternalCatalogLinkRepository(db)
    links = repo.get_by_reference_type_id(reference_type_id)

    return ExternalLinksListResponse(
        links=[
            ExternalLinkResponse(
                id=link.id or 0,
                reference_type_id=link.reference_type_id,
                catalog_source=link.catalog_source,
                external_id=link.external_id,
                external_url=link.external_url,
                external_data=link.external_data,
                last_synced_at=link.last_synced_at,
                sync_status=link.sync_status,
            )
            for link in links
        ],
        total_count=len(links),
    )


@router.get("/reference/{reference_type_id}/{catalog_source}", response_model=ExternalLinkResponse)
def get_external_link_by_source(
    reference_type_id: int,
    catalog_source: str,
    db: Session = Depends(get_db),
):
    """Get a specific external link by reference type and source."""
    if catalog_source not in VALID_CATALOG_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid catalog source. Must be one of: {', '.join(VALID_CATALOG_SOURCES)}",
        )

    repo = SqlAlchemyExternalCatalogLinkRepository(db)
    link = repo.get_by_source(reference_type_id, catalog_source)

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External link not found for reference {reference_type_id} and source {catalog_source}",
        )

    return ExternalLinkResponse(
        id=link.id or 0,
        reference_type_id=link.reference_type_id,
        catalog_source=link.catalog_source,
        external_id=link.external_id,
        external_url=link.external_url,
        external_data=link.external_data,
        last_synced_at=link.last_synced_at,
        sync_status=link.sync_status,
    )


@router.get("/pending", response_model=ExternalLinksListResponse)
def get_pending_sync_links(
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get external links pending synchronization."""
    repo = SqlAlchemyExternalCatalogLinkRepository(db)
    links = repo.list_pending_sync(limit=limit)

    return ExternalLinksListResponse(
        links=[
            ExternalLinkResponse(
                id=link.id or 0,
                reference_type_id=link.reference_type_id,
                catalog_source=link.catalog_source,
                external_id=link.external_id,
                external_url=link.external_url,
                external_data=link.external_data,
                last_synced_at=link.last_synced_at,
                sync_status=link.sync_status,
            )
            for link in links
        ],
        total_count=len(links),
    )


@router.post("/", response_model=ExternalLinkResponse, status_code=status.HTTP_201_CREATED)
def create_external_link(
    request: CreateExternalLinkRequest,
    db: Session = Depends(get_db),
):
    """Create a new external catalog link."""
    if request.catalog_source not in VALID_CATALOG_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid catalog source. Must be one of: {', '.join(VALID_CATALOG_SOURCES)}",
        )

    repo = SqlAlchemyExternalCatalogLinkRepository(db)

    # Check if link already exists
    existing = repo.get_by_source(request.reference_type_id, request.catalog_source)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"External link already exists for reference {request.reference_type_id} and source {request.catalog_source}",
        )

    link = repo.create(
        ExternalCatalogLink(
            reference_type_id=request.reference_type_id,
            catalog_source=request.catalog_source,
            external_id=request.external_id,
            external_url=request.external_url,
            sync_status="pending",
        )
    )

    return ExternalLinkResponse(
        id=link.id or 0,
        reference_type_id=link.reference_type_id,
        catalog_source=link.catalog_source,
        external_id=link.external_id,
        external_url=link.external_url,
        external_data=link.external_data,
        last_synced_at=link.last_synced_at,
        sync_status=link.sync_status,
    )


@router.put("/{link_id}", response_model=ExternalLinkResponse)
def update_external_link(
    link_id: int,
    request: UpdateExternalLinkRequest,
    db: Session = Depends(get_db),
):
    """Update an external catalog link."""
    repo = SqlAlchemyExternalCatalogLinkRepository(db)

    # Get existing link
    links_for_id = [
        link for link in repo.list_pending_sync(limit=1000)
        if link.id == link_id
    ]

    # Query directly for the link
    from src.infrastructure.persistence.orm import ExternalCatalogLinkModel
    model = db.query(ExternalCatalogLinkModel).get(link_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External link {link_id} not found",
        )

    # Build updated entity
    updated_link = ExternalCatalogLink(
        id=link_id,
        reference_type_id=model.reference_type_id,
        catalog_source=model.catalog_source,
        external_id=request.external_id or model.external_id,
        external_url=request.external_url if request.external_url is not None else model.external_url,
        external_data=request.external_data if request.external_data is not None else model.external_data,
        sync_status=request.sync_status or model.sync_status or "pending",
    )

    result = repo.update(link_id, updated_link)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update external link",
        )

    return ExternalLinkResponse(
        id=result.id or 0,
        reference_type_id=result.reference_type_id,
        catalog_source=result.catalog_source,
        external_id=result.external_id,
        external_url=result.external_url,
        external_data=result.external_data,
        last_synced_at=result.last_synced_at,
        sync_status=result.sync_status,
    )


@router.post("/{link_id}/sync", response_model=ExternalLinkResponse)
def mark_link_synced(
    link_id: int,
    request: SyncExternalLinkRequest,
    db: Session = Depends(get_db),
):
    """Mark an external link as synced with optional data."""
    repo = SqlAlchemyExternalCatalogLinkRepository(db)

    if not repo.mark_synced(link_id, request.external_data):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External link {link_id} not found",
        )

    # Fetch updated link
    from src.infrastructure.persistence.orm import ExternalCatalogLinkModel
    model = db.query(ExternalCatalogLinkModel).get(link_id)

    return ExternalLinkResponse(
        id=model.id,
        reference_type_id=model.reference_type_id,
        catalog_source=model.catalog_source,
        external_id=model.external_id,
        external_url=model.external_url,
        external_data=model.external_data,
        last_synced_at=model.last_synced_at,
        sync_status=model.sync_status,
    )


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_external_link(
    link_id: int,
    db: Session = Depends(get_db),
):
    """Delete an external catalog link."""
    repo = SqlAlchemyExternalCatalogLinkRepository(db)

    if not repo.delete(link_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External link {link_id} not found",
        )
