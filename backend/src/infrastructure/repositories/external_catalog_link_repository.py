"""
External Catalog Link Repository - SQLAlchemy implementation.

Manages links to external online catalog databases like OCRE, Nomisma, CRRO, RPC Online.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.domain.coin import ExternalCatalogLink
from src.domain.repositories import IExternalCatalogLinkRepository
from src.infrastructure.persistence.orm import ExternalCatalogLinkModel


class SqlAlchemyExternalCatalogLinkRepository(IExternalCatalogLinkRepository):
    """SQLAlchemy implementation of IExternalCatalogLinkRepository."""

    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: ExternalCatalogLinkModel) -> ExternalCatalogLink:
        """Convert ORM model to domain entity."""
        return ExternalCatalogLink(
            id=model.id,
            reference_type_id=model.reference_type_id,
            catalog_source=model.catalog_source,
            external_id=model.external_id,
            external_url=model.external_url,
            external_data=model.external_data,
            last_synced_at=model.last_synced_at,
            sync_status=model.sync_status or "pending",
        )

    def _to_model(self, entity: ExternalCatalogLink) -> ExternalCatalogLinkModel:
        """Convert domain entity to ORM model."""
        model = ExternalCatalogLinkModel(
            reference_type_id=entity.reference_type_id,
            catalog_source=entity.catalog_source,
            external_id=entity.external_id,
            external_url=entity.external_url,
            external_data=entity.external_data,
            last_synced_at=entity.last_synced_at,
            sync_status=entity.sync_status,
        )
        if entity.id:
            model.id = entity.id
        return model

    def get_by_reference_type_id(self, reference_type_id: int) -> List[ExternalCatalogLink]:
        """Get all external links for a reference type."""
        models = (
            self.session.query(ExternalCatalogLinkModel)
            .filter(ExternalCatalogLinkModel.reference_type_id == reference_type_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_source(
        self,
        reference_type_id: int,
        catalog_source: str
    ) -> Optional[ExternalCatalogLink]:
        """Get a specific external link by reference type and source."""
        model = (
            self.session.query(ExternalCatalogLinkModel)
            .filter(
                ExternalCatalogLinkModel.reference_type_id == reference_type_id,
                ExternalCatalogLinkModel.catalog_source == catalog_source
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def create(self, link: ExternalCatalogLink) -> ExternalCatalogLink:
        """Create a new external catalog link."""
        model = self._to_model(link)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def upsert(self, link: ExternalCatalogLink) -> ExternalCatalogLink:
        """Create or update an external catalog link."""
        existing = self.get_by_source(link.reference_type_id, link.catalog_source)

        if existing and existing.id:
            return self.update(existing.id, link) or link
        else:
            return self.create(link)

    def update(self, link_id: int, link: ExternalCatalogLink) -> Optional[ExternalCatalogLink]:
        """Update an existing external catalog link."""
        model = self.session.query(ExternalCatalogLinkModel).get(link_id)
        if not model:
            return None

        model.external_id = link.external_id
        model.external_url = link.external_url
        model.external_data = link.external_data
        model.sync_status = link.sync_status
        if link.last_synced_at:
            model.last_synced_at = link.last_synced_at

        self.session.flush()
        return self._to_domain(model)

    def delete(self, link_id: int) -> bool:
        """Delete an external catalog link by ID."""
        model = self.session.query(ExternalCatalogLinkModel).get(link_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def find_by_external_id(
        self,
        catalog_source: str,
        external_id: str
    ) -> Optional[ExternalCatalogLink]:
        """Find an external link by source and external ID."""
        model = (
            self.session.query(ExternalCatalogLinkModel)
            .filter(
                ExternalCatalogLinkModel.catalog_source == catalog_source,
                ExternalCatalogLinkModel.external_id == external_id
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def list_pending_sync(self, limit: int = 100) -> List[ExternalCatalogLink]:
        """Get external links pending synchronization."""
        models = (
            self.session.query(ExternalCatalogLinkModel)
            .filter(ExternalCatalogLinkModel.sync_status == "pending")
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def mark_synced(
        self,
        link_id: int,
        external_data: Optional[str] = None
    ) -> bool:
        """Mark an external link as synced with optional data."""
        model = self.session.query(ExternalCatalogLinkModel).get(link_id)
        if not model:
            return False

        model.sync_status = "synced"
        model.last_synced_at = datetime.utcnow()
        if external_data:
            model.external_data = external_data

        self.session.flush()
        return True
