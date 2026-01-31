import json
from typing import Optional, List, Dict, Any
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal,
    GradingDetails, AcquisitionDetails, GradingState, GradeService, CoinImage,
    Design, CatalogReference, ProvenanceEntry, IssueStatus, DieInfo, Monogram, FindData, EnrichmentData,
    # Phase 1: Schema V3 value objects
    SecondaryAuthority, CoRuler, PhysicalEnhancements, SecondaryTreatments,
    ToolingRepairs, Centering, DieStudyEnhancements, GradingTPGEnhancements, ChronologyEnhancements
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

            # --- Phase 1: Schema V3 Numismatic Enhancements ---
            # Attribution enhancements
            secondary_authority=SecondaryAuthority(
                name=model.secondary_authority,
                term_id=model.secondary_authority_term_id,
                authority_type=model.authority_type
            ) if (model.secondary_authority or model.secondary_authority_term_id) else None,
            co_ruler=CoRuler(
                name=model.co_ruler,
                term_id=model.co_ruler_term_id,
                portrait_relationship=model.portrait_relationship
            ) if (model.co_ruler or model.co_ruler_term_id) else None,
            moneyer_gens=model.moneyer_gens,

            # Physical enhancements
            physical_enhancements=PhysicalEnhancements(
                weight_standard=model.weight_standard,
                expected_weight_g=model.expected_weight_g,
                flan_shape=model.flan_shape,
                flan_type=model.flan_type,
                flan_notes=model.flan_notes
            ) if any([model.weight_standard, model.expected_weight_g, model.flan_shape, model.flan_type, model.flan_notes]) else None,

            # Secondary treatments - check both boolean flags AND text fields to avoid data loss
            secondary_treatments_v3=SecondaryTreatments(
                is_overstrike=model.is_overstrike or False,
                undertype_visible=model.undertype_visible,
                undertype_attribution=model.undertype_attribution,
                has_test_cut=model.has_test_cut or False,
                test_cut_count=model.test_cut_count,
                test_cut_positions=model.test_cut_positions,
                has_bankers_marks=model.has_bankers_marks or False,
                has_graffiti=model.has_graffiti or False,
                graffiti_description=model.graffiti_description,
                was_mounted=model.was_mounted or False,
                mount_evidence=model.mount_evidence
            ) if any([
                model.is_overstrike, model.has_test_cut, model.has_bankers_marks, model.has_graffiti, model.was_mounted,
                model.undertype_visible, model.undertype_attribution, model.test_cut_positions,
                model.graffiti_description, model.mount_evidence, model.test_cut_count
            ]) else None,

            # Tooling/Repairs
            tooling_repairs=ToolingRepairs(
                tooling_extent=model.tooling_extent,
                tooling_details=model.tooling_details,
                has_ancient_repair=model.has_ancient_repair or False,
                ancient_repairs=model.ancient_repairs
            ) if any([model.tooling_extent, model.tooling_details, model.has_ancient_repair]) else None,

            # Centering
            centering_info=Centering(
                centering=model.centering,
                centering_notes=model.centering_notes
            ) if (model.centering or model.centering_notes) else None,

            # Die study enhancements
            die_study=DieStudyEnhancements(
                obverse_die_state=model.obverse_die_state,
                reverse_die_state=model.reverse_die_state,
                die_break_description=model.die_break_description
            ) if any([model.obverse_die_state, model.reverse_die_state, model.die_break_description]) else None,

            # Grading TPG enhancements
            grading_tpg=GradingTPGEnhancements(
                grade_numeric=model.grade_numeric,
                grade_designation=model.grade_designation,
                has_star_designation=model.has_star_designation or False,
                photo_certificate=model.photo_certificate or False,
                verification_url=model.verification_url
            ) if any([model.grade_numeric, model.grade_designation, model.has_star_designation, model.photo_certificate, model.verification_url]) else None,

            # Chronology enhancements
            chronology=ChronologyEnhancements(
                date_period_notation=model.date_period_notation,
                emission_phase=model.emission_phase
            ) if (model.date_period_notation or model.emission_phase) else None,
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

            # --- Phase 1: Schema V3 Numismatic Enhancements ---
            # Attribution enhancements
            secondary_authority=coin.secondary_authority.name if coin.secondary_authority else None,
            secondary_authority_term_id=coin.secondary_authority.term_id if coin.secondary_authority else None,
            authority_type=coin.secondary_authority.authority_type if coin.secondary_authority else None,
            co_ruler=coin.co_ruler.name if coin.co_ruler else None,
            co_ruler_term_id=coin.co_ruler.term_id if coin.co_ruler else None,
            portrait_relationship=coin.co_ruler.portrait_relationship if coin.co_ruler else None,
            moneyer_gens=coin.moneyer_gens,

            # Physical enhancements
            weight_standard=coin.physical_enhancements.weight_standard if coin.physical_enhancements else None,
            expected_weight_g=coin.physical_enhancements.expected_weight_g if coin.physical_enhancements else None,
            flan_shape=coin.physical_enhancements.flan_shape if coin.physical_enhancements else None,
            flan_type=coin.physical_enhancements.flan_type if coin.physical_enhancements else None,
            flan_notes=coin.physical_enhancements.flan_notes if coin.physical_enhancements else None,

            # Secondary treatments
            is_overstrike=coin.secondary_treatments_v3.is_overstrike if coin.secondary_treatments_v3 else False,
            undertype_visible=coin.secondary_treatments_v3.undertype_visible if coin.secondary_treatments_v3 else None,
            undertype_attribution=coin.secondary_treatments_v3.undertype_attribution if coin.secondary_treatments_v3 else None,
            has_test_cut=coin.secondary_treatments_v3.has_test_cut if coin.secondary_treatments_v3 else False,
            test_cut_count=coin.secondary_treatments_v3.test_cut_count if coin.secondary_treatments_v3 else None,
            test_cut_positions=coin.secondary_treatments_v3.test_cut_positions if coin.secondary_treatments_v3 else None,
            has_bankers_marks=coin.secondary_treatments_v3.has_bankers_marks if coin.secondary_treatments_v3 else False,
            has_graffiti=coin.secondary_treatments_v3.has_graffiti if coin.secondary_treatments_v3 else False,
            graffiti_description=coin.secondary_treatments_v3.graffiti_description if coin.secondary_treatments_v3 else None,
            was_mounted=coin.secondary_treatments_v3.was_mounted if coin.secondary_treatments_v3 else False,
            mount_evidence=coin.secondary_treatments_v3.mount_evidence if coin.secondary_treatments_v3 else None,

            # Tooling/Repairs
            tooling_extent=coin.tooling_repairs.tooling_extent if coin.tooling_repairs else None,
            tooling_details=coin.tooling_repairs.tooling_details if coin.tooling_repairs else None,
            has_ancient_repair=coin.tooling_repairs.has_ancient_repair if coin.tooling_repairs else False,
            ancient_repairs=coin.tooling_repairs.ancient_repairs if coin.tooling_repairs else None,

            # Centering
            centering=coin.centering_info.centering if coin.centering_info else None,
            centering_notes=coin.centering_info.centering_notes if coin.centering_info else None,

            # Die study enhancements
            obverse_die_state=coin.die_study.obverse_die_state if coin.die_study else None,
            reverse_die_state=coin.die_study.reverse_die_state if coin.die_study else None,
            die_break_description=coin.die_study.die_break_description if coin.die_study else None,

            # Grading TPG enhancements
            grade_numeric=coin.grading_tpg.grade_numeric if coin.grading_tpg else None,
            grade_designation=coin.grading_tpg.grade_designation if coin.grading_tpg else None,
            has_star_designation=coin.grading_tpg.has_star_designation if coin.grading_tpg else False,
            photo_certificate=coin.grading_tpg.photo_certificate if coin.grading_tpg else False,
            verification_url=coin.grading_tpg.verification_url if coin.grading_tpg else None,

            # Chronology enhancements
            date_period_notation=coin.chronology.date_period_notation if coin.chronology else None,
            emission_phase=coin.chronology.emission_phase if coin.chronology else None,

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
        """
        Map ProvenanceEventModel to domain ProvenanceEntry.

        V3 schema uses unified source_name field. For backward compatibility
        with legacy data, falls back to auction_house/dealer_name/collection_name.
        """
        from src.domain.coin import ProvenanceEventType, ProvenanceSource

        # V3: Use unified source_name, fall back to legacy fields for migration
        source_name = model.source_name
        if not source_name:
            # Legacy fallback: reconstruct from denormalized fields
            source_name = (
                model.auction_house
                or model.dealer_name
                or model.collection_name
                or ""
            )

        # Parse event_type enum (handle both V2 strings and V3 enum values)
        try:
            event_type = ProvenanceEventType(model.event_type)
        except ValueError:
            event_type = ProvenanceEventType.UNKNOWN

        # Parse source_origin enum (V3 field, default for legacy data)
        try:
            source_origin = ProvenanceSource(model.source_origin) if model.source_origin else ProvenanceSource.MIGRATION
        except ValueError:
            source_origin = ProvenanceSource.MANUAL_ENTRY

        return ProvenanceEntry(
            id=model.id,
            event_type=event_type,
            source_name=source_name,
            event_date=model.event_date,
            date_string=model.date_string,
            sale_name=model.sale_name or model.sale_series,  # V3 field, fall back to legacy
            sale_number=model.sale_number,
            lot_number=model.lot_number,
            catalog_reference=model.catalog_reference,
            hammer_price=model.hammer_price,
            buyers_premium_pct=model.buyers_premium_pct,
            total_price=model.total_price,
            currency=model.currency,
            notes=model.notes,
            url=model.url,
            receipt_available=model.receipt_available or False,
            source_origin=source_origin,
            auction_data_id=model.auction_data_id,
            sort_order=model.sort_order or 0,
            raw_text=""  # Computed on demand via build_raw_text()
        )

    @staticmethod
    def _provenance_to_model(domain: ProvenanceEntry) -> ProvenanceEventModel:
        """
        Map domain ProvenanceEntry to ProvenanceEventModel.

        V3 schema: Direct 1:1 mapping with unified source_name.
        Also populates legacy fields for backward compatibility during migration.
        """
        # Map event_type to legacy fields for backward compat
        auction_house = None
        dealer_name = None
        collection_name = None

        event_type_value = domain.event_type.value if hasattr(domain.event_type, 'value') else str(domain.event_type)

        if event_type_value == "auction":
            auction_house = domain.source_name
        elif event_type_value == "dealer":
            dealer_name = domain.source_name
        elif event_type_value == "collection":
            collection_name = domain.source_name

        return ProvenanceEventModel(
            id=domain.id,
            event_type=event_type_value,
            source_name=domain.source_name,  # V3 unified field
            event_date=domain.event_date,
            date_string=domain.date_string,
            sale_name=domain.sale_name,
            sale_number=domain.sale_number,
            lot_number=domain.lot_number,
            catalog_reference=domain.catalog_reference,
            hammer_price=domain.hammer_price,
            buyers_premium_pct=domain.buyers_premium_pct,
            total_price=domain.total_price,
            currency=domain.currency,
            notes=domain.notes,
            url=domain.url,
            receipt_available=domain.receipt_available,
            source_origin=domain.source_origin.value if hasattr(domain.source_origin, 'value') else str(domain.source_origin),
            auction_data_id=domain.auction_data_id,
            sort_order=domain.sort_order,
            # Legacy fields for backward compat
            auction_house=auction_house,
            dealer_name=dealer_name,
            collection_name=collection_name,
            sale_series=domain.sale_name,  # Legacy alias
        )