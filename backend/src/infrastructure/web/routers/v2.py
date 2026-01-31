from fastapi import APIRouter, Depends, status, Query, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import date
from src.domain.repositories import ICoinRepository
from src.application.commands.create_coin import (
    CreateCoinUseCase, CreateCoinDTO, ImageDTO, DesignDTO,
    # Phase 1: Schema V3 DTOs
    SecondaryAuthorityDTO, CoRulerDTO, PhysicalEnhancementsDTO, SecondaryTreatmentsV3DTO,
    ToolingRepairsDTO, CenteringDTO, DieStudyEnhancementsDTO, GradingTPGEnhancementsDTO, ChronologyEnhancementsDTO
)
from src.application.services.grade_normalizer import normalize_grade_for_storage
from src.domain.coin import (
    Coin, Dimensions, Attribution, GradingDetails, AcquisitionDetails,
    Category, Metal, GradingState, GradeService, IssueStatus, DieInfo, FindData, Design, ProvenanceEntry, ProvenanceEventType,
    # Phase 1: Schema V3 value objects
    SecondaryAuthority, CoRuler, PhysicalEnhancements, SecondaryTreatments,
    ToolingRepairs, Centering, DieStudyEnhancements, GradingTPGEnhancements, ChronologyEnhancements
)
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.infrastructure.web.dependencies import get_coin_repo, get_db

router = APIRouter(prefix="/api/v2/coins", tags=["coins"])

# --- Request/Response Models ---
class ImageRequest(BaseModel):
    url: str
    image_type: str
    is_primary: bool = False

class DesignRequest(BaseModel):
    obverse_legend: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_description: Optional[str] = None
    exergue: Optional[str] = None


class CatalogReferenceInput(BaseModel):
    """Input for a single catalog reference (create/update)."""
    catalog: str
    number: str
    volume: Optional[str] = None
    suffix: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None
    raw_text: Optional[str] = None
    variant: Optional[str] = None   # e.g. "a", "b" (RIC, Crawford)
    mint: Optional[str] = None     # RIC mint code
    supplement: Optional[str] = None  # RPC S, S2
    collection: Optional[str] = None  # SNG collection


class ProvenanceEntryRequest(BaseModel):
    """Request to create/update a provenance entry nested in coin update."""
    id: Optional[int] = None
    event_type: str
    source_name: str
    event_date: Optional[date] = None
    date_string: Optional[str] = None
    lot_number: Optional[str] = None
    hammer_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    sort_order: int = 0


# --- Phase 1: Schema V3 Input Models ---

class SecondaryAuthorityRequest(BaseModel):
    name: Optional[str] = None
    term_id: Optional[int] = None
    authority_type: Optional[str] = None  # magistrate, satrap, dynast, etc.


class CoRulerRequest(BaseModel):
    name: Optional[str] = None
    term_id: Optional[int] = None
    portrait_relationship: Optional[str] = None  # self, consort, heir, etc.


class PhysicalEnhancementsRequest(BaseModel):
    weight_standard: Optional[str] = None  # attic, aeginetan, etc.
    expected_weight_g: Optional[Decimal] = None
    flan_shape: Optional[str] = None  # round, irregular, scyphate
    flan_type: Optional[str] = None  # cast, struck, hammered
    flan_notes: Optional[str] = None


class SecondaryTreatmentsV3Request(BaseModel):
    is_overstrike: bool = False
    undertype_visible: Optional[str] = None
    undertype_attribution: Optional[str] = None
    has_test_cut: bool = False
    test_cut_count: Optional[int] = None
    test_cut_positions: Optional[str] = None
    has_bankers_marks: bool = False
    has_graffiti: bool = False
    graffiti_description: Optional[str] = None
    was_mounted: bool = False
    mount_evidence: Optional[str] = None


class ToolingRepairsRequest(BaseModel):
    tooling_extent: Optional[str] = None  # none, minor, moderate, significant, extensive
    tooling_details: Optional[str] = None
    has_ancient_repair: bool = False
    ancient_repairs: Optional[str] = None


class CenteringRequest(BaseModel):
    centering: Optional[str] = None  # well-centered, slightly_off, off_center
    centering_notes: Optional[str] = None


class DieStudyEnhancementsRequest(BaseModel):
    obverse_die_state: Optional[str] = None  # fresh, early, middle, late, worn, broken
    reverse_die_state: Optional[str] = None
    die_break_description: Optional[str] = None


class GradingTPGEnhancementsRequest(BaseModel):
    grade_numeric: Optional[int] = None  # NGC/PCGS numeric grades
    grade_designation: Optional[str] = None  # Fine Style, Choice, Gem
    has_star_designation: bool = False
    photo_certificate: bool = False
    verification_url: Optional[str] = None


class ChronologyEnhancementsRequest(BaseModel):
    date_period_notation: Optional[str] = None  # "c. 150-100 BC"
    emission_phase: Optional[str] = None  # First Issue, Second Issue


class CreateCoinRequest(BaseModel):
    category: str
    metal: str
    weight_g: Optional[Decimal] = None
    diameter_mm: Decimal
    issuer: str
    grading_state: str
    grade: str
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    die_axis: Optional[int] = None
    grade_service: Optional[str] = None
    certification: Optional[str] = None
    strike: Optional[str] = None
    surface: Optional[str] = None
    acquisition_price: Optional[Decimal] = None
    acquisition_source: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_url: Optional[str] = None
    images: List[ImageRequest] = []
    # Attribution extensions: issuer = ruling authority; portrait_subject = person/deity on obverse (may differ)
    denomination: Optional[str] = None
    portrait_subject: Optional[str] = None
    # Design
    design: Optional[DesignRequest] = None
    # Collection management
    storage_location: Optional[str] = None
    personal_notes: Optional[str] = None
    
    # Rarity
    rarity: Optional[str] = None
    rarity_notes: Optional[str] = None
    
    # Research Grade Extensions
    specific_gravity: Optional[Decimal] = None
    issue_status: str = "official"
    obverse_die_id: Optional[str] = None
    reverse_die_id: Optional[str] = None
    find_spot: Optional[str] = None
    find_date: Optional[date] = None
    # None = omit/not provided (create: no refs; update: preserve existing). [] = clear on update; [x,y] = set.
    references: Optional[List[CatalogReferenceInput]] = None
    provenance: Optional[List[ProvenanceEntryRequest]] = None
    # Note: secondary_treatments and monograms not yet supported in simple CREATE
    # They should be added via specific endpoints or future updates

    # --- Phase 1: Schema V3 Numismatic Enhancements ---
    secondary_authority: Optional[SecondaryAuthorityRequest] = None
    co_ruler: Optional[CoRulerRequest] = None
    moneyer_gens: Optional[str] = None
    physical_enhancements: Optional[PhysicalEnhancementsRequest] = None
    secondary_treatments_v3: Optional[SecondaryTreatmentsV3Request] = None
    tooling_repairs: Optional[ToolingRepairsRequest] = None
    centering_info: Optional[CenteringRequest] = None
    die_study: Optional[DieStudyEnhancementsRequest] = None
    grading_tpg: Optional[GradingTPGEnhancementsRequest] = None
    chronology: Optional[ChronologyEnhancementsRequest] = None

class DimensionsResponse(BaseModel):
    weight_g: Optional[Decimal] = None
    diameter_mm: Decimal
    die_axis: Optional[int] = None
    specific_gravity: Optional[Decimal] = None

class AttributionResponse(BaseModel):
    issuer: str
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None

class GradingResponse(BaseModel):
    grading_state: str
    grade: str
    service: Optional[str] = None
    certification_number: Optional[str] = None
    strike: Optional[str] = None
    surface: Optional[str] = None

class AcquisitionResponse(BaseModel):
    price: Decimal
    currency: str
    source: str
    date: Optional[date] = None
    url: Optional[str] = None

class ImageResponse(BaseModel):
    url: str
    image_type: str
    is_primary: bool

class DesignResponse(BaseModel):
    obverse_legend: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_description: Optional[str] = None
    exergue: Optional[str] = None

class CatalogReferenceResponse(BaseModel):
    catalog: str
    number: str
    volume: Optional[str] = None
    suffix: Optional[str] = None
    raw_text: str = ""
    source: Optional[str] = None
    variant: Optional[str] = None
    mint: Optional[str] = None
    supplement: Optional[str] = None
    collection: Optional[str] = None

class ProvenanceEntryResponse(BaseModel):
    id: Optional[int] = None
    event_type: str
    source_name: str
    event_date: Optional[date] = None
    date_string: Optional[str] = None
    lot_number: Optional[str] = None
    notes: Optional[str] = None
    raw_text: str = ""
    hammer_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    currency: Optional[str] = None
    url: Optional[str] = None
    sort_order: int = 0

class DieInfoResponse(BaseModel):
    obverse_die_id: Optional[str] = None
    reverse_die_id: Optional[str] = None

class MonogramResponse(BaseModel):
    id: Optional[int]
    label: str
    image_url: Optional[str] = None
    vector_data: Optional[str] = None

class FindDataResponse(BaseModel):
    find_spot: Optional[str] = None
    find_date: Optional[date] = None


# --- Phase 1: Schema V3 Response Models ---

class SecondaryAuthorityResponse(BaseModel):
    name: Optional[str] = None
    term_id: Optional[int] = None
    authority_type: Optional[str] = None


class CoRulerResponse(BaseModel):
    name: Optional[str] = None
    term_id: Optional[int] = None
    portrait_relationship: Optional[str] = None


class PhysicalEnhancementsResponse(BaseModel):
    weight_standard: Optional[str] = None
    expected_weight_g: Optional[Decimal] = None
    flan_shape: Optional[str] = None
    flan_type: Optional[str] = None
    flan_notes: Optional[str] = None


class SecondaryTreatmentsV3Response(BaseModel):
    is_overstrike: bool = False
    undertype_visible: Optional[str] = None
    undertype_attribution: Optional[str] = None
    has_test_cut: bool = False
    test_cut_count: Optional[int] = None
    test_cut_positions: Optional[str] = None
    has_bankers_marks: bool = False
    has_graffiti: bool = False
    graffiti_description: Optional[str] = None
    was_mounted: bool = False
    mount_evidence: Optional[str] = None


class ToolingRepairsResponse(BaseModel):
    tooling_extent: Optional[str] = None
    tooling_details: Optional[str] = None
    has_ancient_repair: bool = False
    ancient_repairs: Optional[str] = None


class CenteringResponse(BaseModel):
    centering: Optional[str] = None
    centering_notes: Optional[str] = None


class DieStudyEnhancementsResponse(BaseModel):
    obverse_die_state: Optional[str] = None
    reverse_die_state: Optional[str] = None
    die_break_description: Optional[str] = None


class GradingTPGEnhancementsResponse(BaseModel):
    grade_numeric: Optional[int] = None
    grade_designation: Optional[str] = None
    has_star_designation: bool = False
    photo_certificate: bool = False
    verification_url: Optional[str] = None


class ChronologyEnhancementsResponse(BaseModel):
    date_period_notation: Optional[str] = None
    emission_phase: Optional[str] = None


class CoinResponse(BaseModel):
    id: Optional[int]
    category: str
    metal: str
    dimensions: DimensionsResponse
    attribution: AttributionResponse
    grading: GradingResponse
    acquisition: Optional[AcquisitionResponse] = None
    images: List[ImageResponse] = []
    # New fields
    description: Optional[str] = None
    denomination: Optional[str] = None
    portrait_subject: Optional[str] = None
    design: Optional[DesignResponse] = None
    references: List[CatalogReferenceResponse] = []
    provenance: List[ProvenanceEntryResponse] = []
    # Collection management
    storage_location: Optional[str] = None
    personal_notes: Optional[str] = None
    # Rarity (numismatic)
    rarity: Optional[str] = None
    rarity_notes: Optional[str] = None
    # LLM enrichment
    historical_significance: Optional[str] = None
    llm_enriched_at: Optional[str] = None
    llm_analysis_sections: Optional[Dict[str, Any]] = None      # JSON-encoded sections
    llm_suggested_references: Optional[List[str]] = None  # Citations found by LLM for audit
    llm_suggested_rarity: Optional[dict] = None      # Rarity info from LLM for audit
    llm_suggested_design: Optional[dict] = None     # Design suggestions: obverse_legend, reverse_legend, exergue, obverse_description, reverse_description, *_expanded
    llm_suggested_attribution: Optional[dict] = None  # Attribution suggestions: issuer, mint, denomination, year_start, year_end

    # Research Grade Extensions
    issue_status: str
    die_info: Optional[DieInfoResponse] = None
    monograms: List[MonogramResponse] = []
    secondary_treatments: Optional[List[Dict[str, Any]]] = None
    find_data: Optional[FindDataResponse] = None
    
    # Navigation helpers
    prev_id: Optional[int] = None
    next_id: Optional[int] = None

    # --- Phase 1: Schema V3 Numismatic Enhancements ---
    secondary_authority: Optional[SecondaryAuthorityResponse] = None
    co_ruler: Optional[CoRulerResponse] = None
    moneyer_gens: Optional[str] = None
    physical_enhancements: Optional[PhysicalEnhancementsResponse] = None
    secondary_treatments_v3: Optional[SecondaryTreatmentsV3Response] = None
    tooling_repairs: Optional[ToolingRepairsResponse] = None
    centering_info: Optional[CenteringResponse] = None
    die_study: Optional[DieStudyEnhancementsResponse] = None
    grading_tpg: Optional[GradingTPGEnhancementsResponse] = None
    chronology: Optional[ChronologyEnhancementsResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def from_domain(coin: Coin) -> "CoinResponse":
        return CoinResponse(
            id=coin.id,
            category=coin.category.value,
            metal=coin.metal.value,
            dimensions=DimensionsResponse(
                weight_g=coin.dimensions.weight_g,
                diameter_mm=coin.dimensions.diameter_mm,
                die_axis=coin.dimensions.die_axis,
                specific_gravity=coin.dimensions.specific_gravity
            ),
            attribution=AttributionResponse(
                issuer=coin.attribution.issuer,
                mint=coin.attribution.mint,
                year_start=coin.attribution.year_start,
                year_end=coin.attribution.year_end
            ),
            grading=GradingResponse(
                grading_state=coin.grading.grading_state.value,
                grade=coin.grading.grade,
                service=coin.grading.service.value if coin.grading.service else None,
                certification_number=coin.grading.certification_number,
                strike=coin.grading.strike,
                surface=coin.grading.surface
            ),
            acquisition=AcquisitionResponse(
                price=coin.acquisition.price,
                currency=coin.acquisition.currency,
                source=coin.acquisition.source,
                date=coin.acquisition.date,
                url=coin.acquisition.url
            ) if coin.acquisition else None,
            images=[
                ImageResponse(
                    url=img.url,
                    image_type=img.image_type,
                    is_primary=img.is_primary
                ) for img in coin.images
            ],
            description=coin.description,
            denomination=coin.denomination,
            portrait_subject=coin.portrait_subject,
            design=DesignResponse(
                obverse_legend=coin.design.obverse_legend,
                obverse_description=coin.design.obverse_description,
                reverse_legend=coin.design.reverse_legend,
                reverse_description=coin.design.reverse_description,
                exergue=coin.design.exergue
            ) if coin.design else None,
            references=[
                CatalogReferenceResponse(
                    catalog=ref.catalog,
                    number=ref.number,
                    volume=ref.volume,
                    suffix=ref.suffix,
                    raw_text=ref.raw_text,
                    source=getattr(ref, "source", None),
                    variant=getattr(ref, "variant", None),
                    mint=getattr(ref, "mint", None),
                    supplement=getattr(ref, "supplement", None),
                    collection=getattr(ref, "collection", None),
                ) for ref in coin.references
            ],
            provenance=[
                ProvenanceEntryResponse(
                    id=p.id,
                    event_type=p.event_type.value if hasattr(p.event_type, 'value') else p.event_type,
                    source_name=p.source_name,
                    event_date=p.event_date,
                    date_string=p.date_string,
                    lot_number=p.lot_number,
                    notes=p.notes,
                    raw_text=p.raw_text,
                    hammer_price=p.hammer_price,
                    total_price=p.total_price,
                    currency=p.currency,
                    url=p.url,
                    sort_order=p.sort_order
                ) for p in coin.provenance
            ],
            storage_location=coin.storage_location,
            personal_notes=coin.personal_notes,
            rarity=coin.rarity,
            rarity_notes=coin.rarity_notes,
            historical_significance=coin.enrichment.historical_significance if coin.enrichment else None,
            llm_enriched_at=coin.enrichment.enriched_at if coin.enrichment else None,
            llm_analysis_sections=coin.enrichment.analysis_sections if coin.enrichment else None,
            llm_suggested_references=coin.enrichment.suggested_references if coin.enrichment else None,
            llm_suggested_rarity=coin.enrichment.suggested_rarity if coin.enrichment else None,
            llm_suggested_design=coin.enrichment.suggested_design if coin.enrichment else None,
            llm_suggested_attribution=coin.enrichment.suggested_attribution if coin.enrichment else None,

            # Extensions mapping
            issue_status=coin.issue_status.value,
            die_info=DieInfoResponse(
                obverse_die_id=coin.die_info.obverse_die_id,
                reverse_die_id=coin.die_info.reverse_die_id
            ) if coin.die_info else None,
            monograms=[
                MonogramResponse(
                    id=m.id,
                    label=m.label,
                    image_url=m.image_url,
                    vector_data=m.vector_data
                ) for m in coin.monograms
            ],
            secondary_treatments=coin.secondary_treatments,
            find_data=FindDataResponse(
                find_spot=coin.find_data.find_spot,
                find_date=coin.find_data.find_date
            ) if coin.find_data else None,

            # --- Phase 1: Schema V3 Numismatic Enhancements ---
            secondary_authority=SecondaryAuthorityResponse(
                name=coin.secondary_authority.name,
                term_id=coin.secondary_authority.term_id,
                authority_type=coin.secondary_authority.authority_type
            ) if coin.secondary_authority else None,
            co_ruler=CoRulerResponse(
                name=coin.co_ruler.name,
                term_id=coin.co_ruler.term_id,
                portrait_relationship=coin.co_ruler.portrait_relationship
            ) if coin.co_ruler else None,
            moneyer_gens=coin.moneyer_gens,
            physical_enhancements=PhysicalEnhancementsResponse(
                weight_standard=coin.physical_enhancements.weight_standard,
                expected_weight_g=coin.physical_enhancements.expected_weight_g,
                flan_shape=coin.physical_enhancements.flan_shape,
                flan_type=coin.physical_enhancements.flan_type,
                flan_notes=coin.physical_enhancements.flan_notes
            ) if coin.physical_enhancements else None,
            secondary_treatments_v3=SecondaryTreatmentsV3Response(
                is_overstrike=coin.secondary_treatments_v3.is_overstrike,
                undertype_visible=coin.secondary_treatments_v3.undertype_visible,
                undertype_attribution=coin.secondary_treatments_v3.undertype_attribution,
                has_test_cut=coin.secondary_treatments_v3.has_test_cut,
                test_cut_count=coin.secondary_treatments_v3.test_cut_count,
                test_cut_positions=coin.secondary_treatments_v3.test_cut_positions,
                has_bankers_marks=coin.secondary_treatments_v3.has_bankers_marks,
                has_graffiti=coin.secondary_treatments_v3.has_graffiti,
                graffiti_description=coin.secondary_treatments_v3.graffiti_description,
                was_mounted=coin.secondary_treatments_v3.was_mounted,
                mount_evidence=coin.secondary_treatments_v3.mount_evidence
            ) if coin.secondary_treatments_v3 else None,
            tooling_repairs=ToolingRepairsResponse(
                tooling_extent=coin.tooling_repairs.tooling_extent,
                tooling_details=coin.tooling_repairs.tooling_details,
                has_ancient_repair=coin.tooling_repairs.has_ancient_repair,
                ancient_repairs=coin.tooling_repairs.ancient_repairs
            ) if coin.tooling_repairs else None,
            centering_info=CenteringResponse(
                centering=coin.centering_info.centering,
                centering_notes=coin.centering_info.centering_notes
            ) if coin.centering_info else None,
            die_study=DieStudyEnhancementsResponse(
                obverse_die_state=coin.die_study.obverse_die_state,
                reverse_die_state=coin.die_study.reverse_die_state,
                die_break_description=coin.die_study.die_break_description
            ) if coin.die_study else None,
            grading_tpg=GradingTPGEnhancementsResponse(
                grade_numeric=coin.grading_tpg.grade_numeric,
                grade_designation=coin.grading_tpg.grade_designation,
                has_star_designation=coin.grading_tpg.has_star_designation,
                photo_certificate=coin.grading_tpg.photo_certificate,
                verification_url=coin.grading_tpg.verification_url
            ) if coin.grading_tpg else None,
            chronology=ChronologyEnhancementsResponse(
                date_period_notation=coin.chronology.date_period_notation,
                emission_phase=coin.chronology.emission_phase
            ) if coin.chronology else None,
        )

@router.post("", status_code=status.HTTP_201_CREATED)
def create_coin(
    request: CreateCoinRequest,
    repo: ICoinRepository = Depends(get_coin_repo),
    db: Session = Depends(get_db),
):
    use_case = CreateCoinUseCase(repo)
    
    grade = normalize_grade_for_storage(request.grade) or "Unknown"
    
    # Map sub-objects
    images_dto = [
        ImageDTO(url=img.url, image_type=img.image_type, is_primary=img.is_primary)
        for img in request.images
    ]
    
    design_dto = None
    if request.design:
        design_dto = DesignDTO(
            obverse_legend=request.design.obverse_legend,
            obverse_description=request.design.obverse_description,
            reverse_legend=request.design.reverse_legend,
            reverse_description=request.design.reverse_description,
            exergue=request.design.exergue
        )

    # Map Phase 1 fields to DTOs
    secondary_authority_dto = SecondaryAuthorityDTO(
        name=request.secondary_authority.name,
        term_id=request.secondary_authority.term_id,
        authority_type=request.secondary_authority.authority_type
    ) if request.secondary_authority else None

    co_ruler_dto = CoRulerDTO(
        name=request.co_ruler.name,
        term_id=request.co_ruler.term_id,
        portrait_relationship=request.co_ruler.portrait_relationship
    ) if request.co_ruler else None

    physical_enhancements_dto = PhysicalEnhancementsDTO(
        weight_standard=request.physical_enhancements.weight_standard,
        expected_weight_g=request.physical_enhancements.expected_weight_g,
        flan_shape=request.physical_enhancements.flan_shape,
        flan_type=request.physical_enhancements.flan_type,
        flan_notes=request.physical_enhancements.flan_notes
    ) if request.physical_enhancements else None

    secondary_treatments_v3_dto = SecondaryTreatmentsV3DTO(
        is_overstrike=request.secondary_treatments_v3.is_overstrike,
        undertype_visible=request.secondary_treatments_v3.undertype_visible,
        undertype_attribution=request.secondary_treatments_v3.undertype_attribution,
        has_test_cut=request.secondary_treatments_v3.has_test_cut,
        test_cut_count=request.secondary_treatments_v3.test_cut_count,
        test_cut_positions=request.secondary_treatments_v3.test_cut_positions,
        has_bankers_marks=request.secondary_treatments_v3.has_bankers_marks,
        has_graffiti=request.secondary_treatments_v3.has_graffiti,
        graffiti_description=request.secondary_treatments_v3.graffiti_description,
        was_mounted=request.secondary_treatments_v3.was_mounted,
        mount_evidence=request.secondary_treatments_v3.mount_evidence
    ) if request.secondary_treatments_v3 else None

    tooling_repairs_dto = ToolingRepairsDTO(
        tooling_extent=request.tooling_repairs.tooling_extent,
        tooling_details=request.tooling_repairs.tooling_details,
        has_ancient_repair=request.tooling_repairs.has_ancient_repair,
        ancient_repairs=request.tooling_repairs.ancient_repairs
    ) if request.tooling_repairs else None

    centering_info_dto = CenteringDTO(
        centering=request.centering_info.centering,
        centering_notes=request.centering_info.centering_notes
    ) if request.centering_info else None

    die_study_dto = DieStudyEnhancementsDTO(
        obverse_die_state=request.die_study.obverse_die_state,
        reverse_die_state=request.die_study.reverse_die_state,
        die_break_description=request.die_study.die_break_description
    ) if request.die_study else None

    grading_tpg_dto = GradingTPGEnhancementsDTO(
        grade_numeric=request.grading_tpg.grade_numeric,
        grade_designation=request.grading_tpg.grade_designation,
        has_star_designation=request.grading_tpg.has_star_designation,
        photo_certificate=request.grading_tpg.photo_certificate,
        verification_url=request.grading_tpg.verification_url
    ) if request.grading_tpg else None

    chronology_dto = ChronologyEnhancementsDTO(
        date_period_notation=request.chronology.date_period_notation,
        emission_phase=request.chronology.emission_phase
    ) if request.chronology else None

    dto = CreateCoinDTO(
        category=request.category,
        metal=request.metal,
        weight_g=request.weight_g,
        diameter_mm=request.diameter_mm,
        issuer=request.issuer,
        grading_state=request.grading_state,
        grade=grade,
        mint=request.mint,
        year_start=request.year_start,
        year_end=request.year_end,
        die_axis=request.die_axis,
        grade_service=request.grade_service,
        certification=request.certification,
        acquisition_price=request.acquisition_price,
        acquisition_source=request.acquisition_source,
        acquisition_date=request.acquisition_date,
        acquisition_url=request.acquisition_url,

        # Extensions
        specific_gravity=request.specific_gravity,
        issue_status=request.issue_status,
        obverse_die_id=request.obverse_die_id,
        reverse_die_id=request.reverse_die_id,
        find_spot=request.find_spot,
        find_date=request.find_date,

        # New Fields
        denomination=request.denomination,
        portrait_subject=request.portrait_subject,
        images=images_dto,
        design=design_dto,

        # Collection management
        storage_location=request.storage_location,
        personal_notes=request.personal_notes,

        # Rarity
        rarity=request.rarity,
        rarity_notes=request.rarity_notes,

        # Phase 1: Schema V3 Numismatic Enhancements
        secondary_authority=secondary_authority_dto,
        co_ruler=co_ruler_dto,
        moneyer_gens=request.moneyer_gens,
        physical_enhancements=physical_enhancements_dto,
        secondary_treatments_v3=secondary_treatments_v3_dto,
        tooling_repairs=tooling_repairs_dto,
        centering_info=centering_info_dto,
        die_study=die_study_dto,
        grading_tpg=grading_tpg_dto,
        chronology=chronology_dto,
    )
    
    saved_coin = use_case.execute(dto)

    if request.references is not None and saved_coin.id:
        from src.application.services.reference_sync import sync_coin_references
        # Skip refs with no catalog or number to avoid persisting "Unknown" / empty rows
        valid_refs = [
            r.model_dump() for r in request.references
            if (r.catalog and r.catalog.strip()) and (r.number and r.number.strip())
        ]
        sync_coin_references(db, saved_coin.id, valid_refs, "user")
        saved_coin = repo.get_by_id(saved_coin.id) or saved_coin

    return CoinResponse.from_domain(saved_coin)

class PaginatedResponse(BaseModel):
    items: List[CoinResponse]
    total: int
    page: int
    per_page: int
    pages: int

@router.get("", response_model=PaginatedResponse)
def get_coins(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=1000),
    sort_by: Optional[str] = Query(None),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    ids: Optional[str] = Query(None, description="Comma-separated list of coin IDs to fetch"),
    # Filter parameters
    category: Optional[str] = Query(None, description="Filter by category (e.g., roman_imperial, greek)"),
    metal: Optional[str] = Query(None, description="Filter by metal (e.g., gold, silver, bronze)"),
    denomination: Optional[str] = Query(None, description="Filter by denomination (e.g., denarius, aureus)"),
    grading_state: Optional[str] = Query(None, description="Filter by grading state (raw, slabbed)"),
    grade_service: Optional[str] = Query(None, description="Filter by grading service (ngc, pcgs)"),
    issuer: Optional[str] = Query(None, description="Filter by issuer name (partial match)"),
    year_start: Optional[int] = Query(None, description="Filter by minimum year (negative for BC)"),
    year_end: Optional[int] = Query(None, description="Filter by maximum year (negative for BC)"),
    mint_year_gte: Optional[int] = Query(None, description="Alias for year_start (frontend param)"),
    mint_year_lte: Optional[int] = Query(None, description="Alias for year_end (frontend param)"),
    weight_min: Optional[float] = Query(None, description="Filter by minimum weight in grams"),
    weight_max: Optional[float] = Query(None, description="Filter by maximum weight in grams"),
    # Added filters
    grade: Optional[str] = Query(None, description="Filter by grade (e.g., XF, VF, or tier like 'fine')"),
    rarity: Optional[str] = Query(None, description="Filter by rarity (e.g., R1, Common)"),
    repo: ICoinRepository = Depends(get_coin_repo)
):
    """
    Get paginated list of coins with optional filtering.
    
    Filters can be combined. All filters use AND logic.
    If `ids` parameter is provided, returns only those coins (ignores pagination).
    """
    # Handle ids parameter - fetch specific coins (batch query, O(1) instead of O(N))
    if ids:
        try:
            coin_ids = [int(id_str.strip()) for id_str in ids.split(",") if id_str.strip()]
            if coin_ids:
                coins = repo.get_by_ids(coin_ids)
                return PaginatedResponse(
                    items=[CoinResponse.from_domain(c) for c in coins],
                    total=len(coins),
                    page=1,
                    per_page=len(coins),
                    pages=1
                )
        except ValueError:
            # Invalid ids format, fall through to normal query
            pass
    
    skip = (page - 1) * per_page
    
    # Build filters dict
    filters = {}
    if category:
        filters["category"] = category
    if metal:
        filters["metal"] = metal
    if denomination:
        filters["denomination"] = denomination
    if grading_state:
        filters["grading_state"] = grading_state
    if grade_service:
        filters["grade_service"] = grade_service
    if issuer:
        filters["issuer"] = issuer
    if year_start is not None:
        filters["year_start"] = year_start
    if year_end is not None:
        filters["year_end"] = year_end
    if mint_year_gte is not None and "year_start" not in filters:
        filters["year_start"] = mint_year_gte
    if mint_year_lte is not None and "year_end" not in filters:
        filters["year_end"] = mint_year_lte
    if weight_min is not None:
        filters["weight_min"] = weight_min
    if weight_max is not None:
        filters["weight_max"] = weight_max
    if grade:
        filters["grade"] = grade
    if rarity:
        filters["rarity"] = rarity
    
    # Pass filters to repository
    coins = repo.get_all(
        skip=skip, 
        limit=per_page, 
        sort_by=sort_by, 
        sort_dir=sort_dir,
        filters=filters if filters else None
    )
    total = repo.count(filters=filters if filters else None)
    pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        items=[CoinResponse.from_domain(c) for c in coins],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )

def _get_neighbor_ids(db: Session, coin_id: int) -> tuple[Optional[int], Optional[int]]:
    """
    Get previous and next coin IDs for navigation.

    Uses efficient SQL queries to find neighbors without loading all coins.
    Returns (prev_id, next_id) tuple.

    Args:
        db: Injected SQLAlchemy session (avoids creating new connection)
        coin_id: Current coin ID to find neighbors for
    """
    # Get previous ID (largest ID less than current)
    prev_result = db.execute(
        text("SELECT id FROM coins_v2 WHERE id < :coin_id ORDER BY id DESC LIMIT 1"),
        {"coin_id": coin_id}
    ).fetchone()
    prev_id = prev_result[0] if prev_result else None

    # Get next ID (smallest ID greater than current)
    next_result = db.execute(
        text("SELECT id FROM coins_v2 WHERE id > :coin_id ORDER BY id ASC LIMIT 1"),
        {"coin_id": coin_id}
    ).fetchone()
    next_id = next_result[0] if next_result else None

    return prev_id, next_id


@router.get("/{coin_id}", response_model=CoinResponse)
def get_coin(
    coin_id: int,
    repo: ICoinRepository = Depends(get_coin_repo),
    db: Session = Depends(get_db)
):
    coin = repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")

    # Calculate neighbor IDs for navigation (uses injected session)
    prev_id, next_id = _get_neighbor_ids(db, coin_id)

    response = CoinResponse.from_domain(coin)
    response.prev_id = prev_id
    response.next_id = next_id
    return response

@router.put("/{coin_id}", response_model=CoinResponse)
def update_coin(
    coin_id: int,
    request: CreateCoinRequest,
    repo: ICoinRepository = Depends(get_coin_repo),
    db: Session = Depends(get_db),
):
    existing_coin = repo.get_by_id(coin_id)
    if not existing_coin:
        raise HTTPException(status_code=404, detail="Coin not found")
        
    try:
        # Construct Design object
        design_obj = None
        if request.design:
            design_obj = Design(
                obverse_legend=request.design.obverse_legend,
                obverse_description=request.design.obverse_description,
                reverse_legend=request.design.reverse_legend,
                reverse_description=request.design.reverse_description,
                exergue=request.design.exergue
            )
        elif existing_coin.design:
            # Preserve existing design if not provided in update
            # (Though usually frontend sends full state, so this might not be needed if form is complete)
            design_obj = existing_coin.design

        updated_coin = Coin(
            id=coin_id,
            category=Category(request.category),
            metal=Metal(request.metal),
            dimensions=Dimensions(
                weight_g=request.weight_g,
                diameter_mm=request.diameter_mm,
                die_axis=request.die_axis,
                specific_gravity=request.specific_gravity
            ),
            attribution=Attribution(
                issuer=request.issuer,
                mint=request.mint,
                year_start=request.year_start,
                year_end=request.year_end
            ),
            grading=GradingDetails(
                grading_state=GradingState(request.grading_state),
                grade=normalize_grade_for_storage(request.grade) or existing_coin.grading.grade,
                service=GradeService(request.grade_service) if request.grade_service else None,
                certification_number=request.certification,
                strike=request.strike,
                surface=request.surface
            ),
            acquisition=AcquisitionDetails(
                price=request.acquisition_price,
                currency="USD",
                source=request.acquisition_source or "Unknown",
                date=request.acquisition_date,
                url=request.acquisition_url
            ) if request.acquisition_price is not None else None,
            storage_location=request.storage_location,
            personal_notes=request.personal_notes,
            rarity=request.rarity if "rarity" in request.model_fields_set else existing_coin.rarity,
            rarity_notes=request.rarity_notes if "rarity_notes" in request.model_fields_set else existing_coin.rarity_notes,

            # Extensions
            issue_status=IssueStatus(request.issue_status) if request.issue_status else IssueStatus.OFFICIAL,
            die_info=DieInfo(
                obverse_die_id=request.obverse_die_id,
                reverse_die_id=request.reverse_die_id
            ) if (request.obverse_die_id or request.reverse_die_id) else None,
            find_data=FindData(
                find_spot=request.find_spot,
                find_date=request.find_date
            ) if (request.find_spot or request.find_date) else None,
            
            # Design - Updated
            design=design_obj,

            # Preserve or update attribution extensions (allow clearing when explicitly sent)
            denomination=request.denomination if "denomination" in request.model_fields_set else existing_coin.denomination,
            portrait_subject=request.portrait_subject if "portrait_subject" in request.model_fields_set else existing_coin.portrait_subject,
            # Preserve existing fields that aren't in simple update request
            monograms=existing_coin.monograms,
            secondary_treatments=existing_coin.secondary_treatments,
            description=existing_coin.description,
            references=existing_coin.references,
            provenance=[
                ProvenanceEntry(
                    id=p.id,
                    event_type=ProvenanceEventType(p.event_type),
                    source_name=p.source_name,
                    event_date=p.event_date,
                    date_string=p.date_string,
                    lot_number=p.lot_number,
                    notes=p.notes,
                    raw_text="",
                    hammer_price=p.hammer_price,
                    total_price=p.total_price,
                    currency=p.currency,
                    url=p.url,
                    sort_order=p.sort_order
                ) for p in request.provenance
            ] if request.provenance is not None else existing_coin.provenance,
            enrichment=existing_coin.enrichment,

            # --- Phase 1: Schema V3 Numismatic Enhancements (preserve existing if not provided) ---
            # Use model_fields_set to distinguish "not provided" from "explicitly clear"
            secondary_authority=SecondaryAuthority(
                name=request.secondary_authority.name,
                term_id=request.secondary_authority.term_id,
                authority_type=request.secondary_authority.authority_type
            ) if "secondary_authority" in request.model_fields_set and request.secondary_authority else (
                None if "secondary_authority" in request.model_fields_set else existing_coin.secondary_authority
            ),

            co_ruler=CoRuler(
                name=request.co_ruler.name,
                term_id=request.co_ruler.term_id,
                portrait_relationship=request.co_ruler.portrait_relationship
            ) if "co_ruler" in request.model_fields_set and request.co_ruler else (
                None if "co_ruler" in request.model_fields_set else existing_coin.co_ruler
            ),

            moneyer_gens=request.moneyer_gens if "moneyer_gens" in request.model_fields_set else existing_coin.moneyer_gens,

            physical_enhancements=PhysicalEnhancements(
                weight_standard=request.physical_enhancements.weight_standard,
                expected_weight_g=request.physical_enhancements.expected_weight_g,
                flan_shape=request.physical_enhancements.flan_shape,
                flan_type=request.physical_enhancements.flan_type,
                flan_notes=request.physical_enhancements.flan_notes
            ) if "physical_enhancements" in request.model_fields_set and request.physical_enhancements else (
                None if "physical_enhancements" in request.model_fields_set else existing_coin.physical_enhancements
            ),

            secondary_treatments_v3=SecondaryTreatments(
                is_overstrike=request.secondary_treatments_v3.is_overstrike,
                undertype_visible=request.secondary_treatments_v3.undertype_visible,
                undertype_attribution=request.secondary_treatments_v3.undertype_attribution,
                has_test_cut=request.secondary_treatments_v3.has_test_cut,
                test_cut_count=request.secondary_treatments_v3.test_cut_count,
                test_cut_positions=request.secondary_treatments_v3.test_cut_positions,
                has_bankers_marks=request.secondary_treatments_v3.has_bankers_marks,
                has_graffiti=request.secondary_treatments_v3.has_graffiti,
                graffiti_description=request.secondary_treatments_v3.graffiti_description,
                was_mounted=request.secondary_treatments_v3.was_mounted,
                mount_evidence=request.secondary_treatments_v3.mount_evidence
            ) if "secondary_treatments_v3" in request.model_fields_set and request.secondary_treatments_v3 else (
                None if "secondary_treatments_v3" in request.model_fields_set else existing_coin.secondary_treatments_v3
            ),

            tooling_repairs=ToolingRepairs(
                tooling_extent=request.tooling_repairs.tooling_extent,
                tooling_details=request.tooling_repairs.tooling_details,
                has_ancient_repair=request.tooling_repairs.has_ancient_repair,
                ancient_repairs=request.tooling_repairs.ancient_repairs
            ) if "tooling_repairs" in request.model_fields_set and request.tooling_repairs else (
                None if "tooling_repairs" in request.model_fields_set else existing_coin.tooling_repairs
            ),

            centering_info=Centering(
                centering=request.centering_info.centering,
                centering_notes=request.centering_info.centering_notes
            ) if "centering_info" in request.model_fields_set and request.centering_info else (
                None if "centering_info" in request.model_fields_set else existing_coin.centering_info
            ),

            die_study=DieStudyEnhancements(
                obverse_die_state=request.die_study.obverse_die_state,
                reverse_die_state=request.die_study.reverse_die_state,
                die_break_description=request.die_study.die_break_description
            ) if "die_study" in request.model_fields_set and request.die_study else (
                None if "die_study" in request.model_fields_set else existing_coin.die_study
            ),

            grading_tpg=GradingTPGEnhancements(
                grade_numeric=request.grading_tpg.grade_numeric,
                grade_designation=request.grading_tpg.grade_designation,
                has_star_designation=request.grading_tpg.has_star_designation,
                photo_certificate=request.grading_tpg.photo_certificate,
                verification_url=request.grading_tpg.verification_url
            ) if "grading_tpg" in request.model_fields_set and request.grading_tpg else (
                None if "grading_tpg" in request.model_fields_set else existing_coin.grading_tpg
            ),

            chronology=ChronologyEnhancements(
                date_period_notation=request.chronology.date_period_notation,
                emission_phase=request.chronology.emission_phase
            ) if "chronology" in request.model_fields_set and request.chronology else (
                None if "chronology" in request.model_fields_set else existing_coin.chronology
            ),
        )
        
        # Add images manually here since DTO/UseCase flow is pending update
        for img in request.images:
            updated_coin.add_image(img.url, img.image_type, img.is_primary)
        
        saved = repo.save(updated_coin)
        if request.references is not None and saved.id:
            from src.application.services.reference_sync import sync_coin_references
            valid_refs = [
                r.model_dump() for r in request.references
                if (r.catalog and r.catalog.strip()) and (r.number and r.number.strip())
            ]
            sync_coin_references(db, saved.id, valid_refs, "user")
            saved = repo.get_by_id(saved.id) or saved
        return CoinResponse.from_domain(saved)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{coin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coin(
    coin_id: int,
    repo: ICoinRepository = Depends(get_coin_repo)
):
    # First check if coin exists
    coin = repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    
    # Perform deletion
    deleted = repo.delete(coin_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete coin")


# --- Reference Search Endpoint ---

class ReferenceSearchResponse(BaseModel):
    """Response for reference search endpoint."""
    coins: List[CoinResponse]
    total: int
    catalog: str
    number: str
    volume: Optional[str] = None


@router.get("/by-reference", response_model=ReferenceSearchResponse)
def get_coins_by_reference(
    catalog: str = Query(..., description="Catalog system (e.g., RIC, Crawford, Sear, RSC, RPC, BMC). May include volume: 'RPC I' -> RPC vol I"),
    number: str = Query(..., description="Reference number (e.g., 756, 44/5, 1234a)"),
    volume: Optional[str] = Query(None, description="Volume (e.g., II, V.1) - optional; also parsed from catalog if e.g. 'RPC I'"),
    repo: ICoinRepository = Depends(get_coin_repo)
):
    """
    Search for coins by catalog reference.
    
    Examples:
    - /api/v2/coins/by-reference?catalog=RIC&number=756
    - /api/v2/coins/by-reference?catalog=RIC&volume=II&number=756
    - /api/v2/coins/by-reference?catalog=RPC%20I&number=4374  (RPC I 4374)
    - /api/v2/coins/by-reference?catalog=Crawford&number=44/5
    
    Note: This endpoint requires the coin_references table to be populated.
    """
    from src.infrastructure.services.catalogs.catalog_systems import split_catalog_and_volume
    catalog_display, volume_from_catalog = split_catalog_and_volume(catalog)
    effective_volume = volume or volume_from_catalog
    coins = repo.get_by_reference(catalog=catalog_display, number=number, volume=effective_volume)
    
    return ReferenceSearchResponse(
        coins=[CoinResponse.from_domain(c) for c in coins],
        total=len(coins),
        catalog=catalog_display,
        number=number,
        volume=effective_volume
    )
