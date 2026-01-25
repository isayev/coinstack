from sqlalchemy.orm import Session
from datetime import datetime
import json
from src.domain.auction import AuctionLot
from src.infrastructure.persistence.orm import AuctionDataModel

class SqlAlchemyAuctionDataRepository:
    """Repository for persisting AuctionData using V2 ORM."""
    
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, lot: AuctionLot, coin_id: int = None) -> AuctionDataModel:
        """
        Create or update AuctionData from a domain AuctionLot.
        Match is done by URL.
        """
        # 1. Map Domain -> Model
        data_dict = self._map_to_model(lot)
        data_dict['coin_id'] = coin_id
        
        # 2. Check existence by URL
        existing = self.session.query(AuctionDataModel).filter(AuctionDataModel.url == lot.url).first()
        
        if existing:
            # UPDATE
            for key, value in data_dict.items():
                if value is not None:
                    setattr(existing, key, value)
            # Update timestamp if we had one, but strict models usually don't have updated_at unless defined
            existing.scraped_at = datetime.utcnow().date()
            self.session.add(existing)
            self.session.flush()
            return existing
        else:
            # INSERT
            data_dict['scraped_at'] = datetime.utcnow().date()
            new_record = AuctionDataModel(**data_dict)
            self.session.add(new_record)
            self.session.flush()
            return new_record
            
    def _map_to_model(self, lot: AuctionLot) -> dict:
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
