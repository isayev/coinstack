from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import json
from decimal import Decimal
from src.domain.auction import AuctionLot
from src.infrastructure.persistence.orm import AuctionDataModel


class SqlAlchemyAuctionDataRepository:
    """Repository for persisting AuctionData using V2 ORM.
    
    Implements the IAuctionDataRepository protocol from src.domain.repositories.
    """
    
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, lot: AuctionLot, coin_id: Optional[int] = None) -> int:
        """
        Insert or update auction lot data. Returns auction_data_id.
        
        Create or update AuctionData from a domain AuctionLot.
        Match is done by URL.
        """
        # 1. Map Domain -> Model
        data_dict = self._map_to_model_dict(lot)
        data_dict['coin_id'] = coin_id
        
        # 2. Check existence by URL
        existing = self.session.query(AuctionDataModel).filter(
            AuctionDataModel.url == lot.url
        ).first()
        
        if existing:
            # UPDATE
            for key, value in data_dict.items():
                if value is not None:
                    setattr(existing, key, value)
            existing.scraped_at = datetime.utcnow().date()
            self.session.add(existing)
            self.session.flush()
            return existing.id
        else:
            # INSERT
            data_dict['scraped_at'] = datetime.utcnow().date()
            new_record = AuctionDataModel(**data_dict)
            self.session.add(new_record)
            self.session.flush()
            return new_record.id

    def get_by_coin_id(self, coin_id: int) -> Optional[AuctionLot]:
        """Get auction data linked to a coin."""
        model = self.session.query(AuctionDataModel).filter(
            AuctionDataModel.coin_id == coin_id
        ).first()
        return self._to_domain(model) if model else None

    def get_by_url(self, url: str) -> Optional[AuctionLot]:
        """Get auction data by unique URL."""
        model = self.session.query(AuctionDataModel).filter(
            AuctionDataModel.url == url
        ).first()
        return self._to_domain(model) if model else None

    def get_comparables(
        self,
        issuer: Optional[str] = None,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        limit: int = 10
    ) -> List[AuctionLot]:
        """Get comparable auction lots for price analysis."""
        query = self.session.query(AuctionDataModel)
        
        if issuer:
            query = query.filter(AuctionDataModel.issuer == issuer)
        if year_start is not None:
            query = query.filter(AuctionDataModel.year_start >= year_start)
        if year_end is not None:
            query = query.filter(AuctionDataModel.year_end <= year_end)
        
        # Order by most recent first, limit results
        query = query.order_by(AuctionDataModel.scraped_at.desc()).limit(limit)
        
        return [self._to_domain(model) for model in query.all()]

    def _to_domain(self, model: AuctionDataModel) -> AuctionLot:
        """Map ORM model back to domain entity."""
        # Parse additional images from JSON
        additional_images = []
        if model.additional_images:
            try:
                additional_images = json.loads(model.additional_images)
            except (json.JSONDecodeError, TypeError):
                additional_images = []
        
        return AuctionLot(
            source=model.source or "",
            lot_id=model.source_lot_id,
            url=model.url,
            sale_name=model.sale_name,
            lot_number=model.lot_number,
            
            # Pricing
            hammer_price=Decimal(str(model.hammer_price)) if model.hammer_price else None,
            estimate_low=Decimal(str(model.estimate_low)) if model.estimate_low else None,
            estimate_high=Decimal(str(model.estimate_high)) if model.estimate_high else None,
            currency=model.currency or "USD",
            
            # Classification
            issuer=model.issuer,
            mint=model.mint,
            year_start=model.year_start,
            year_end=model.year_end,
            
            # Physical
            weight_g=Decimal(str(model.weight_g)) if model.weight_g else None,
            diameter_mm=Decimal(str(model.diameter_mm)) if model.diameter_mm else None,
            die_axis=model.die_axis,
            
            # Grading
            grade=model.grade,
            service=None,  # Not stored in model
            certification=None,  # Not stored in model
            
            # Description
            description=model.description,
            
            # Images
            primary_image_url=model.primary_image_url,
            additional_images=additional_images,
        )

    def _map_to_model_dict(self, lot: AuctionLot) -> dict:
        """Map generic AuctionLot domain object to V2 ORM model dict."""
        return {
            "url": lot.url,
            "source": lot.source,
            "sale_name": lot.sale_name,
            "lot_number": lot.lot_number,
            "source_lot_id": lot.lot_id,
            
            # Pricing
            "hammer_price": lot.hammer_price,
            "estimate_low": lot.estimate_low,
            "estimate_high": lot.estimate_high,
            "currency": lot.currency,
            
            # Classification
            "issuer": lot.issuer,
            "mint": lot.mint,
            "year_start": lot.year_start,
            "year_end": lot.year_end,
            
            # Physical
            "weight_g": lot.weight_g,
            "diameter_mm": lot.diameter_mm,
            "die_axis": lot.die_axis,
            
            # Description
            "title": f"{lot.issuer or 'Coin'} - {lot.source}",
            "description": lot.description,
            
            # Grading
            "grade": lot.grade,
            
            # Photos
            "primary_image_url": lot.primary_image_url,
            "additional_images": json.dumps(lot.additional_images) if lot.additional_images else "[]",
        }
