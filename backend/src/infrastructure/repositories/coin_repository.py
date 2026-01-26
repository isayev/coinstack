import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal, 
    GradingDetails, AcquisitionDetails, GradingState, GradeService, CoinImage,
    Design, CatalogReference, ProvenanceEntry
)
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel, CoinImageModel, ProvenanceEventModel, CoinReferenceModel

class SqlAlchemyCoinRepository(ICoinRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, coin: Coin) -> Coin:
        # Map Domain -> ORM using the helper method
        orm_coin = self._to_model(coin)
        
        # Handle Images (separate from _to_model because images are value objects)
        # For simplicity, we clear and recreate images on save.
        orm_images = []
        for img in coin.images:
            orm_images.append(CoinImageModel(
                url=img.url,
                image_type=img.image_type,
                is_primary=img.is_primary
            ))
        orm_coin.images = orm_images
        
        # Handle References (separate from _to_model because they're complex relationships)
        # TODO: Implement proper reference handling with reference_types table
        # For now, skip references as they require complex lookup/creation in reference_types table
        # References will be stored as JSON in llm_suggested_references field temporarily
        if coin.references:
            import json
            orm_coin.llm_suggested_references = json.dumps([ref.raw_text for ref in coin.references])

        # Merge handles both insert (if id is None) and update
        merged_coin = self.session.merge(orm_coin)
        
        self.session.flush()  # Get ID
        
        # Map ORM -> Domain (return updated entity with ID)
        return self._to_domain(merged_coin)

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images),  # Eager load images to prevent N+1 queries
            selectinload(CoinModel.provenance_events),  # Eager load provenance
            selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type)  # Eager load references with their types
        ).filter(CoinModel.id == coin_id).first()
        if not orm_coin:
            return None
        return self._to_domain(orm_coin)

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
            selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type)  # Eager load references
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
        return [self._to_domain(c) for c in orm_coins]

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
        """
        from sqlalchemy import text
        
        # Build query to find coin IDs from coin_references via reference_types
        # The V1 schema uses: coin_references -> reference_types (with system, volume, number)
        if volume:
            result = self.session.execute(
                text("""
                    SELECT DISTINCT cr.coin_id 
                    FROM coin_references cr
                    JOIN reference_types rt ON cr.reference_type_id = rt.id
                    WHERE UPPER(rt.system) = UPPER(:catalog)
                      AND rt.number = :number
                      AND rt.volume = :volume
                """),
                {"catalog": catalog, "number": number, "volume": volume}
            )
        else:
            result = self.session.execute(
                text("""
                    SELECT DISTINCT cr.coin_id 
                    FROM coin_references cr
                    JOIN reference_types rt ON cr.reference_type_id = rt.id
                    WHERE UPPER(rt.system) = UPPER(:catalog)
                      AND rt.number = :number
                """),
                {"catalog": catalog, "number": number}
            )
        
        coin_ids = [row[0] for row in result.fetchall()]
        
        if not coin_ids:
            return []
        
        # Fetch the actual coins
        orm_coins = self.session.query(CoinModel).options(
            selectinload(CoinModel.images)
        ).filter(CoinModel.id.in_(coin_ids)).all()
        
        return [self._to_domain(c) for c in orm_coins]
    
    def _apply_filters(self, query, filters: Optional[Dict[str, Any]]):
        """Apply filter conditions to a query."""
        if not filters:
            return query
        
        conditions = []
        
        # Exact match filters
        if "category" in filters:
            conditions.append(CoinModel.category == filters["category"])
        
        if "metal" in filters:
            conditions.append(CoinModel.metal == filters["metal"])
        
        if "denomination" in filters:
            conditions.append(CoinModel.denomination == filters["denomination"])
        
        if "grading_state" in filters:
            conditions.append(CoinModel.grading_state == filters["grading_state"])
        
        if "grade_service" in filters:
            conditions.append(CoinModel.grade_service == filters["grade_service"])
        
        # Partial match for issuer (case-insensitive LIKE)
        if "issuer" in filters:
            conditions.append(CoinModel.issuer.ilike(f"%{filters['issuer']}%"))
        
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

    def _to_domain(self, model: CoinModel) -> Coin:
        # Build Design value object if any design fields are present
        design = None
        if any([model.obverse_legend, model.obverse_description, 
                model.reverse_legend, model.reverse_description, model.exergue]):
            design = Design(
                obverse_legend=model.obverse_legend,
                obverse_description=model.obverse_description,
                reverse_legend=model.reverse_legend,
                reverse_description=model.reverse_description,
                exergue=model.exergue
            )
        
        return Coin(
            id=model.id,
            category=Category(model.category),
            metal=Metal(model.metal),
            dimensions=Dimensions(
                weight_g=model.weight_g,
                diameter_mm=model.diameter_mm,
                die_axis=model.die_axis
            ),
            attribution=Attribution(
                issuer=model.issuer,
                issuer_id=model.issuer_id,
                mint=model.mint,
                mint_id=model.mint_id,
                year_start=model.year_start,
                year_end=model.year_end
            ),
            grading=GradingDetails(
                grading_state=GradingState(model.grading_state),
                grade=model.grade,
                service=GradeService(model.grade_service) if model.grade_service else None,
                certification_number=model.certification_number,
                strike=model.strike_quality,
                surface=model.surface_quality
            ),
            acquisition=AcquisitionDetails(
                price=model.acquisition_price,
                currency=model.acquisition_currency,
                source=model.acquisition_source,
                date=model.acquisition_date,
                url=model.acquisition_url
            ) if model.acquisition_price is not None else None,
            description=model.description,
            images=[
                CoinImage(url=img.url, image_type=img.image_type, is_primary=img.is_primary)
                for img in model.images
            ],
            denomination=model.denomination,
            portrait_subject=model.portrait_subject,
            design=design,
            # Map references from coin_references -> reference_types
            references=[
                self._reference_to_domain(ref) for ref in model.references
                if ref.reference_type is not None
            ],
            # Map provenance events from ORM to domain value objects
            provenance=[
                self._provenance_to_domain(p) for p in model.provenance_events
            ] if model.provenance_events else [],
            # Collection management fields
            storage_location=model.storage_location,
            personal_notes=model.personal_notes,
            # LLM enrichment fields
            historical_significance=model.historical_significance,
            llm_enriched_at=model.llm_enriched_at.isoformat() if model.llm_enriched_at else None,
            llm_analysis_sections=model.llm_analysis_sections,
            llm_suggested_references=json.loads(model.llm_suggested_references) if model.llm_suggested_references else None,
            llm_suggested_rarity=json.loads(model.llm_suggested_rarity) if model.llm_suggested_rarity else None
        )
    
    def _reference_to_domain(self, model: CoinReferenceModel) -> CatalogReference:
        """Map CoinReferenceModel + ReferenceTypeModel to domain CatalogReference."""
        ref_type = model.reference_type
        if not ref_type:
            # Should not happen if filtered properly, but safety check
            return CatalogReference(
                catalog="unknown",
                number="",
                volume=None,
                suffix=None,
                raw_text=""
            )
        
        # Build raw text from local_ref or construct from parts
        raw_text = ref_type.local_ref or f"{ref_type.system.upper()} {ref_type.volume or ''} {ref_type.number or ''}".strip()
        
        return CatalogReference(
            catalog=ref_type.system.upper(),
            number=ref_type.number or "",
            volume=ref_type.volume,
            suffix=None,  # Not stored in V1 schema
            raw_text=raw_text,
            is_primary=model.is_primary or False,
            notes=model.notes
        )
    
    def _provenance_to_domain(self, model: ProvenanceEventModel) -> ProvenanceEntry:
        """Map ProvenanceEventModel to domain ProvenanceEntry."""
        # Determine source name based on event type
        source_name = ""
        if model.event_type == "auction":
            source_name = model.auction_house or ""
        elif model.event_type == "dealer":
            source_name = model.dealer_name or ""
        elif model.event_type == "collection":
            source_name = model.collection_name or ""
        else:
            source_name = model.auction_house or model.dealer_name or model.collection_name or ""
        
        # Build raw text representation
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

    def _to_model(self, coin: Coin) -> CoinModel:
        return CoinModel(
            id=coin.id,
            category=coin.category.value,
            metal=coin.metal.value,
            weight_g=coin.dimensions.weight_g,
            diameter_mm=coin.dimensions.diameter_mm,
            die_axis=coin.dimensions.die_axis,
            issuer=coin.attribution.issuer,
            issuer_id=coin.attribution.issuer_id,
            mint=coin.attribution.mint,
            mint_id=coin.attribution.mint_id,
            year_start=coin.attribution.year_start,
            year_end=coin.attribution.year_end,
            grading_state=coin.grading.grading_state.value,
            grade=coin.grading.grade,
            grade_service=coin.grading.service.value if coin.grading.service else None,
            certification_number=coin.grading.certification_number,
            strike_quality=coin.grading.strike,
            surface_quality=coin.grading.surface,
            acquisition_price=coin.acquisition.price if coin.acquisition else None,
            acquisition_currency=coin.acquisition.currency if coin.acquisition else None,
            acquisition_source=coin.acquisition.source if coin.acquisition else None,
            acquisition_date=coin.acquisition.date if coin.acquisition else None,
            acquisition_url=coin.acquisition.url if coin.acquisition else None,
            description=coin.description,
            denomination=coin.denomination,
            portrait_subject=coin.portrait_subject,
            obverse_legend=coin.design.obverse_legend if coin.design else None,
            obverse_description=coin.design.obverse_description if coin.design else None,
            reverse_legend=coin.design.reverse_legend if coin.design else None,
            reverse_description=coin.design.reverse_description if coin.design else None,
            exergue=coin.design.exergue if coin.design else None,
            # Collection management fields
            storage_location=coin.storage_location,
            personal_notes=coin.personal_notes,
            # LLM enrichment fields
            historical_significance=coin.historical_significance
        )