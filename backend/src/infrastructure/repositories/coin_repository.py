import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal, 
    GradingDetails, AcquisitionDetails, GradingState, GradeService, CoinImage,
    Design, CatalogReference, ProvenanceEntry, IssueStatus, DieInfo, Monogram, FindData
)
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel, CoinImageModel, ProvenanceEventModel, CoinReferenceModel, MonogramModel
from src.infrastructure.services.catalogs.catalog_systems import catalog_to_system, SYSTEM_TO_DISPLAY

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
        return self._to_domain(merged_coin)

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images),  # Eager load images to prevent N+1 queries
            selectinload(CoinModel.provenance_events),  # Eager load provenance
            selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type),  # Eager load references with their types
            selectinload(CoinModel.monograms) # Eager load monograms
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
        
        return [self._to_domain(c) for c in orm_coins]

    def _apply_filters(self, query, filters: Optional[Dict[str, Any]]):
        """Apply filter conditions to a query."""
        from sqlalchemy import and_, or_, func
        if not filters:
            return query
        
        conditions = []
        
        # Exact match filters
        if "category" in filters:
            # Case insensitive category match since backend uses slugs/values inconsistently
            conditions.append(func.lower(CoinModel.category) == filters["category"].lower())
        
        if "metal" in filters:
            conditions.append(func.lower(CoinModel.metal) == filters["metal"].lower())
        
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
                die_axis=model.die_axis,
                specific_gravity=model.specific_gravity
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
            
            # --- Research Grade Extensions ---
            issue_status=IssueStatus(model.issue_status) if model.issue_status else IssueStatus.OFFICIAL,
            die_info=DieInfo(
                obverse_die_id=model.obverse_die_id,
                reverse_die_id=model.reverse_die_id
            ) if (model.obverse_die_id or model.reverse_die_id) else None,
            monograms=[
                Monogram(id=m.id, label=m.label, image_url=m.image_url, vector_data=m.vector_data)
                for m in model.monograms
            ] if model.monograms else [],
            secondary_treatments=json.loads(model.secondary_treatments) if model.secondary_treatments else None,
            find_data=FindData(
                find_spot=model.find_spot,
                find_date=model.find_date
            ) if (model.find_spot or model.find_date) else None,

            # Collection management fields
            storage_location=model.storage_location,
            personal_notes=model.personal_notes,
            # Rarity
            rarity=model.rarity,
            rarity_notes=model.rarity_notes,
            # LLM enrichment fields
            historical_significance=model.historical_significance,
            llm_enriched_at=model.llm_enriched_at.isoformat() if model.llm_enriched_at else None,
            llm_analysis_sections=model.llm_analysis_sections,
            llm_suggested_references=json.loads(model.llm_suggested_references) if model.llm_suggested_references else None,
            llm_suggested_rarity=json.loads(model.llm_suggested_rarity) if model.llm_suggested_rarity else None,
            llm_suggested_design=json.loads(model.llm_suggested_design) if model.llm_suggested_design else None,
            llm_suggested_attribution=json.loads(model.llm_suggested_attribution) if model.llm_suggested_attribution else None,
        )
    
    def _reference_to_domain(self, model: CoinReferenceModel) -> CatalogReference:
        """
        Map CoinReferenceModel + ReferenceTypeModel to domain CatalogReference.

        Mapping: ReferenceTypeModel.system -> catalog (uppercase); volume, number, local_ref -> raw_text;
        CoinReferenceModel.is_primary, notes, source -> domain. suffix not stored in V1 schema (None).
        """
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
        # Use display catalog (e.g. RRC for crawford) for API consistency
        catalog_display = SYSTEM_TO_DISPLAY.get(ref_type.system) or ref_type.system.upper()
        
        return CatalogReference(
            catalog=catalog_display,
            number=ref_type.number or "",
            volume=ref_type.volume,
            suffix=None,  # Not stored in V1 schema
            raw_text=raw_text,
            is_primary=model.is_primary or False,
            notes=model.notes,
            source=model.source,
            variant=getattr(ref_type, "variant", None),
            mint=getattr(ref_type, "mint", None),
            supplement=getattr(ref_type, "supplement", None),
            collection=getattr(ref_type, "collection", None),
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
            specific_gravity=coin.dimensions.specific_gravity,
            
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
            
            # --- Research Grade Extensions ---
            issue_status=coin.issue_status.value,
            obverse_die_id=coin.die_info.obverse_die_id if coin.die_info else None,
            reverse_die_id=coin.die_info.reverse_die_id if coin.die_info else None,
            secondary_treatments=json.dumps(coin.secondary_treatments) if coin.secondary_treatments else None,
            find_spot=coin.find_data.find_spot if coin.find_data else None,
            find_date=coin.find_data.find_date if coin.find_data else None,
            
            # Collection management fields
            storage_location=coin.storage_location,
            personal_notes=coin.personal_notes,
            # Rarity
            rarity=coin.rarity,
            rarity_notes=coin.rarity_notes,
            # LLM enrichment fields
            historical_significance=coin.historical_significance,
            llm_suggested_references=json.dumps(coin.llm_suggested_references) if coin.llm_suggested_references else None,
            llm_suggested_rarity=json.dumps(coin.llm_suggested_rarity) if coin.llm_suggested_rarity else None,
            llm_suggested_design=json.dumps(coin.llm_suggested_design) if coin.llm_suggested_design else None,
            llm_suggested_attribution=json.dumps(coin.llm_suggested_attribution) if coin.llm_suggested_attribution else None,
        )