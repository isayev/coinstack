"""
Die Study Repository Implementation.

Handles persistence of die links and die study groups.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from src.domain.die_study import (
    DieLink, DieStudyGroup, DieSide, DieMatchConfidence, DieMatchSource
)
from src.infrastructure.persistence.models_die_study import (
    DieLinkModel, DieStudyGroupModel, DieGroupMemberModel
)


class SqlAlchemyDieStudyRepository:
    """Repository for managing die links and die study groups."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # -------------------------------------------------------------------------
    # Die Links
    # -------------------------------------------------------------------------
    
    def create_link(
        self,
        coin_a_id: int,
        coin_b_id: int,
        die_side: DieSide,
        confidence: DieMatchConfidence,
        source: DieMatchSource = DieMatchSource.MANUAL,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> DieLinkModel:
        """
        Create a die link between two coins.
        
        Normalizes the coin order (lower ID first) to prevent duplicates.
        """
        # Normalize order - always store lower ID first
        if coin_a_id > coin_b_id:
            coin_a_id, coin_b_id = coin_b_id, coin_a_id
        
        model = DieLinkModel(
            coin_a_id=coin_a_id,
            coin_b_id=coin_b_id,
            die_side=die_side.value,
            confidence=confidence.value,
            source=source.value,
            reference=reference,
            notes=notes,
            identified_at=datetime.now(timezone.utc),
        )
        
        self.session.add(model)
        self.session.flush()
        return model
    
    def get_link_by_id(self, link_id: int) -> Optional[DieLink]:
        """Get a die link by ID."""
        model = self.session.get(DieLinkModel, link_id)
        if not model:
            return None
        return self._link_to_domain(model)
    
    def get_links_for_coin(self, coin_id: int) -> List[DieLink]:
        """Get all die links involving a specific coin."""
        models = self.session.query(DieLinkModel).filter(
            or_(
                DieLinkModel.coin_a_id == coin_id,
                DieLinkModel.coin_b_id == coin_id
            )
        ).all()
        
        return [self._link_to_domain(m) for m in models]
    
    def get_link_between(
        self, 
        coin_a_id: int, 
        coin_b_id: int, 
        die_side: Optional[DieSide] = None
    ) -> Optional[DieLink]:
        """Get die link between two specific coins."""
        # Normalize order
        if coin_a_id > coin_b_id:
            coin_a_id, coin_b_id = coin_b_id, coin_a_id
        
        query = self.session.query(DieLinkModel).filter(
            DieLinkModel.coin_a_id == coin_a_id,
            DieLinkModel.coin_b_id == coin_b_id
        )
        
        if die_side:
            query = query.filter(DieLinkModel.die_side == die_side.value)
        
        model = query.first()
        if not model:
            return None
        return self._link_to_domain(model)
    
    def update_link(
        self,
        link_id: int,
        confidence: Optional[DieMatchConfidence] = None,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[DieLinkModel]:
        """Update a die link."""
        model = self.session.get(DieLinkModel, link_id)
        if not model:
            return None
        
        if confidence is not None:
            model.confidence = confidence.value
        if reference is not None:
            model.reference = reference
        if notes is not None:
            model.notes = notes
        
        self.session.flush()
        return model
    
    def delete_link(self, link_id: int) -> bool:
        """Delete a die link."""
        model = self.session.get(DieLinkModel, link_id)
        if model:
            self.session.delete(model)
            return True
        return False
    
    def _link_to_domain(self, model: DieLinkModel) -> DieLink:
        """Convert ORM model to domain entity."""
        return DieLink(
            id=model.id,
            coin_a_id=model.coin_a_id,
            coin_b_id=model.coin_b_id,
            die_side=DieSide(model.die_side),
            confidence=DieMatchConfidence(model.confidence),
            source=DieMatchSource(model.source),
            reference=model.reference,
            notes=model.notes,
            identified_at=model.identified_at,
        )
    
    # -------------------------------------------------------------------------
    # Die Study Groups
    # -------------------------------------------------------------------------
    
    def create_group(
        self,
        name: str,
        die_side: DieSide,
        issuer_id: Optional[int] = None,
        mint_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> DieStudyGroupModel:
        """Create a new die study group."""
        model = DieStudyGroupModel(
            name=name,
            die_side=die_side.value,
            issuer_id=issuer_id,
            mint_id=mint_id,
            notes=notes,
            created_at=datetime.now(timezone.utc),
        )
        
        self.session.add(model)
        self.session.flush()
        return model
    
    def get_group_by_id(self, group_id: int) -> Optional[DieStudyGroup]:
        """Get a die study group by ID with members loaded."""
        model = self.session.get(DieStudyGroupModel, group_id)
        if not model:
            return None
        return self._group_to_domain(model)
    
    def get_all_groups(
        self, 
        die_side: Optional[DieSide] = None,
        issuer_id: Optional[int] = None
    ) -> List[DieStudyGroup]:
        """Get all die study groups with optional filtering."""
        query = self.session.query(DieStudyGroupModel)
        
        if die_side:
            query = query.filter(DieStudyGroupModel.die_side == die_side.value)
        if issuer_id:
            query = query.filter(DieStudyGroupModel.issuer_id == issuer_id)
        
        models = query.order_by(DieStudyGroupModel.name).all()
        return [self._group_to_domain(m) for m in models]
    
    def update_group(
        self,
        group_id: int,
        name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[DieStudyGroupModel]:
        """Update a die study group."""
        model = self.session.get(DieStudyGroupModel, group_id)
        if not model:
            return None
        
        if name is not None:
            model.name = name
        if notes is not None:
            model.notes = notes
        
        self.session.flush()
        return model
    
    def delete_group(self, group_id: int) -> bool:
        """Delete a die study group and all memberships."""
        model = self.session.get(DieStudyGroupModel, group_id)
        if model:
            self.session.delete(model)
            return True
        return False
    
    def add_member_to_group(
        self,
        group_id: int,
        coin_id: int,
        sequence_position: Optional[int] = None,
    ) -> Optional[DieGroupMemberModel]:
        """Add a coin to a die study group."""
        # Check group exists
        group = self.session.get(DieStudyGroupModel, group_id)
        if not group:
            return None
        
        # Check if already a member
        existing = self.session.query(DieGroupMemberModel).filter(
            DieGroupMemberModel.die_group_id == group_id,
            DieGroupMemberModel.coin_id == coin_id
        ).first()
        
        if existing:
            # Update position if provided
            if sequence_position is not None:
                existing.sequence_position = sequence_position
                self.session.flush()
            return existing
        
        # Create new membership
        member = DieGroupMemberModel(
            die_group_id=group_id,
            coin_id=coin_id,
            sequence_position=sequence_position,
        )
        
        self.session.add(member)
        self.session.flush()
        return member
    
    def remove_member_from_group(self, group_id: int, coin_id: int) -> bool:
        """Remove a coin from a die study group."""
        member = self.session.query(DieGroupMemberModel).filter(
            DieGroupMemberModel.die_group_id == group_id,
            DieGroupMemberModel.coin_id == coin_id
        ).first()
        
        if member:
            self.session.delete(member)
            return True
        return False
    
    def get_groups_for_coin(self, coin_id: int) -> List[DieStudyGroup]:
        """Get all die study groups that contain a specific coin."""
        members = self.session.query(DieGroupMemberModel).filter(
            DieGroupMemberModel.coin_id == coin_id
        ).all()
        
        group_ids = [m.die_group_id for m in members]
        if not group_ids:
            return []
        
        models = self.session.query(DieStudyGroupModel).filter(
            DieStudyGroupModel.id.in_(group_ids)
        ).all()
        
        return [self._group_to_domain(m) for m in models]
    
    def _group_to_domain(self, model: DieStudyGroupModel) -> DieStudyGroup:
        """Convert ORM model to domain entity."""
        members = []
        member_positions = {}
        
        for m in model.members:
            members.append(m.coin_id)
            if m.sequence_position is not None:
                member_positions[m.coin_id] = m.sequence_position
        
        return DieStudyGroup(
            id=model.id,
            name=model.name,
            die_side=DieSide(model.die_side),
            issuer_id=model.issuer_id,
            mint_id=model.mint_id,
            notes=model.notes,
            created_at=model.created_at,
            members=members,
            member_positions=member_positions,
        )
