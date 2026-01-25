from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from src.infrastructure.persistence.database import get_db
from src.infrastructure.services.series_service import SeriesService

router = APIRouter(prefix="/api/series", tags=["series"])

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

class SeriesResponse(BaseModel):
    id: int
    name: str
    slug: str
    series_type: str
    target_count: Optional[int]
    is_complete: bool
    slots: List[SlotResponse] = []

# --- Endpoints ---

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
    # Map to response manually or let Pydantic handle it if ORM mode is on
    # Assuming ORM mode isn't configured in Pydantic models above, we construct dicts
    # or update models to ConfigDict(from_attributes=True)
    
    # Let's simple return attributes for now as MagicMock in test expects dict access
    return SeriesResponse(
        id=series.id,
        name=series.name,
        slug=series.slug,
        series_type=series.series_type,
        target_count=series.target_count,
        is_complete=series.is_complete,
        slots=[]
    )

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
        return SlotResponse(
            id=slot.id,
            series_id=slot.series_id,
            slot_number=slot.slot_number,
            name=slot.name,
            status=slot.status
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
