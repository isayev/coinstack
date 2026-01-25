from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
import re

from src.infrastructure.persistence.models_series import SeriesModel, SeriesSlotModel, SeriesMembershipModel

class SeriesService:
    def __init__(self, session: Session):
        self.session = session

    def create_series(self, name: str, series_type: str, target_count: Optional[int] = None, description: Optional[str] = None) -> SeriesModel:
        slug = self._generate_slug(name)
        
        series = SeriesModel(
            name=name,
            slug=slug,
            series_type=series_type,
            target_count=target_count,
            description=description
        )
        self.session.add(series)
        self.session.flush()
        self.session.refresh(series)
        return series

    def add_slot(self, series_id: int, slot_number: int, name: str, description: Optional[str] = None) -> SeriesSlotModel:
        series = self.session.get(SeriesModel, series_id)
        if not series:
            raise ValueError("Series not found")
        
        slot = SeriesSlotModel(
            series_id=series_id,
            slot_number=slot_number,
            name=name,
            description=description
        )
        self.session.add(slot)
        self.session.flush()
        self.session.refresh(slot)
        return slot

    def add_coin_to_series(self, series_id: int, coin_id: int, slot_id: Optional[int] = None) -> SeriesMembershipModel:
        # Check if already a member
        existing = self.session.scalar(
            select(SeriesMembershipModel).where(
                SeriesMembershipModel.series_id == series_id,
                SeriesMembershipModel.coin_id == coin_id
            )
        )
        if existing:
            if slot_id is not None:
                existing.slot_id = slot_id
                self.session.flush()
            return existing

        membership = SeriesMembershipModel(
            series_id=series_id,
            coin_id=coin_id,
            slot_id=slot_id
        )
        self.session.add(membership)
        
        if slot_id:
            slot = self.session.get(SeriesSlotModel, slot_id)
            if slot:
                slot.status = "filled"
        
        self.session.flush()
        self.session.refresh(membership)
        return membership

    def remove_coin_from_series(self, series_id: int, coin_id: int) -> bool:
        membership = self.session.scalar(
            select(SeriesMembershipModel).where(
                SeriesMembershipModel.series_id == series_id,
                SeriesMembershipModel.coin_id == coin_id
            )
        )
        if not membership:
            return False
        
        if membership.slot_id:
            slot = self.session.get(SeriesSlotModel, membership.slot_id)
            if slot:
                slot.status = "empty"
        
        self.session.delete(membership)
        self.session.flush()
        return True

    def _generate_slug(self, name: str) -> str:
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = slug.strip('-')
        
        # Truncate to avoid overflow when adding suffix (100 char limit on column)
        slug = slug[:90]
        
        base_slug = slug
        counter = 1
        
        # Simple retry loop, in a real concurrent scenario handling IntegrityError is better
        # but requires transaction rollback. For now, we improve the check.
        while True:
            stmt = select(SeriesModel).where(SeriesModel.slug == slug)
            if not self.session.scalar(stmt):
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        return slug
