from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import date
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal,
    GradingDetails, GradingState, GradeService, AcquisitionDetails,
    IssueStatus, DieInfo, FindData, Design, CoinImage,
    # Phase 1: Schema V3 value objects
    SecondaryAuthority, CoRuler, PhysicalEnhancements, SecondaryTreatments,
    ToolingRepairs, Centering, DieStudyEnhancements, GradingTPGEnhancements, ChronologyEnhancements
)
from src.domain.repositories import ICoinRepository

@dataclass
class ImageDTO:
    url: str
    image_type: str
    is_primary: bool = False

@dataclass
class DesignDTO:
    obverse_legend: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_description: Optional[str] = None
    exergue: Optional[str] = None


# --- Phase 1: Schema V3 DTO Classes ---

@dataclass
class SecondaryAuthorityDTO:
    name: Optional[str] = None
    term_id: Optional[int] = None
    authority_type: Optional[str] = None


@dataclass
class CoRulerDTO:
    name: Optional[str] = None
    term_id: Optional[int] = None
    portrait_relationship: Optional[str] = None


@dataclass
class PhysicalEnhancementsDTO:
    weight_standard: Optional[str] = None
    expected_weight_g: Optional[Decimal] = None
    flan_shape: Optional[str] = None
    flan_type: Optional[str] = None
    flan_notes: Optional[str] = None


@dataclass
class SecondaryTreatmentsV3DTO:
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


@dataclass
class ToolingRepairsDTO:
    tooling_extent: Optional[str] = None
    tooling_details: Optional[str] = None
    has_ancient_repair: bool = False
    ancient_repairs: Optional[str] = None


@dataclass
class CenteringDTO:
    centering: Optional[str] = None
    centering_notes: Optional[str] = None


@dataclass
class DieStudyEnhancementsDTO:
    obverse_die_state: Optional[str] = None
    reverse_die_state: Optional[str] = None
    die_break_description: Optional[str] = None


@dataclass
class GradingTPGEnhancementsDTO:
    grade_numeric: Optional[int] = None
    grade_designation: Optional[str] = None
    has_star_designation: bool = False
    photo_certificate: bool = False
    verification_url: Optional[str] = None


@dataclass
class ChronologyEnhancementsDTO:
    date_period_notation: Optional[str] = None
    emission_phase: Optional[str] = None


@dataclass
class CreateCoinDTO:
    category: str
    metal: str
    diameter_mm: Decimal
    issuer: str
    grading_state: str
    grade: str
    weight_g: Optional[Decimal] = None
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
    
    # Extensions & New Fields
    denomination: Optional[str] = None
    portrait_subject: Optional[str] = None
    design: Optional[DesignDTO] = None

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

    # Lists
    images: List[ImageDTO] = field(default_factory=list)

    # --- Phase 1: Schema V3 Numismatic Enhancements ---
    secondary_authority: Optional[SecondaryAuthorityDTO] = None
    co_ruler: Optional[CoRulerDTO] = None
    moneyer_gens: Optional[str] = None
    physical_enhancements: Optional[PhysicalEnhancementsDTO] = None
    secondary_treatments_v3: Optional[SecondaryTreatmentsV3DTO] = None
    tooling_repairs: Optional[ToolingRepairsDTO] = None
    centering_info: Optional[CenteringDTO] = None
    die_study: Optional[DieStudyEnhancementsDTO] = None
    grading_tpg: Optional[GradingTPGEnhancementsDTO] = None
    chronology: Optional[ChronologyEnhancementsDTO] = None

class CreateCoinUseCase:
    def __init__(self, repository: ICoinRepository):
        self.repository = repository

    def execute(self, dto: CreateCoinDTO) -> Coin:
        try:
            category = Category(dto.category)
            metal = Metal(dto.metal)
            grading_state = GradingState(dto.grading_state)
            grade_service = GradeService(dto.grade_service) if dto.grade_service else None
            issue_status = IssueStatus(dto.issue_status) if dto.issue_status else IssueStatus.OFFICIAL
        except ValueError as e:
            raise ValueError(f"Invalid enum value: {e}")

        grading = GradingDetails(
            grading_state=grading_state,
            grade=dto.grade,
            service=grade_service,
            certification_number=dto.certification,
            strike=dto.strike,
            surface=dto.surface,
        )

        acquisition = None
        if dto.acquisition_price is not None:
            acquisition = AcquisitionDetails(
                price=dto.acquisition_price,
                currency="USD", # Default for now
                source=dto.acquisition_source or "Unknown",
                date=dto.acquisition_date,
                url=dto.acquisition_url
            )

        # Build Design value object
        design = None
        if dto.design:
            design = Design(
                obverse_legend=dto.design.obverse_legend,
                obverse_description=dto.design.obverse_description,
                reverse_legend=dto.design.reverse_legend,
                reverse_description=dto.design.reverse_description,
                exergue=dto.design.exergue
            )

        # Map Images
        images = [
            CoinImage(url=img.url, image_type=img.image_type, is_primary=img.is_primary)
            for img in dto.images
        ]

        new_coin = Coin(
            id=None,
            category=category,
            metal=metal,
            dimensions=Dimensions(
                weight_g=dto.weight_g,
                diameter_mm=dto.diameter_mm,
                die_axis=dto.die_axis,
                specific_gravity=dto.specific_gravity
            ),
            attribution=Attribution(
                issuer=dto.issuer,
                mint=dto.mint,
                year_start=dto.year_start,
                year_end=dto.year_end
            ),
            grading=grading,
            acquisition=acquisition,

            # New Fields
            denomination=dto.denomination,
            portrait_subject=dto.portrait_subject,
            design=design,
            images=images,

            # Collection management
            storage_location=dto.storage_location,
            personal_notes=dto.personal_notes,

            # Rarity
            rarity=dto.rarity,
            rarity_notes=dto.rarity_notes,

            # Extensions
            issue_status=issue_status,
            die_info=DieInfo(
                obverse_die_id=dto.obverse_die_id,
                reverse_die_id=dto.reverse_die_id
            ) if (dto.obverse_die_id or dto.reverse_die_id) else None,
            find_data=FindData(
                find_spot=dto.find_spot,
                find_date=dto.find_date
            ) if (dto.find_spot or dto.find_date) else None,

            # --- Phase 1: Schema V3 Numismatic Enhancements ---
            secondary_authority=SecondaryAuthority(
                name=dto.secondary_authority.name,
                term_id=dto.secondary_authority.term_id,
                authority_type=dto.secondary_authority.authority_type
            ) if dto.secondary_authority else None,
            co_ruler=CoRuler(
                name=dto.co_ruler.name,
                term_id=dto.co_ruler.term_id,
                portrait_relationship=dto.co_ruler.portrait_relationship
            ) if dto.co_ruler else None,
            moneyer_gens=dto.moneyer_gens,
            physical_enhancements=PhysicalEnhancements(
                weight_standard=dto.physical_enhancements.weight_standard,
                expected_weight_g=dto.physical_enhancements.expected_weight_g,
                flan_shape=dto.physical_enhancements.flan_shape,
                flan_type=dto.physical_enhancements.flan_type,
                flan_notes=dto.physical_enhancements.flan_notes
            ) if dto.physical_enhancements else None,
            secondary_treatments_v3=SecondaryTreatments(
                is_overstrike=dto.secondary_treatments_v3.is_overstrike,
                undertype_visible=dto.secondary_treatments_v3.undertype_visible,
                undertype_attribution=dto.secondary_treatments_v3.undertype_attribution,
                has_test_cut=dto.secondary_treatments_v3.has_test_cut,
                test_cut_count=dto.secondary_treatments_v3.test_cut_count,
                test_cut_positions=dto.secondary_treatments_v3.test_cut_positions,
                has_bankers_marks=dto.secondary_treatments_v3.has_bankers_marks,
                has_graffiti=dto.secondary_treatments_v3.has_graffiti,
                graffiti_description=dto.secondary_treatments_v3.graffiti_description,
                was_mounted=dto.secondary_treatments_v3.was_mounted,
                mount_evidence=dto.secondary_treatments_v3.mount_evidence
            ) if dto.secondary_treatments_v3 else None,
            tooling_repairs=ToolingRepairs(
                tooling_extent=dto.tooling_repairs.tooling_extent,
                tooling_details=dto.tooling_repairs.tooling_details,
                has_ancient_repair=dto.tooling_repairs.has_ancient_repair,
                ancient_repairs=dto.tooling_repairs.ancient_repairs
            ) if dto.tooling_repairs else None,
            centering_info=Centering(
                centering=dto.centering_info.centering,
                centering_notes=dto.centering_info.centering_notes
            ) if dto.centering_info else None,
            die_study=DieStudyEnhancements(
                obverse_die_state=dto.die_study.obverse_die_state,
                reverse_die_state=dto.die_study.reverse_die_state,
                die_break_description=dto.die_study.die_break_description
            ) if dto.die_study else None,
            grading_tpg=GradingTPGEnhancements(
                grade_numeric=dto.grading_tpg.grade_numeric,
                grade_designation=dto.grading_tpg.grade_designation,
                has_star_designation=dto.grading_tpg.has_star_designation,
                photo_certificate=dto.grading_tpg.photo_certificate,
                verification_url=dto.grading_tpg.verification_url
            ) if dto.grading_tpg else None,
            chronology=ChronologyEnhancements(
                date_period_notation=dto.chronology.date_period_notation,
                emission_phase=dto.chronology.emission_phase
            ) if dto.chronology else None,
        )

        return self.repository.save(new_coin)