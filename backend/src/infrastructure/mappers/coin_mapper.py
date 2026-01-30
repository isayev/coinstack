import json
from typing import Optional, List, Dict, Any
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal, 
    GradingDetails, AcquisitionDetails, GradingState, GradeService, CoinImage,
    Design, CatalogReference, ProvenanceEntry, IssueStatus, DieInfo, Monogram, FindData, EnrichmentData
)
from src.infrastructure.persistence.orm import CoinModel, CoinImageModel, ProvenanceEventModel, CoinReferenceModel, MonogramModel
from src.infrastructure.services.catalogs.catalog_systems import catalog_to_system, SYSTEM_TO_DISPLAY

class CoinMapper:
    """
    Handles mapping between Domain Entities (Coin) and ORM Models (CoinModel).
    Extracts this logic from the Repository to adhere to SRP.
    """

    @staticmethod
    def _safe_json_load(json_str: Optional[str]) -> Any | None:
        """Safely parse JSON string, returning None on error."""
        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            # Log this error in production
            return None

    @staticmethod
    def to_domain(model: CoinModel) -> Coin:
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
                CoinMapper._reference_to_domain(ref) for ref in model.references
                if ref.reference_type is not None
            ],
            # Map provenance events from ORM to domain value objects
            provenance=[
                CoinMapper._provenance_to_domain(p) for p in model.provenance_events
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
            secondary_treatments=CoinMapper._safe_json_load(model.secondary_treatments),
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
            enrichment=EnrichmentData(
                historical_significance=model.historical_significance,
                enriched_at=model.llm_enriched_at.isoformat() if model.llm_enriched_at else None,
                analysis_sections=CoinMapper._safe_json_load(model.llm_analysis_sections),
                suggested_references=CoinMapper._safe_json_load(model.llm_suggested_references),
                suggested_rarity=CoinMapper._safe_json_load(model.llm_suggested_rarity),
                suggested_design=CoinMapper._safe_json_load(model.llm_suggested_design),
                suggested_attribution=CoinMapper._safe_json_load(model.llm_suggested_attribution),
            ) if (model.historical_significance or model.llm_suggested_references) else None,
        )

    @staticmethod
    def to_model(coin: Coin) -> CoinModel:
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
            historical_significance=coin.enrichment.historical_significance if coin.enrichment else None,
            llm_analysis_sections=json.dumps(coin.enrichment.analysis_sections) if (coin.enrichment and coin.enrichment.analysis_sections) else None,
            llm_suggested_references=json.dumps(coin.enrichment.suggested_references) if (coin.enrichment and coin.enrichment.suggested_references) else None,
            llm_suggested_rarity=json.dumps(coin.enrichment.suggested_rarity) if (coin.enrichment and coin.enrichment.suggested_rarity) else None,
            llm_suggested_design=json.dumps(coin.enrichment.suggested_design) if (coin.enrichment and coin.enrichment.suggested_design) else None,
            llm_suggested_attribution=json.dumps(coin.enrichment.suggested_attribution) if (coin.enrichment and coin.enrichment.suggested_attribution) else None,
            
            # Relationships
            provenance_events=[
                CoinMapper._provenance_to_model(p) for p in coin.provenance
            ]
        )

    @staticmethod
    def _reference_to_domain(model: CoinReferenceModel) -> CatalogReference:
        """
        Map CoinReferenceModel + ReferenceTypeModel to domain CatalogReference.
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
    
    @staticmethod
    def _provenance_to_domain(model: ProvenanceEventModel) -> ProvenanceEntry:
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

    @staticmethod
    def _provenance_to_model(domain: ProvenanceEntry) -> ProvenanceEventModel:
        """Map domain ProvenanceEntry to ProvenanceEventModel."""
        # Logic to split source_name back to specific fields could be complex.
        # For now, we put source_name into the field corresponding to source_type.
        
        auction_house = None
        dealer_name = None
        collection_name = None
        
        if domain.source_type == "auction":
            auction_house = domain.source_name
        elif domain.source_type == "dealer":
            dealer_name = domain.source_name
        elif domain.source_type == "collection":
            collection_name = domain.source_name
        
        return ProvenanceEventModel(
            event_type=domain.source_type,
            event_date=domain.event_date,
            lot_number=domain.lot_number,
            notes=domain.notes,
            auction_house=auction_house,
            dealer_name=dealer_name,
            collection_name=collection_name
        )