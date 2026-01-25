"""
CoinStack LLM Domain Layer.

This module defines the domain-level interfaces, value objects, and error types
for LLM services. Following Clean Architecture: Domain has NO external dependencies.

Capabilities are organized by priority tier:
- P0 (MVP): vocab_normalize, legend_expand, auction_parse, provenance_parse
- P1 (Core): image_identify, reference_validate, context_generate
- P2 (Advanced): attribution_assist, legend_transcribe, catalog_parse, condition_observations
- P3 (Deferred): search_assist, collection_insights, description_generate, die_study
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol, Optional, Any, List, Union, runtime_checkable


# =============================================================================
# CAPABILITIES
# =============================================================================

class LLMCapability(str, Enum):
    """
    LLM capabilities organized by priority tier.
    
    P0 (MVP): Automates most tedious data entry
    P1 (Core): High value, well-defined
    P2 (Advanced): Useful but complex
    P3 (Deferred): Scope creep risk, lower ROI
    """
    # P0: MVP Capabilities (Phase 1A)
    VOCAB_NORMALIZE = "vocab_normalize"
    LEGEND_EXPAND = "legend_expand"
    AUCTION_PARSE = "auction_parse"
    PROVENANCE_PARSE = "provenance_parse"
    
    # P1: Core Capabilities (Phase 1B)
    IMAGE_IDENTIFY = "image_identify"
    REFERENCE_VALIDATE = "reference_validate"
    CONTEXT_GENERATE = "context_generate"
    
    # P2: Advanced Capabilities (Phase 2+)
    ATTRIBUTION_ASSIST = "attribution_assist"
    LEGEND_TRANSCRIBE = "legend_transcribe"
    CATALOG_PARSE = "catalog_parse"
    CONDITION_OBSERVATIONS = "condition_observations"
    
    # P3: Deferred Capabilities (Phase 3+)
    SEARCH_ASSIST = "search_assist"
    COLLECTION_INSIGHTS = "collection_insights"
    DESCRIPTION_GENERATE = "description_generate"
    DIE_STUDY = "die_study"
    
    @classmethod
    def p0_capabilities(cls) -> list["LLMCapability"]:
        """Return P0 (MVP) capabilities."""
        return [cls.VOCAB_NORMALIZE, cls.LEGEND_EXPAND, cls.AUCTION_PARSE, cls.PROVENANCE_PARSE]
    
    @classmethod
    def p1_capabilities(cls) -> list["LLMCapability"]:
        """Return P1 (Core) capabilities."""
        return [cls.IMAGE_IDENTIFY, cls.REFERENCE_VALIDATE, cls.CONTEXT_GENERATE]
    
    @classmethod
    def mvp_capabilities(cls) -> list["LLMCapability"]:
        """Return all MVP capabilities (P0 + P1)."""
        return cls.p0_capabilities() + cls.p1_capabilities()
    
    @classmethod
    def p2_capabilities(cls) -> list["LLMCapability"]:
        """Return P2 (Advanced) capabilities."""
        return [
            cls.ATTRIBUTION_ASSIST,
            cls.LEGEND_TRANSCRIBE,
            cls.CATALOG_PARSE,
            cls.CONDITION_OBSERVATIONS
        ]
    
    @classmethod
    def p3_capabilities(cls) -> list["LLMCapability"]:
        """Return P3 (Deferred) capabilities."""
        return [cls.SEARCH_ASSIST, cls.COLLECTION_INSIGHTS, cls.DESCRIPTION_GENERATE, cls.DIE_STUDY]


# =============================================================================
# ERRORS
# =============================================================================

class LLMError(Exception):
    """Base class for all LLM-related errors."""
    pass


class LLMParseError(LLMError):
    """LLM returned unparseable output."""
    
    def __init__(self, message: str, raw_output: str, capability: str):
        super().__init__(message)
        self.raw_output = raw_output
        self.capability = capability
    
    def __str__(self) -> str:
        return f"{self.args[0]} (capability={self.capability}, output_preview={self.raw_output[:100]}...)"


class LLMHallucinationDetected(LLMError):
    """Output failed validation (e.g., invalid RIC reference)."""
    
    def __init__(self, message: str, field: str, invalid_value: str):
        super().__init__(message)
        self.field = field
        self.invalid_value = invalid_value
    
    def __str__(self) -> str:
        return f"{self.args[0]} (field={self.field}, value={self.invalid_value})"


class LLMProviderUnavailable(LLMError):
    """All LLM providers failed."""
    
    def __init__(self, message: str, providers_tried: List[str]):
        super().__init__(message)
        self.providers_tried = providers_tried
    
    def __str__(self) -> str:
        return f"{self.args[0]} (tried: {', '.join(self.providers_tried)})"


class LLMRateLimitExceeded(LLMError):
    """Rate limit exceeded for this operation."""
    
    def __init__(self, message: str, retry_after_seconds: int):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
    
    def __str__(self) -> str:
        return f"{self.args[0]} (retry after {self.retry_after_seconds}s)"


class LLMBudgetExceeded(LLMError):
    """Monthly budget has been exceeded."""
    
    def __init__(self, message: str, current_cost: float, budget: float):
        super().__init__(message)
        self.current_cost = current_cost
        self.budget = budget
    
    def __str__(self) -> str:
        return f"{self.args[0]} (current=${self.current_cost:.2f}, budget=${self.budget:.2f})"


class LLMCapabilityNotAvailable(LLMError):
    """Requested capability is not available in current profile."""
    
    def __init__(self, capability: str, profile: str):
        super().__init__(f"Capability '{capability}' not available in profile '{profile}'")
        self.capability = capability
        self.profile = profile


# =============================================================================
# RESULT VALUE OBJECTS
# =============================================================================

@dataclass(frozen=True)
class LLMResult:
    """
    Base result from an LLM operation.
    
    This is a domain value object - it contains no infrastructure details
    except what's needed for audit/tracking purposes.
    """
    content: str
    confidence: float  # 0.0 to 1.0
    cost_usd: float
    model_used: str
    cached: bool = False
    reasoning: List[str] = field(default_factory=list)  # "Why" explanations
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if result confidence is above threshold (0.8)."""
        return self.confidence >= 0.8
    
    @property
    def needs_review(self) -> bool:
        """Check if result should be flagged for human review."""
        return self.confidence < 0.7
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
        if self.cost_usd < 0:
            raise ValueError(f"Cost cannot be negative, got {self.cost_usd}")


@dataclass(frozen=True)
class VocabNormalizationResult(LLMResult):
    """Result of vocabulary normalization (vocab_normalize capability)."""
    raw_input: str = ""
    canonical_name: str = ""
    vocab_type: str = ""  # "issuer", "mint", "denomination"


@dataclass(frozen=True)
class LegendExpansionResult(LLMResult):
    """Result of legend expansion (legend_expand capability)."""
    abbreviated: str = ""
    expanded: str = ""


@dataclass(frozen=True)
class ProvenanceEntry:
    """A single entry in a provenance chain."""
    source: str
    source_type: str  # "auction", "collection", "dealer", "publication"
    year: Optional[int] = None
    sale: Optional[str] = None
    lot: Optional[str] = None


@dataclass(frozen=True)
class ProvenanceParseResult(LLMResult):
    """Result of provenance parsing (provenance_parse capability)."""
    raw_text: str = ""
    provenance_chain: List[ProvenanceEntry] = field(default_factory=list)
    earliest_known: Optional[int] = None


@dataclass(frozen=True)
class AuctionParseResult(LLMResult):
    """Result of auction description parsing (auction_parse capability)."""
    raw_text: str = ""
    issuer: Optional[str] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    weight_g: Optional[float] = None
    diameter_mm: Optional[float] = None
    obverse_legend: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_description: Optional[str] = None
    references: List[str] = field(default_factory=list)
    grade: Optional[str] = None


@dataclass(frozen=True)
class CoinIdentificationResult(LLMResult):
    """Result of coin image identification (image_identify capability)."""
    ruler: Optional[str] = None
    denomination: Optional[str] = None
    mint: Optional[str] = None
    date_range: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_description: Optional[str] = None
    suggested_references: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReferenceValidationResult(LLMResult):
    """Result of reference validation (reference_validate capability)."""
    reference: str = ""
    is_valid: bool = False
    normalized: str = ""
    alternatives: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass(frozen=True)
class SearchAssistResult(LLMResult):
    """Result of search assistance (search_assist capability)."""
    query: str = ""
    extracted_keywords: List[str] = field(default_factory=list)
    suggested_filters: dict = field(default_factory=dict)
    interpretation: str = ""
    needs_clarification: bool = False
    ambiguities: List[dict] = field(default_factory=list)


# =============================================================================
# P2 RESULT TYPES (Advanced Capabilities)
# =============================================================================

@dataclass(frozen=True)
class AttributionSuggestion:
    """
    A single attribution suggestion with reasoning.
    
    Used by attribution_assist capability to provide ranked suggestions
    with full reasoning chains for verification.
    """
    attribution: str  # "Caracalla, Denarius, Rome mint, 213 AD"
    reference: str    # "RIC IV 223"
    confidence: float
    reasoning: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AttributionAssistResult(LLMResult):
    """
    Result of attribution_assist capability.
    
    Provides ranked suggestions for coin attribution from partial information
    (legend fragments, weight, design elements). Also lists questions that
    would help narrow down the attribution.
    """
    suggestions: List[AttributionSuggestion] = field(default_factory=list)
    questions_to_resolve: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class LegendTranscribeResult(LLMResult):
    """
    Result of legend_transcribe capability (OCR from images).
    
    Uses vision model to read legend characters from coin images.
    Handles worn/uncertain portions with [...] notation and provides
    both abbreviated and expanded forms.
    """
    obverse_legend: Optional[str] = None
    obverse_legend_expanded: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_legend_expanded: Optional[str] = None
    exergue: Optional[str] = None
    uncertain_portions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CatalogParseResult(LLMResult):
    """
    Result of catalog_parse capability.
    
    Parses catalog reference strings (e.g., "RIC II 207") into
    structured components. Recognizes major systems: RIC, RSC, RPC,
    Crawford, Sear, BMC, Cohen.
    """
    raw_reference: str = ""
    catalog_system: str = ""  # "RIC", "Crawford", "RSC", etc.
    volume: Optional[str] = None  # "II", "IV.1", etc.
    number: str = ""
    issuer: Optional[str] = None  # Inferred from catalog volume
    mint: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)  # Cross-references


@dataclass(frozen=True)
class ConditionObservationsResult(LLMResult):
    """
    Result of condition_observations capability.
    
    Describes observable wear patterns and surface conditions WITHOUT
    numeric grades. This is critical: NO VF/EF/AU terminology allowed.
    Always recommends professional grading for consequential decisions.
    """
    wear_observations: str = ""
    surface_notes: str = ""
    strike_quality: str = ""
    notable_features: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    recommendation: str = "Professional grading recommended for sale/insurance"


# =============================================================================
# ENRICHMENT TYPES
# =============================================================================

@dataclass
class EnrichmentDiff:
    """
    Safe JSON diff for coin enrichment.
    
    Separates safe auto-fills from conflicts requiring review.
    """
    safe_fills: dict[str, Any] = field(default_factory=dict)
    conflicts: dict[str, dict] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_safe_fill(self, field_name: str, value: Any, source: str) -> None:
        """Add a safe auto-fill (empty field -> value)."""
        self.safe_fills[field_name] = value
        self.notes.append(f"{field_name}: {value} (via {source})")
    
    def add_conflict(
        self,
        field_name: str,
        current: Any,
        suggested: Any,
        reason: str,
        confidence: float
    ) -> None:
        """Add a conflict requiring review."""
        self.conflicts[field_name] = {
            "current": current,
            "suggested": suggested,
            "reason": reason,
            "confidence": confidence,
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "safe_fills": self.safe_fills,
            "conflicts": self.conflicts,
            "notes": self.notes,
            "warnings": self.warnings,
        }


@dataclass
class EnrichmentResult:
    """Result of enrichment use case."""
    coin_id: int
    diff: EnrichmentDiff
    total_cost_usd: float
    tasks_completed: List[str]
    tasks_skipped: List[str]
    errors: List[str]
    request_id: Optional[str] = None
    
    @property
    def has_conflicts(self) -> bool:
        """Check if there are conflicts requiring review."""
        return len(self.diff.conflicts) > 0
    
    @property
    def has_safe_fills(self) -> bool:
        """Check if there are safe fills to apply."""
        return len(self.diff.safe_fills) > 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "coin_id": self.coin_id,
            "diff": self.diff.to_dict(),
            "total_cost_usd": self.total_cost_usd,
            "tasks_completed": self.tasks_completed,
            "tasks_skipped": self.tasks_skipped,
            "errors": self.errors,
            "has_conflicts": self.has_conflicts,
            "has_safe_fills": self.has_safe_fills,
            "request_id": self.request_id,
        }


# =============================================================================
# FUZZY MATCH RESULT (for fallback)
# =============================================================================

@dataclass(frozen=True)
class FuzzyMatch:
    """Result of fuzzy string matching (for fallback when LLM unavailable)."""
    canonical_name: str
    score: float  # 0.0 to 1.0 similarity score
    vocab_type: str
    vocab_id: Optional[int] = None


# =============================================================================
# SERVICE PROTOCOL
# =============================================================================

@runtime_checkable
class ILLMService(Protocol):
    """
    Domain-level LLM service interface.
    
    This protocol defines what the domain expects from an LLM service.
    The infrastructure layer provides the implementation.
    
    Usage in application layer:
        class LLMEnrichCoinUseCase:
            def __init__(self, llm: ILLMService):
                self._llm = llm
            
            async def execute(self, coin_id: int) -> EnrichmentResult:
                result = await self._llm.normalize_vocab(
                    "IMP CAES AVG", "issuer"
                )
    """
    
    # -------------------------------------------------------------------------
    # Generic completion
    # -------------------------------------------------------------------------
    
    async def complete(
        self,
        capability: LLMCapability,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[dict] = None,
        image_b64: Optional[str] = None,
    ) -> LLMResult:
        """
        Generic completion for any capability.
        
        Args:
            capability: The task type
            prompt: User prompt
            system: Optional system prompt override
            context: Optional context dict
            image_b64: Optional base64 image for vision tasks
        
        Returns:
            LLMResult with content and metadata
        """
        ...
    
    # -------------------------------------------------------------------------
    # P0 Capabilities
    # -------------------------------------------------------------------------
    
    async def normalize_vocab(
        self,
        raw_text: str,
        vocab_type: str,
        context: Optional[dict] = None,
    ) -> VocabNormalizationResult:
        """
        Normalize vocabulary term to canonical form.
        
        Args:
            raw_text: Raw input (e.g., "IMP CAES AVG")
            vocab_type: Type of vocab ("issuer", "mint", "denomination")
            context: Optional context (era, category, etc.)
        
        Returns:
            VocabNormalizationResult with canonical name
        """
        ...
    
    async def expand_legend(
        self,
        abbreviation: str,
    ) -> LegendExpansionResult:
        """
        Expand abbreviated Latin legend.
        
        Args:
            abbreviation: Abbreviated legend (e.g., "IMP CAESAR AVG")
        
        Returns:
            LegendExpansionResult with expanded form
        """
        ...
    
    async def parse_auction(
        self,
        description: str,
        hints: Optional[dict] = None,
    ) -> AuctionParseResult:
        """
        Parse auction lot description into structured data.
        
        Args:
            description: Full auction lot description text
            hints: Optional hints (auction house, category, etc.)
        
        Returns:
            AuctionParseResult with extracted fields
        """
        ...
    
    async def parse_provenance(
        self,
        description: str,
    ) -> ProvenanceParseResult:
        """
        Extract provenance chain from description text.
        
        Args:
            description: Text containing provenance information
        
        Returns:
            ProvenanceParseResult with structured provenance chain
        """
        ...
    
    # -------------------------------------------------------------------------
    # P1 Capabilities
    # -------------------------------------------------------------------------
    
    async def identify_coin(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> CoinIdentificationResult:
        """
        Identify coin from image.
        
        Args:
            image_b64: Base64-encoded image
            hints: Optional hints (category, era, etc.)
        
        Returns:
            CoinIdentificationResult with identification
        """
        ...
    
    async def validate_reference(
        self,
        reference: str,
        coin_context: Optional[dict] = None,
    ) -> ReferenceValidationResult:
        """
        Validate and cross-reference catalog number.
        
        Args:
            reference: Reference to validate (e.g., "RIC II 207")
            coin_context: Optional context (issuer, denomination, etc.)
        
        Returns:
            ReferenceValidationResult with validation status
        """
        ...
    
    async def generate_context(
        self,
        coin_data: dict,
    ) -> LLMResult:
        """
        Generate historical context narrative.
        
        Args:
            coin_data: Dict with coin attributes
        
        Returns:
            LLMResult with narrative text
        """
        ...
    
    # -------------------------------------------------------------------------
    # P2 Capabilities (Advanced)
    # -------------------------------------------------------------------------
    
    async def assist_attribution(
        self,
        known_info: dict,
    ) -> AttributionAssistResult:
        """
        Suggest attribution from partial coin information.
        
        Args:
            known_info: Dict with partial coin info (legend fragments, 
                       weight, diameter, design descriptions)
        
        Returns:
            AttributionAssistResult with ranked suggestions and questions
        """
        ...
    
    async def transcribe_legend(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> LegendTranscribeResult:
        """
        OCR-like legend transcription from coin images.
        
        Uses vision model to read legend characters. Handles worn/uncertain
        portions with [...] notation.
        
        Args:
            image_b64: Base64-encoded coin image
            hints: Optional hints (known ruler, era, etc.)
        
        Returns:
            LegendTranscribeResult with transcribed legends
        """
        ...
    
    async def parse_catalog(
        self,
        reference: str,
    ) -> CatalogParseResult:
        """
        Parse catalog reference string into components.
        
        Recognizes: RIC, RSC, RPC, Crawford, Sear, BMC, Cohen
        
        Args:
            reference: Reference string (e.g., "RIC II 207")
        
        Returns:
            CatalogParseResult with parsed components
        """
        ...
    
    async def observe_condition(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> ConditionObservationsResult:
        """
        Describe wear patterns and condition (NOT grades).
        
        CRITICAL: Does NOT provide numeric grades (VF/EF/AU).
        Describes observable facts only.
        
        Args:
            image_b64: Base64-encoded coin image
            hints: Optional hints about coin type
        
        Returns:
            ConditionObservationsResult with wear descriptions
        """
        ...
    
    # -------------------------------------------------------------------------
    # Admin methods
    # -------------------------------------------------------------------------
    
    def get_monthly_cost(self) -> float:
        """Get current month's total cost."""
        ...
    
    def get_active_profile(self) -> str:
        """Get current configuration profile (development/production/offline)."""
        ...
    
    def is_capability_available(self, capability: LLMCapability) -> bool:
        """Check if a capability is available in current profile."""
        ...
