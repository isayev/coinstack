"""
Die Study Router for CoinStack API.

Provides REST endpoints for managing die links and die study groups.

Die Link Endpoints:
- GET /api/v2/die-study/links/{coin_id} - Get die links for a coin
- POST /api/v2/die-study/links - Create a die link
- PUT /api/v2/die-study/links/{id} - Update a die link
- DELETE /api/v2/die-study/links/{id} - Delete a die link

Die Group Endpoints:
- GET /api/v2/die-study/groups - List all die study groups
- POST /api/v2/die-study/groups - Create a die study group
- GET /api/v2/die-study/groups/{id} - Get a die study group
- PUT /api/v2/die-study/groups/{id} - Update a die study group
- DELETE /api/v2/die-study/groups/{id} - Delete a die study group
- POST /api/v2/die-study/groups/{id}/members - Add member to group
- DELETE /api/v2/die-study/groups/{id}/members/{coin_id} - Remove member
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.die_study_repository import SqlAlchemyDieStudyRepository
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.domain.die_study import DieSide, DieMatchConfidence, DieMatchSource

router = APIRouter(prefix="/die-study", tags=["Die Study"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class DieLinkCreate(BaseModel):
    """Request to create a die link."""
    coin_a_id: int = Field(..., description="First coin ID")
    coin_b_id: int = Field(..., description="Second coin ID")
    die_side: str = Field(..., description="obverse or reverse")
    confidence: str = Field("possible", description="certain, probable, possible, uncertain")
    source: str = Field("manual", description="manual, llm, reference, import")
    reference: Optional[str] = Field(None, description="Published reference")
    notes: Optional[str] = Field(None, description="Additional notes")


class DieLinkUpdate(BaseModel):
    """Request to update a die link."""
    confidence: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class DieLinkResponse(BaseModel):
    """Response for a die link."""
    id: int
    coin_a_id: int
    coin_b_id: int
    die_side: str
    confidence: str
    source: str
    reference: Optional[str]
    notes: Optional[str]
    identified_at: datetime


class DieGroupCreate(BaseModel):
    """Request to create a die study group."""
    name: str = Field(..., description="Group name")
    die_side: str = Field(..., description="obverse or reverse")
    issuer_id: Optional[int] = Field(None, description="Issuer ID for filtering")
    mint_id: Optional[int] = Field(None, description="Mint ID for filtering")
    notes: Optional[str] = Field(None, description="Description")


class DieGroupUpdate(BaseModel):
    """Request to update a die study group."""
    name: Optional[str] = None
    notes: Optional[str] = None


class DieGroupMemberAdd(BaseModel):
    """Request to add a member to a die group."""
    coin_id: int = Field(..., description="Coin ID to add")
    sequence_position: Optional[int] = Field(None, description="Estimated strike order")


class DieGroupMemberResponse(BaseModel):
    """Response for a die group member."""
    coin_id: int
    sequence_position: Optional[int]


class DieGroupResponse(BaseModel):
    """Response for a die study group."""
    id: int
    name: str
    die_side: str
    issuer_id: Optional[int]
    mint_id: Optional[int]
    notes: Optional[str]
    created_at: datetime
    member_count: int
    members: List[DieGroupMemberResponse]


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_die_study_repo(db: Session = Depends(get_db)) -> SqlAlchemyDieStudyRepository:
    """Get die study repository instance."""
    return SqlAlchemyDieStudyRepository(db)


def get_coin_repo(db: Session = Depends(get_db)) -> SqlAlchemyCoinRepository:
    """Get coin repository instance."""
    return SqlAlchemyCoinRepository(db)


# =============================================================================
# DIE LINK ENDPOINTS
# =============================================================================

@router.get(
    "/links/coin/{coin_id}",
    response_model=List[DieLinkResponse],
    summary="Get die links for a coin",
    description="Get all die links involving a specific coin.",
)
def get_links_for_coin(
    coin_id: int,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get all die links for a coin."""
    # Verify coin exists
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    
    links = die_study_repo.get_links_for_coin(coin_id)
    
    return [
        DieLinkResponse(
            id=link.id,
            coin_a_id=link.coin_a_id,
            coin_b_id=link.coin_b_id,
            die_side=link.die_side.value,
            confidence=link.confidence.value,
            source=link.source.value,
            reference=link.reference,
            notes=link.notes,
            identified_at=link.identified_at,
        )
        for link in links
    ]


@router.post(
    "/links",
    response_model=DieLinkResponse,
    status_code=201,
    summary="Create die link",
    description="Create a die link between two coins.",
)
def create_link(
    request: DieLinkCreate,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Create a die link between two coins.
    
    The link indicates that both coins were struck from the same die
    on the specified side (obverse or reverse).
    """
    # Validate coins exist
    coin_a = coin_repo.get_by_id(request.coin_a_id)
    if not coin_a:
        raise HTTPException(status_code=404, detail=f"Coin {request.coin_a_id} not found")
    
    coin_b = coin_repo.get_by_id(request.coin_b_id)
    if not coin_b:
        raise HTTPException(status_code=404, detail=f"Coin {request.coin_b_id} not found")
    
    if request.coin_a_id == request.coin_b_id:
        raise HTTPException(status_code=400, detail="Cannot link a coin to itself")
    
    # Validate enums
    try:
        die_side = DieSide(request.die_side)
    except ValueError:
        raise HTTPException(status_code=400, detail="die_side must be 'obverse' or 'reverse'")
    
    try:
        confidence = DieMatchConfidence(request.confidence)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="confidence must be 'certain', 'probable', 'possible', or 'uncertain'"
        )
    
    try:
        source = DieMatchSource(request.source)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="source must be 'manual', 'llm', 'reference', or 'import'"
        )
    
    # Check for existing link
    existing = die_study_repo.get_link_between(request.coin_a_id, request.coin_b_id, die_side)
    if existing:
        raise HTTPException(
            status_code=409, 
            detail=f"Die link already exists between these coins for {die_side.value}"
        )
    
    model = die_study_repo.create_link(
        coin_a_id=request.coin_a_id,
        coin_b_id=request.coin_b_id,
        die_side=die_side,
        confidence=confidence,
        source=source,
        reference=request.reference,
        notes=request.notes,
    )
    
    return DieLinkResponse(
        id=model.id,
        coin_a_id=model.coin_a_id,
        coin_b_id=model.coin_b_id,
        die_side=model.die_side,
        confidence=model.confidence,
        source=model.source,
        reference=model.reference,
        notes=model.notes,
        identified_at=model.identified_at,
    )


@router.put(
    "/links/{link_id}",
    response_model=DieLinkResponse,
    summary="Update die link",
    description="Update a die link's confidence, reference, or notes.",
)
def update_link(
    link_id: int,
    request: DieLinkUpdate,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
):
    """Update a die link."""
    confidence = None
    if request.confidence:
        try:
            confidence = DieMatchConfidence(request.confidence)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="confidence must be 'certain', 'probable', 'possible', or 'uncertain'"
            )
    
    model = die_study_repo.update_link(
        link_id=link_id,
        confidence=confidence,
        reference=request.reference,
        notes=request.notes,
    )
    
    if not model:
        raise HTTPException(status_code=404, detail=f"Die link {link_id} not found")
    
    return DieLinkResponse(
        id=model.id,
        coin_a_id=model.coin_a_id,
        coin_b_id=model.coin_b_id,
        die_side=model.die_side,
        confidence=model.confidence,
        source=model.source,
        reference=model.reference,
        notes=model.notes,
        identified_at=model.identified_at,
    )


@router.delete(
    "/links/{link_id}",
    status_code=204,
    summary="Delete die link",
    description="Delete a die link.",
)
def delete_link(
    link_id: int,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
):
    """Delete a die link."""
    deleted = die_study_repo.delete_link(link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Die link {link_id} not found")
    return None


# =============================================================================
# DIE GROUP ENDPOINTS
# =============================================================================

@router.get(
    "/groups",
    response_model=List[DieGroupResponse],
    summary="List die study groups",
    description="List all die study groups with optional filtering.",
)
def list_groups(
    die_side: Optional[str] = None,
    issuer_id: Optional[int] = None,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
):
    """List all die study groups."""
    side = None
    if die_side:
        try:
            side = DieSide(die_side)
        except ValueError:
            raise HTTPException(status_code=400, detail="die_side must be 'obverse' or 'reverse'")
    
    groups = die_study_repo.get_all_groups(die_side=side, issuer_id=issuer_id)
    
    return [
        DieGroupResponse(
            id=g.id,
            name=g.name,
            die_side=g.die_side.value,
            issuer_id=g.issuer_id,
            mint_id=g.mint_id,
            notes=g.notes,
            created_at=g.created_at,
            member_count=g.member_count,
            members=[
                DieGroupMemberResponse(
                    coin_id=coin_id,
                    sequence_position=g.member_positions.get(coin_id)
                )
                for coin_id in g.members
            ],
        )
        for g in groups
    ]


@router.post(
    "/groups",
    response_model=DieGroupResponse,
    status_code=201,
    summary="Create die study group",
    description="Create a new die study group.",
)
def create_group(
    request: DieGroupCreate,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
):
    """Create a new die study group."""
    try:
        die_side = DieSide(request.die_side)
    except ValueError:
        raise HTTPException(status_code=400, detail="die_side must be 'obverse' or 'reverse'")
    
    model = die_study_repo.create_group(
        name=request.name,
        die_side=die_side,
        issuer_id=request.issuer_id,
        mint_id=request.mint_id,
        notes=request.notes,
    )
    
    return DieGroupResponse(
        id=model.id,
        name=model.name,
        die_side=model.die_side,
        issuer_id=model.issuer_id,
        mint_id=model.mint_id,
        notes=model.notes,
        created_at=model.created_at,
        member_count=0,
        members=[],
    )


@router.get(
    "/groups/{group_id}",
    response_model=DieGroupResponse,
    summary="Get die study group",
    description="Get a die study group by ID with members.",
)
def get_group(
    group_id: int,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
):
    """Get a die study group."""
    group = die_study_repo.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"Die study group {group_id} not found")
    
    return DieGroupResponse(
        id=group.id,
        name=group.name,
        die_side=group.die_side.value,
        issuer_id=group.issuer_id,
        mint_id=group.mint_id,
        notes=group.notes,
        created_at=group.created_at,
        member_count=group.member_count,
        members=[
            DieGroupMemberResponse(
                coin_id=coin_id,
                sequence_position=group.member_positions.get(coin_id)
            )
            for coin_id in group.members
        ],
    )


@router.put(
    "/groups/{group_id}",
    response_model=DieGroupResponse,
    summary="Update die study group",
    description="Update a die study group's name or notes.",
)
def update_group(
    group_id: int,
    request: DieGroupUpdate,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
):
    """Update a die study group."""
    model = die_study_repo.update_group(
        group_id=group_id,
        name=request.name,
        notes=request.notes,
    )
    
    if not model:
        raise HTTPException(status_code=404, detail=f"Die study group {group_id} not found")
    
    # Re-fetch to get members
    group = die_study_repo.get_group_by_id(group_id)
    
    return DieGroupResponse(
        id=group.id,
        name=group.name,
        die_side=group.die_side.value,
        issuer_id=group.issuer_id,
        mint_id=group.mint_id,
        notes=group.notes,
        created_at=group.created_at,
        member_count=group.member_count,
        members=[
            DieGroupMemberResponse(
                coin_id=coin_id,
                sequence_position=group.member_positions.get(coin_id)
            )
            for coin_id in group.members
        ],
    )


@router.delete(
    "/groups/{group_id}",
    status_code=204,
    summary="Delete die study group",
    description="Delete a die study group and all memberships.",
)
def delete_group(
    group_id: int,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
):
    """Delete a die study group."""
    deleted = die_study_repo.delete_group(group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Die study group {group_id} not found")
    return None


@router.post(
    "/groups/{group_id}/members",
    response_model=DieGroupMemberResponse,
    status_code=201,
    summary="Add member to group",
    description="Add a coin to a die study group.",
)
def add_member(
    group_id: int,
    request: DieGroupMemberAdd,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Add a coin to a die study group."""
    # Verify coin exists
    coin = coin_repo.get_by_id(request.coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {request.coin_id} not found")
    
    member = die_study_repo.add_member_to_group(
        group_id=group_id,
        coin_id=request.coin_id,
        sequence_position=request.sequence_position,
    )
    
    if not member:
        raise HTTPException(status_code=404, detail=f"Die study group {group_id} not found")
    
    return DieGroupMemberResponse(
        coin_id=member.coin_id,
        sequence_position=member.sequence_position,
    )


@router.delete(
    "/groups/{group_id}/members/{coin_id}",
    status_code=204,
    summary="Remove member from group",
    description="Remove a coin from a die study group.",
)
def remove_member(
    group_id: int,
    coin_id: int,
    die_study_repo: SqlAlchemyDieStudyRepository = Depends(get_die_study_repo),
):
    """Remove a coin from a die study group."""
    removed = die_study_repo.remove_member_from_group(group_id, coin_id)
    if not removed:
        raise HTTPException(
            status_code=404, 
            detail=f"Coin {coin_id} not found in group {group_id}"
        )
    return None
