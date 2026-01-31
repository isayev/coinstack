import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from src.domain.coin import Coin, CoinImage
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel, CoinImageModel, ProvenanceEventModel, CoinReferenceModel, MonogramModel
from src.infrastructure.services.catalogs.catalog_systems import catalog_to_system, SYSTEM_TO_DISPLAY
from src.infrastructure.mappers.coin_mapper import CoinMapper

class SqlAlchemyCoinRepository(ICoinRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, coin: Coin) -> Coin:
        # Map Domain -> ORM using the helper method
        orm_coin = CoinMapper.to_model(coin)
        
        # Handle Images with diffing logic to prevent ID churn and unnecessary DB writes
        if coin.id:
            # Load existing images to allow for stable merging
            existing_orm = self.session.query(CoinModel).options(
                selectinload(CoinModel.images)
            ).filter(CoinModel.id == coin.id).first()
            
            if existing_orm:
                existing_images_map = {img.url: img for img in existing_orm.images}
                final_images = []
                for img in coin.images:
                    if img.url in existing_images_map:
                        # Reuse existing ORM object and update its attributes
                        orm_img = existing_images_map[img.url]
                        orm_img.image_type = img.image_type
                        orm_img.is_primary = img.is_primary
                        final_images.append(orm_img)
                    else:
                        # Create new ORM object for new URL
                        final_images.append(CoinImageModel(
                            url=img.url,
                            image_type=img.image_type,
                            is_primary=img.is_primary
                        ))
                orm_coin.images = final_images
            else:
                # Coin has an ID but not found in DB, treat as new images
                orm_coin.images = [
                    CoinImageModel(url=img.url, image_type=img.image_type, is_primary=img.is_primary)
                    for img in coin.images
                ]
        else:
            # New coin without ID
            orm_coin.images = [
                CoinImageModel(url=img.url, image_type=img.image_type, is_primary=img.is_primary)
                for img in coin.images
            ]
        
        # References are persisted via ReferenceSyncService from API create/update and LLM approve.
        # Do not write coin.references into llm_suggested_references; reserve that for pending suggestions only.

        # Handle Monograms (Many-to-Many)
        if coin.monograms:
            # We assume monograms are already persisted or managed elsewhere for now,
            # OR we try to find existing ones by label/id. 
            # For simplicity in this iteration, we look up by ID or create if needed (simple check).
            orm_monograms = []
            for m in coin.monograms:
                if m.id:
                    mono = self.session.get(MonogramModel, m.id)
                    if mono:
                        orm_monograms.append(mono)
                # If no ID, we might create, but let's stick to linking for now to be safe
            orm_coin.monograms = orm_monograms

        # Merge handles both insert (if id is None) and update
        merged_coin = self.session.merge(orm_coin)
        
        self.session.flush()  # Get ID
        
        # Map ORM -> Domain (return updated entity with ID)
        return CoinMapper.to_domain(merged_coin)

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images),  # Eager load images to prevent N+1 queries
            selectinload(CoinModel.provenance_events),  # Eager load provenance
            selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type),  # Eager load references with their types
            selectinload(CoinModel.monograms) # Eager load monograms
        ).filter(CoinModel.id == coin_id).first()
        if not orm_coin:
            return None
        return CoinMapper.to_domain(orm_coin)

    def get_by_ids(self, coin_ids: List[int]) -> List[Coin]:
        """Retrieve multiple coins by their IDs efficiently with chunking.

        Uses chunking to avoid SQLite's 999 parameter limit for IN clauses.
        """
        if not coin_ids:
            return []

        CHUNK_SIZE = 500  # SQLite limit is 999, use 500 for safety
        all_coins: Dict[int, Coin] = {}

        for i in range(0, len(coin_ids), CHUNK_SIZE):
            chunk = coin_ids[i:i + CHUNK_SIZE]
            orm_coins = self.session.query(CoinModel).options(
                selectinload(CoinModel.images),
                selectinload(CoinModel.provenance_events),
                selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type),
                selectinload(CoinModel.monograms)
            ).filter(CoinModel.id.in_(chunk)).all()

            for orm in orm_coins:
                all_coins[orm.id] = CoinMapper.to_domain(orm)

        # Return in the order of input IDs
        return [all_coins[cid] for cid in coin_ids if cid in all_coins]

    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        sort_by: Optional[str] = None, 
        sort_dir: str = "asc",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Coin]:
        query = self.session.query(CoinModel).options(
            selectinload(CoinModel.images),  # Eager load images to prevent N+1 queries
            selectinload(CoinModel.provenance_events),  # Eager load provenance
            selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type),  # Eager load references
            selectinload(CoinModel.monograms)
        )
        
        # Apply filters
        query = self._apply_filters(query, filters)

        # Apply sorting
        if sort_by:
            sort_column = None
            if sort_by == "id":
                sort_column = CoinModel.id
            elif sort_by == "created":
                sort_column = CoinModel.id # Proxy for creation time
            elif sort_by == "year":
                sort_column = CoinModel.year_start
            elif sort_by == "price":
                sort_column = CoinModel.acquisition_price
            elif sort_by == "acquired":
                sort_column = CoinModel.acquisition_date
            elif sort_by == "grade":
                sort_column = CoinModel.grade
            elif sort_by == "name":
                sort_column = CoinModel.issuer
            elif sort_by == "weight":
                sort_column = CoinModel.weight_g
            elif sort_by == "category":
                sort_column = CoinModel.category
            elif sort_by == "denomination":
                sort_column = CoinModel.denomination
            elif sort_by == "metal":
                sort_column = CoinModel.metal
            elif sort_by == "rarity":
                sort_column = CoinModel.rarity
            elif sort_by == "value":
                # Sort by market_value (NULLs will be handled by nulls_last)
                sort_column = CoinModel.market_value
            elif sort_by == "mint":
                sort_column = CoinModel.mint
            elif sort_by == "diameter":
                sort_column = CoinModel.diameter_mm
            elif sort_by == "die_axis":
                sort_column = CoinModel.die_axis
            elif sort_by == "specific_gravity":
                sort_column = CoinModel.specific_gravity
            elif sort_by == "issue_status":
                sort_column = CoinModel.issue_status
                
            if sort_column is not None:
                from sqlalchemy import nulls_last
                if sort_dir == "desc":
                    query = query.order_by(nulls_last(sort_column.desc()))
                else:
                    query = query.order_by(nulls_last(sort_column.asc()))
            else:
                # Unknown sort_by value - log warning and use default
                import logging
                logging.warning(f"Unknown sort_by value: {sort_by}, using default sort")
                query = query.order_by(CoinModel.id.desc())
        else:
            # Default sort if not specified
            query = query.order_by(CoinModel.id.desc())

        orm_coins = query.offset(skip).limit(limit).all()
        return [CoinMapper.to_domain(c) for c in orm_coins]

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        query = self.session.query(CoinModel)
        query = self._apply_filters(query, filters)
        return query.count()
    
    def get_by_reference(
        self,
        catalog: str,
        number: str,
        volume: Optional[str] = None
    ) -> List[Coin]:
        """
        Find coins by catalog reference.
        
        Searches the coin_references table and returns matching coins.
        catalog: Display name (RIC, Crawford, RRC, RPC, etc.) — normalized to
        reference_types.system (ric, crawford, rpc) before query.
        """
        from sqlalchemy import text
        
        # Normalize API catalog to reference_types.system (lowercase; RRC/Crawford -> crawford)
        system = catalog_to_system(catalog)
        if not system or not number:
            return []

        # Build query to find coin IDs from coin_references via reference_types
        if volume:
            result = self.session.execute(
                text("""
                    SELECT DISTINCT cr.coin_id 
                    FROM coin_references cr
                    JOIN reference_types rt ON cr.reference_type_id = rt.id
                    WHERE rt.system = :system
                      AND rt.number = :number
                      AND rt.volume = :volume
                """),
                {"system": system, "number": number, "volume": volume}
            )
        else:
            result = self.session.execute(
                text("""
                    SELECT DISTINCT cr.coin_id 
                    FROM coin_references cr
                    JOIN reference_types rt ON cr.reference_type_id = rt.id
                    WHERE rt.system = :system
                      AND rt.number = :number
                """),
                {"system": system, "number": number}
            )
        
        coin_ids = [row[0] for row in result.fetchall()]
        
        if not coin_ids:
            return []
        
        # Fetch coins with references eager-loaded to avoid N+1 when serializing
        orm_coins = self.session.query(CoinModel).options(
            selectinload(CoinModel.images),
            selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type),
            selectinload(CoinModel.provenance_events),
        ).filter(CoinModel.id.in_(coin_ids)).all()
        
        return [CoinMapper.to_domain(c) for c in orm_coins]

    def _apply_filters(self, query, filters: Optional[Dict[str, Any]]):
        """Apply filter conditions to a query."""
        from sqlalchemy import and_, or_, func
        if not filters:
            return query
        
        conditions = []
        
        # Exact match filters (data normalized on input, direct comparison for index usage)
        if "category" in filters:
            conditions.append(CoinModel.category == filters["category"].lower())

        if "metal" in filters:
            conditions.append(CoinModel.metal == filters["metal"].lower())
        
        if "denomination" in filters:
            conditions.append(CoinModel.denomination == filters["denomination"])
        
        if "grading_state" in filters:
            conditions.append(CoinModel.grading_state == filters["grading_state"])
        
        if "grade_service" in filters:
            conditions.append(CoinModel.grade_service == filters["grade_service"])
        
        # Partial match for issuer (case-insensitive LIKE)
        if "issuer" in filters:
            conditions.append(CoinModel.issuer.ilike(f"%{filters['issuer']}%"))
        
        # Grade filter (Smart Buckets)
        if "grade" in filters:
            g = filters["grade"].lower()
            if g == 'poor':
                conditions.append(or_(CoinModel.grade.ilike('%Poor%'), CoinModel.grade.ilike('%Fair%'), CoinModel.grade.ilike('%Basal%'), CoinModel.grade.ilike('AG%')))
            elif g == 'good':
                conditions.append(or_(CoinModel.grade.ilike('%Good%'), CoinModel.grade.ilike('%VG%')))
            elif g == 'fine':
                conditions.append(or_(CoinModel.grade.ilike('%Fine%'), CoinModel.grade.ilike('%VF%'), CoinModel.grade == 'F', CoinModel.grade.ilike('F %')))
            elif g == 'ef':
                conditions.append(or_(CoinModel.grade.ilike('%XF%'), CoinModel.grade.ilike('%EF%'), CoinModel.grade.ilike('%Extremely%')))
            elif g == 'au':
                conditions.append(or_(CoinModel.grade.ilike('%AU%'), CoinModel.grade.ilike('%About Unc%')))
            elif g == 'ms':
                conditions.append(or_(CoinModel.grade.ilike('%MS%'), CoinModel.grade.ilike('%Mint State%'), CoinModel.grade.ilike('%FDC%'), CoinModel.grade.ilike('%Unc%')))
            else:
                conditions.append(CoinModel.grade.ilike(f"%{filters['grade']}%"))

        # Rarity filter
        if "rarity" in filters:
             conditions.append(CoinModel.rarity.ilike(filters["rarity"]))

        # Year range filters
        if "year_start" in filters:
            # Coins minted on or after this year
            conditions.append(CoinModel.year_start >= filters["year_start"])
        
        if "year_end" in filters:
            # Coins minted on or before this year
            conditions.append(CoinModel.year_start <= filters["year_end"])
        
        # Weight range filters
        if "weight_min" in filters:
            conditions.append(CoinModel.weight_g >= filters["weight_min"])
        
        if "weight_max" in filters:
            conditions.append(CoinModel.weight_g <= filters["weight_max"])
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        return query
        
    def delete(self, coin_id: int) -> bool:
        orm_coin = self.session.get(CoinModel, coin_id)
        if orm_coin:
            self.session.delete(orm_coin)
            return True
        return False
