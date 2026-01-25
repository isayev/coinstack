from typing import Optional, List
from sqlalchemy.orm import Session
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal, 
    GradingDetails, AcquisitionDetails, GradingState, GradeService, CoinImage
)
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel, CoinImageModel

class SqlAlchemyCoinRepository(ICoinRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, coin: Coin) -> Coin:
        # Map Domain -> ORM
        orm_coin = CoinModel(
            id=coin.id,
            category=coin.category.value,
            metal=coin.metal.value,
            weight_g=coin.dimensions.weight_g,
            diameter_mm=coin.dimensions.diameter_mm,
            die_axis=coin.dimensions.die_axis,
            issuer=coin.attribution.issuer,
            mint=coin.attribution.mint,
            year_start=coin.attribution.year_start,
            year_end=coin.attribution.year_end,
            grading_state=coin.grading.grading_state.value,
            grade=coin.grading.grade,
            grade_service=coin.grading.service.value if coin.grading.service else None,
            certification_number=coin.grading.certification_number,
            strike_quality=coin.grading.strike,
            surface_quality=coin.grading.surface
        )

        if coin.acquisition:
            orm_coin.acquisition_price = coin.acquisition.price
            orm_coin.acquisition_currency = coin.acquisition.currency
            orm_coin.acquisition_source = coin.acquisition.source
            orm_coin.acquisition_date = coin.acquisition.date
            orm_coin.acquisition_url = coin.acquisition.url
        
        # Handle Images
        # For simplicity in this sync implementation, we clear and recreate images
        # In a highly optimized system, we would diff them.
        # But wait, `merge` might handle list updates if we provide the objects.
        # However, domain `CoinImage` has no ID, so they are Value Objects effectively.
        # We need to map them to ORM objects.
        
        orm_images = []
        for img in coin.images:
            orm_images.append(CoinImageModel(
                url=img.url,
                image_type=img.image_type,
                is_primary=img.is_primary
            ))
        orm_coin.images = orm_images

        # Merge handles both insert (if id is None) and update
        merged_coin = self.session.merge(orm_coin)
        self.session.flush() # Get ID
        
        # Map ORM -> Domain (return updated entity with ID)
        return self._to_domain(merged_coin)

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        orm_coin = self.session.get(CoinModel, coin_id)
        if not orm_coin:
            return None
        return self._to_domain(orm_coin)

    def get_all(self, skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, sort_dir: str = "asc") -> List[Coin]:
        query = self.session.query(CoinModel)
        
        # Apply sorting
        if sort_by:
            sort_column = None
            if sort_by == "created":
                sort_column = CoinModel.id # Proxy for creation time
            elif sort_by == "year":
                sort_column = CoinModel.year_start
            elif sort_by == "price":
                sort_column = CoinModel.acquisition_price
            elif sort_by == "grade":
                sort_column = CoinModel.grade
            elif sort_by == "name":
                sort_column = CoinModel.issuer
            elif sort_by == "weight":
                sort_column = CoinModel.weight_g
                
            if sort_column is not None:
                if sort_dir == "desc":
                    from sqlalchemy import nulls_last
                    query = query.order_by(nulls_last(sort_column.desc()))
                else:
                    from sqlalchemy import nulls_last
                    query = query.order_by(nulls_last(sort_column.asc()))
        
        # Default sort if not specified or fallback
        if not sort_by:
             query = query.order_by(CoinModel.id.desc())

        orm_coins = query.offset(skip).limit(limit).all()
        return [self._to_domain(c) for c in orm_coins]

    def count(self) -> int:
        return self.session.query(CoinModel).count()
        
    def delete(self, coin_id: int) -> bool:
        orm_coin = self.session.get(CoinModel, coin_id)
        if orm_coin:
            self.session.delete(orm_coin)
            self.session.commit()
            return True
        return False

    def _to_domain(self, orm_coin: CoinModel) -> Coin:
        acquisition = None
        if orm_coin.acquisition_price is not None:
            acquisition = AcquisitionDetails(
                price=orm_coin.acquisition_price,
                currency=orm_coin.acquisition_currency,
                source=orm_coin.acquisition_source,
                date=orm_coin.acquisition_date,
                url=orm_coin.acquisition_url
            )

        grading = GradingDetails(
            grading_state=GradingState(orm_coin.grading_state),
            grade=orm_coin.grade,
            service=GradeService(orm_coin.grade_service) if orm_coin.grade_service else None,
            certification_number=orm_coin.certification_number,
            strike=orm_coin.strike_quality,
            surface=orm_coin.surface_quality
        )
        
        images = []
        for img in orm_coin.images:
            images.append(CoinImage(
                url=img.url,
                image_type=img.image_type,
                is_primary=img.is_primary
            ))

        return Coin(
            id=orm_coin.id,
            category=Category(orm_coin.category),
            metal=Metal(orm_coin.metal),
            dimensions=Dimensions(
                weight_g=orm_coin.weight_g,
                diameter_mm=orm_coin.diameter_mm,
                die_axis=orm_coin.die_axis
            ),
            attribution=Attribution(
                issuer=orm_coin.issuer,
                mint=orm_coin.mint,
                year_start=orm_coin.year_start,
                year_end=orm_coin.year_end
            ),
            grading=grading,
            acquisition=acquisition,
            images=images
        )