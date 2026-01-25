from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.services.series_service import SeriesService

router = APIRouter(prefix="/api/v2/series", tags=["series"])

# --- Request/Response Models ---
class SeriesCreate(BaseModel):
    name: str
    series_type: str
    target_count: Optional[int] = None
    description: Optional[str] = None

class SlotCreate(BaseModel):
    slot_number: int
    name: str
    description: Optional[str] = None

class SlotResponse(BaseModel):
    id: int
    series_id: int
    slot_number: int
    name: str
    status: str

    @classmethod
    def from_model(cls, slot) -> "SlotResponse":
        """Factory method to create SlotResponse from ORM model."""
        return cls(
            id=slot.id,
            series_id=slot.series_id,
            slot_number=slot.slot_number,
            name=slot.name,
            status=slot.status
        )

class MembershipResponse(BaseModel):
    id: int
    series_id: int
    coin_id: int
    slot_id: Optional[int]

    @classmethod
    def from_model(cls, membership) -> "MembershipResponse":
        """Factory method to create MembershipResponse from ORM model."""
        return cls(
            id=membership.id,
            series_id=membership.series_id,
            coin_id=membership.coin_id,
            slot_id=membership.slot_id
        )

class SeriesResponse(BaseModel):
    id: int
    name: str
    slug: str
    series_type: str
    target_count: Optional[int]
    is_complete: bool
    slots: List[SlotResponse] = []

    @classmethod
    def from_model(cls, series) -> "SeriesResponse":
        """Factory method to create SeriesResponse from ORM model."""
        return cls(
            id=series.id,
            name=series.name,
            slug=series.slug,
            series_type=series.series_type,
            target_count=series.target_count,
            is_complete=series.is_complete,
            slots=[SlotResponse.from_model(sl) for sl in series.slots]
        )

class SeriesListResponse(BaseModel):
    items: List[SeriesResponse]
    total: int

# --- Endpoints ---

@router.get("", response_model=SeriesListResponse)
def list_series(
    db: Session = Depends(get_db)
):
    from src.infrastructure.persistence.models_series import SeriesModel
    items = db.query(SeriesModel).all()
    return SeriesListResponse(
        items=[SeriesResponse.from_model(s) for s in items],
        total=len(items)
    )

@router.get("/{series_id}", response_model=SeriesResponse)
def get_series(
    series_id: int,
    db: Session = Depends(get_db)
):
    from src.infrastructure.persistence.models_series import SeriesModel
    series = db.get(SeriesModel, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    return SeriesResponse.from_model(series)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SeriesResponse)
def create_series(
    request: SeriesCreate,
    db: Session = Depends(get_db)
):
    service = SeriesService(db)
    series = service.create_series(
        name=request.name,
        series_type=request.series_type,
        target_count=request.target_count,
        description=request.description
    )
    return SeriesResponse.from_model(series)

@router.post("/{series_id}/slots", status_code=status.HTTP_201_CREATED, response_model=SlotResponse)
def add_slot(
    series_id: int,
    request: SlotCreate,
    db: Session = Depends(get_db)
):
    service = SeriesService(db)
    try:
        slot = service.add_slot(
            series_id=series_id,
            slot_number=request.slot_number,
            name=request.name,
            description=request.description
        )
        return SlotResponse.from_model(slot)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{series_id}/coins/{coin_id}", status_code=status.HTTP_201_CREATED, response_model=MembershipResponse)
def add_coin_to_series(
    series_id: int,
    coin_id: int,
    slot_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    service = SeriesService(db)
    membership = service.add_coin_to_series(series_id, coin_id, slot_id)
    return MembershipResponse.from_model(membership)

@router.delete("/{series_id}/coins/{coin_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_coin_from_series(
    series_id: int,
    coin_id: int,
    db: Session = Depends(get_db)
):
    service = SeriesService(db)
    if not service.remove_coin_from_series(series_id, coin_id):
        raise HTTPException(status_code=404, detail="Membership not found")
