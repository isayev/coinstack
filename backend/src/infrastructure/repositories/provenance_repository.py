"""
Provenance Repository Implementation.

Handles persistence of provenance events for coins.
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from src.domain.coin import ProvenanceEntry
from src.infrastructure.persistence.orm import ProvenanceEventModel


class SqlAlchemyProvenanceRepository:
    """Repository for managing coin provenance events."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_coin_id(self, coin_id: int) -> List[ProvenanceEntry]:
        """Get all provenance entries for a coin, ordered by sort_order."""
        models = self.session.query(ProvenanceEventModel).filter(
            ProvenanceEventModel.coin_id == coin_id
        ).order_by(ProvenanceEventModel.sort_order.asc()).all()
        
        return [self._to_domain(m) for m in models]
    
    def get_by_id(self, provenance_id: int) -> Optional[ProvenanceEventModel]:
        """Get a specific provenance entry by ID."""
        return self.session.get(ProvenanceEventModel, provenance_id)
    
    def add(
        self,
        coin_id: int,
        event_type: str,
        source_name: str,
        event_date: Optional[date] = None,
        lot_number: Optional[str] = None,
        hammer_price: Optional[Decimal] = None,
        total_price: Optional[Decimal] = None,
        currency: Optional[str] = None,
        notes: Optional[str] = None,
        url: Optional[str] = None,
        sort_order: int = 0,
    ) -> ProvenanceEventModel:
        """
        Add a provenance entry to a coin.
        
        Args:
            coin_id: ID of the coin
            event_type: Type of event (auction, dealer, collection, private_sale)
            source_name: Name of the source (auction house, dealer, collection)
            event_date: Date of the event
            lot_number: Lot number if auction
            hammer_price: Hammer price if auction
            total_price: Total price including premium
            currency: Currency code (USD, EUR, GBP)
            notes: Additional notes
            url: URL to source documentation
            sort_order: Order for display (0 = earliest/first)
        
        Returns:
            Created ProvenanceEventModel
        """
        # Determine which field to populate based on event type
        auction_house = None
        dealer_name = None
        collection_name = None
        
        if event_type == "auction":
            auction_house = source_name
        elif event_type == "dealer":
            dealer_name = source_name
        elif event_type == "collection":
            collection_name = source_name
        else:
            # For other types, use auction_house as general storage
            auction_house = source_name
        
        model = ProvenanceEventModel(
            coin_id=coin_id,
            event_type=event_type,
            event_date=event_date,
            auction_house=auction_house,
            dealer_name=dealer_name,
            collection_name=collection_name,
            lot_number=lot_number,
            hammer_price=hammer_price,
            total_price=total_price,
            currency=currency,
            notes=notes,
            url=url,
            sort_order=sort_order,
        )
        
        self.session.add(model)
        self.session.flush()
        return model
    
    def update(
        self,
        provenance_id: int,
        event_type: Optional[str] = None,
        source_name: Optional[str] = None,
        event_date: Optional[date] = None,
        lot_number: Optional[str] = None,
        hammer_price: Optional[Decimal] = None,
        total_price: Optional[Decimal] = None,
        currency: Optional[str] = None,
        notes: Optional[str] = None,
        url: Optional[str] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ProvenanceEventModel]:
        """
        Update a provenance entry.
        
        Returns:
            Updated model or None if not found
        """
        model = self.session.get(ProvenanceEventModel, provenance_id)
        if not model:
            return None
        
        if event_type is not None:
            model.event_type = event_type
            # Update the appropriate name field
            if source_name is not None:
                if event_type == "auction":
                    model.auction_house = source_name
                    model.dealer_name = None
                    model.collection_name = None
                elif event_type == "dealer":
                    model.dealer_name = source_name
                    model.auction_house = None
                    model.collection_name = None
                elif event_type == "collection":
                    model.collection_name = source_name
                    model.auction_house = None
                    model.dealer_name = None
        elif source_name is not None:
            # Update name without changing type
            if model.event_type == "auction":
                model.auction_house = source_name
            elif model.event_type == "dealer":
                model.dealer_name = source_name
            elif model.event_type == "collection":
                model.collection_name = source_name
        
        if event_date is not None:
            model.event_date = event_date
        if lot_number is not None:
            model.lot_number = lot_number
        if hammer_price is not None:
            model.hammer_price = hammer_price
        if total_price is not None:
            model.total_price = total_price
        if currency is not None:
            model.currency = currency
        if notes is not None:
            model.notes = notes
        if url is not None:
            model.url = url
        if sort_order is not None:
            model.sort_order = sort_order
        
        self.session.flush()
        return model
    
    def delete(self, provenance_id: int) -> bool:
        """
        Delete a provenance entry.
        
        Returns:
            True if deleted, False if not found
        """
        model = self.session.get(ProvenanceEventModel, provenance_id)
        if model:
            self.session.delete(model)
            return True
        return False
    
    def _to_domain(self, model: ProvenanceEventModel) -> ProvenanceEntry:
        """Map ORM model to domain value object."""
        # Determine source name
        source_name = ""
        if model.event_type == "auction":
            source_name = model.auction_house or ""
        elif model.event_type == "dealer":
            source_name = model.dealer_name or ""
        elif model.event_type == "collection":
            source_name = model.collection_name or ""
        else:
            source_name = model.auction_house or model.dealer_name or model.collection_name or ""
        
        # Build raw text
        raw_parts = []
        if source_name:
            raw_parts.append(source_name)
        if model.event_date:
            raw_parts.append(str(model.event_date.year))
        if model.lot_number:
            raw_parts.append(f"lot {model.lot_number}")
        raw_text = ", ".join(raw_parts) if raw_parts else ""
        
        return ProvenanceEntry(
            source_type=model.event_type,
            source_name=source_name,
            event_date=model.event_date,
            lot_number=model.lot_number,
            notes=model.notes,
            raw_text=raw_text
        )
