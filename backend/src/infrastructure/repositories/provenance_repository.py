"""
Provenance Repository Implementation (V3).

Handles persistence of provenance events for coins using unified source_name field.
Implements IProvenanceRepository protocol.
"""

from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from src.domain.coin import ProvenanceEntry, ProvenanceEventType, ProvenanceSource
from src.domain.repositories import IProvenanceRepository
from src.infrastructure.persistence.orm import ProvenanceEventModel
from src.infrastructure.mappers.coin_mapper import CoinMapper


class SqlAlchemyProvenanceRepository(IProvenanceRepository):
    """
    Repository for managing coin provenance events.

    Implements the IProvenanceRepository protocol with clean 1:1 field mapping
    using the unified source_name field (V3 schema).
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_coin_id(self, coin_id: int) -> List[ProvenanceEntry]:
        """
        Get all provenance entries for a coin, ordered by sort_order.

        Returns complete pedigree timeline from earliest (sort_order=0)
        to most recent (highest sort_order, typically ACQUISITION).
        """
        models = self.session.query(ProvenanceEventModel).filter(
            ProvenanceEventModel.coin_id == coin_id
        ).order_by(
            ProvenanceEventModel.sort_order.asc(),
            ProvenanceEventModel.event_date.asc().nulls_last()
        ).all()

        return [CoinMapper._provenance_to_domain(m) for m in models]

    def get_by_id(self, provenance_id: int) -> Optional[ProvenanceEntry]:
        """Get a specific provenance entry by ID."""
        model = self.session.get(ProvenanceEventModel, provenance_id)
        return CoinMapper._provenance_to_domain(model) if model else None

    def create(self, coin_id: int, entry: ProvenanceEntry) -> ProvenanceEntry:
        """
        Create a new provenance entry for a coin.

        Returns entry with ID assigned.
        """
        model = CoinMapper._provenance_to_model(entry)
        model.coin_id = coin_id
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()  # Get ID without committing

        return CoinMapper._provenance_to_domain(model)

    def create_bulk(self, coin_id: int, entries: List[ProvenanceEntry]) -> List[ProvenanceEntry]:
        """Create multiple provenance entries efficiently."""
        if not entries:
            return []

        models = []
        for entry in entries:
            model = CoinMapper._provenance_to_model(entry)
            model.coin_id = coin_id
            model.id = None
            models.append(model)

        self.session.add_all(models)
        self.session.flush()

        return [CoinMapper._provenance_to_domain(m) for m in models]

    def update(self, provenance_id: int, entry: ProvenanceEntry) -> Optional[ProvenanceEntry]:
        """Update an existing provenance entry."""
        model = self.session.get(ProvenanceEventModel, provenance_id)
        if not model:
            return None

        # Get event_type value
        event_type_value = entry.event_type.value if hasattr(entry.event_type, 'value') else str(entry.event_type)
        source_origin_value = entry.source_origin.value if hasattr(entry.source_origin, 'value') else str(entry.source_origin)

        # Update all fields from domain object
        model.event_type = event_type_value
        model.source_name = entry.source_name
        model.event_date = entry.event_date
        model.date_string = entry.date_string
        model.sale_name = entry.sale_name
        model.sale_number = entry.sale_number
        model.lot_number = entry.lot_number
        model.catalog_reference = entry.catalog_reference
        model.hammer_price = entry.hammer_price
        model.buyers_premium_pct = entry.buyers_premium_pct
        model.total_price = entry.total_price
        model.currency = entry.currency
        model.notes = entry.notes
        model.url = entry.url
        model.receipt_available = entry.receipt_available
        model.source_origin = source_origin_value
        model.auction_data_id = entry.auction_data_id
        model.sort_order = entry.sort_order

        # Update legacy fields for backward compat
        model.auction_house = entry.source_name if event_type_value == "auction" else None
        model.dealer_name = entry.source_name if event_type_value == "dealer" else None
        model.collection_name = entry.source_name if event_type_value == "collection" else None
        model.sale_series = entry.sale_name

        self.session.flush()
        return CoinMapper._provenance_to_domain(model)

    def delete(self, provenance_id: int) -> bool:
        """Delete a provenance entry by ID."""
        model = self.session.get(ProvenanceEventModel, provenance_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def find_by_source(
        self,
        event_type: ProvenanceEventType,
        source_name: str,
        event_date: Optional[date] = None
    ) -> List[ProvenanceEntry]:
        """
        Find provenance entries by source details (for deduplication).

        Case-insensitive search on source_name.
        """
        event_type_value = event_type.value if hasattr(event_type, 'value') else str(event_type)

        query = self.session.query(ProvenanceEventModel).filter(
            and_(
                ProvenanceEventModel.event_type == event_type_value,
                func.lower(ProvenanceEventModel.source_name) == source_name.lower()
            )
        )

        if event_date:
            query = query.filter(ProvenanceEventModel.event_date == event_date)

        models = query.all()
        return [CoinMapper._provenance_to_domain(m) for m in models]

    def get_acquisition_by_coin(self, coin_id: int) -> Optional[ProvenanceEntry]:
        """
        Get the acquisition (current ownership) entry for a coin, if exists.

        Returns the provenance entry with event_type='acquisition'.
        """
        model = self.session.query(ProvenanceEventModel).filter(
            and_(
                ProvenanceEventModel.coin_id == coin_id,
                ProvenanceEventModel.event_type == ProvenanceEventType.ACQUISITION.value
            )
        ).first()

        return CoinMapper._provenance_to_domain(model) if model else None

    def get_earliest_by_coin(self, coin_id: int) -> Optional[ProvenanceEntry]:
        """Get the earliest known provenance entry for a coin."""
        model = self.session.query(ProvenanceEventModel).filter(
            ProvenanceEventModel.coin_id == coin_id
        ).order_by(
            ProvenanceEventModel.event_date.asc().nulls_last(),
            ProvenanceEventModel.sort_order.asc()
        ).first()

        return CoinMapper._provenance_to_domain(model) if model else None

    # -------------------------------------------------------------------------
    # Legacy compatibility methods (deprecated, use create/update instead)
    # -------------------------------------------------------------------------

    def add(
        self,
        coin_id: int,
        event_type: str,
        source_name: str,
        event_date: Optional[date] = None,
        date_string: Optional[str] = None,
        lot_number: Optional[str] = None,
        hammer_price=None,
        total_price=None,
        currency: Optional[str] = None,
        notes: Optional[str] = None,
        url: Optional[str] = None,
        sort_order: int = 0,
    ) -> ProvenanceEntry:
        """
        Legacy add method for backward compatibility.

        DEPRECATED: Use create() with ProvenanceEntry instead.
        """
        try:
            evt_type = ProvenanceEventType(event_type)
        except ValueError:
            evt_type = ProvenanceEventType.UNKNOWN

        entry = ProvenanceEntry(
            event_type=evt_type,
            source_name=source_name,
            event_date=event_date,
            date_string=date_string,
            lot_number=lot_number,
            hammer_price=hammer_price,
            total_price=total_price,
            currency=currency,
            notes=notes,
            url=url,
            sort_order=sort_order,
            source_origin=ProvenanceSource.MANUAL_ENTRY,
        )

        return self.create(coin_id, entry)
