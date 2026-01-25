"""
Unit tests for LLM domain layer.

Tests the domain entities, value objects, and error types defined in
src/domain/llm.py without any infrastructure dependencies.
"""

import pytest
from src.domain.llm import (
    # Enums
    LLMCapability,
    # Errors
    LLMError,
    LLMParseError,
    LLMHallucinationDetected,
    LLMProviderUnavailable,
    LLMRateLimitExceeded,
    LLMBudgetExceeded,
    LLMCapabilityNotAvailable,
    # Result types
    LLMResult,
    VocabNormalizationResult,
    LegendExpansionResult,
    AuctionParseResult,
    ProvenanceParseResult,
    ProvenanceEntry,
    CoinIdentificationResult,
    ReferenceValidationResult,
    SearchAssistResult,
    # Enrichment types
    EnrichmentDiff,
    EnrichmentResult,
    # Fuzzy match
    FuzzyMatch,
)


# =============================================================================
# CAPABILITY ENUM TESTS
# =============================================================================

class TestLLMCapability:
    """Tests for LLMCapability enum."""
    
    def test_p0_capabilities(self):
        """P0 capabilities should include MVP capabilities."""
        p0 = LLMCapability.p0_capabilities()
        assert LLMCapability.VOCAB_NORMALIZE in p0
        assert LLMCapability.LEGEND_EXPAND in p0
        assert LLMCapability.AUCTION_PARSE in p0
        assert LLMCapability.PROVENANCE_PARSE in p0
        assert len(p0) == 4
    
    def test_p1_capabilities(self):
        """P1 capabilities should include core capabilities."""
        p1 = LLMCapability.p1_capabilities()
        assert LLMCapability.IMAGE_IDENTIFY in p1
        assert LLMCapability.REFERENCE_VALIDATE in p1
        assert LLMCapability.CONTEXT_GENERATE in p1
        assert len(p1) == 3
    
    def test_mvp_capabilities(self):
        """MVP should be P0 + P1."""
        mvp = LLMCapability.mvp_capabilities()
        assert len(mvp) == 7
        assert LLMCapability.VOCAB_NORMALIZE in mvp
        assert LLMCapability.IMAGE_IDENTIFY in mvp
    
    def test_capability_values(self):
        """Capability values should be snake_case strings."""
        assert LLMCapability.VOCAB_NORMALIZE.value == "vocab_normalize"
        assert LLMCapability.IMAGE_IDENTIFY.value == "image_identify"


# =============================================================================
# ERROR TYPE TESTS
# =============================================================================

class TestLLMErrors:
    """Tests for LLM error types."""
    
    def test_llm_parse_error(self):
        """LLMParseError should capture raw output."""
        error = LLMParseError(
            "Failed to parse JSON",
            raw_output="invalid json {",
            capability="vocab_normalize"
        )
        assert error.raw_output == "invalid json {"
        assert error.capability == "vocab_normalize"
        assert "vocab_normalize" in str(error)
    
    def test_llm_hallucination_detected(self):
        """LLMHallucinationDetected should capture field info."""
        error = LLMHallucinationDetected(
            "Invalid reference format",
            field="reference",
            invalid_value="RIC XXIV 9999"
        )
        assert error.field == "reference"
        assert error.invalid_value == "RIC XXIV 9999"
        assert "reference" in str(error)
    
    def test_llm_provider_unavailable(self):
        """LLMProviderUnavailable should list tried providers."""
        error = LLMProviderUnavailable(
            "All providers failed",
            providers_tried=["claude-haiku", "k2", "ollama-phi3"]
        )
        assert len(error.providers_tried) == 3
        assert "claude-haiku" in str(error)
    
    def test_llm_rate_limit_exceeded(self):
        """LLMRateLimitExceeded should include retry time."""
        error = LLMRateLimitExceeded(
            "Rate limit exceeded",
            retry_after_seconds=120
        )
        assert error.retry_after_seconds == 120
        assert "120" in str(error)
    
    def test_llm_budget_exceeded(self):
        """LLMBudgetExceeded should include cost info."""
        error = LLMBudgetExceeded(
            "Budget exceeded",
            current_cost=5.23,
            budget=5.0
        )
        assert error.current_cost == 5.23
        assert error.budget == 5.0
        assert "5.23" in str(error)
    
    def test_llm_capability_not_available(self):
        """LLMCapabilityNotAvailable should include profile."""
        error = LLMCapabilityNotAvailable(
            capability="die_study",
            profile="offline"
        )
        assert error.capability == "die_study"
        assert error.profile == "offline"


# =============================================================================
# LLM RESULT TESTS
# =============================================================================

class TestLLMResult:
    """Tests for LLMResult value object."""
    
    def test_basic_result(self):
        """LLMResult should store basic fields."""
        result = LLMResult(
            content="Augustus",
            confidence=0.92,
            cost_usd=0.001,
            model_used="claude-haiku",
        )
        assert result.content == "Augustus"
        assert result.confidence == 0.92
        assert result.cost_usd == 0.001
        assert result.model_used == "claude-haiku"
        assert result.cached is False
    
    def test_high_confidence(self):
        """is_high_confidence should be True for >= 0.8."""
        high = LLMResult("x", confidence=0.85, cost_usd=0, model_used="m")
        low = LLMResult("x", confidence=0.75, cost_usd=0, model_used="m")
        assert high.is_high_confidence is True
        assert low.is_high_confidence is False
    
    def test_needs_review(self):
        """needs_review should be True for < 0.7."""
        high = LLMResult("x", confidence=0.75, cost_usd=0, model_used="m")
        low = LLMResult("x", confidence=0.65, cost_usd=0, model_used="m")
        assert high.needs_review is False
        assert low.needs_review is True
    
    def test_confidence_validation(self):
        """Confidence must be 0.0-1.0."""
        with pytest.raises(ValueError):
            LLMResult("x", confidence=1.5, cost_usd=0, model_used="m")
        with pytest.raises(ValueError):
            LLMResult("x", confidence=-0.1, cost_usd=0, model_used="m")
    
    def test_cost_validation(self):
        """Cost cannot be negative."""
        with pytest.raises(ValueError):
            LLMResult("x", confidence=0.5, cost_usd=-0.01, model_used="m")
    
    def test_reasoning(self):
        """Reasoning should be a list."""
        result = LLMResult(
            content="x",
            confidence=0.9,
            cost_usd=0,
            model_used="m",
            reasoning=["reason 1", "reason 2"]
        )
        assert len(result.reasoning) == 2
    
    def test_cached_result(self):
        """Cached results should be marked."""
        result = LLMResult(
            content="x",
            confidence=0.9,
            cost_usd=0,
            model_used="m",
            cached=True
        )
        assert result.cached is True


class TestVocabNormalizationResult:
    """Tests for VocabNormalizationResult."""
    
    def test_vocab_result(self):
        """VocabNormalizationResult should extend LLMResult."""
        result = VocabNormalizationResult(
            content='{"canonical_name": "Augustus"}',
            confidence=0.92,
            cost_usd=0.001,
            model_used="mock",
            raw_input="IMP CAES AVG",
            canonical_name="Augustus",
            vocab_type="issuer",
        )
        assert result.raw_input == "IMP CAES AVG"
        assert result.canonical_name == "Augustus"
        assert result.vocab_type == "issuer"
        assert result.is_high_confidence is True


class TestLegendExpansionResult:
    """Tests for LegendExpansionResult."""
    
    def test_legend_result(self):
        """LegendExpansionResult should store abbreviation and expansion."""
        result = LegendExpansionResult(
            content="Imperator Caesar Augustus",
            confidence=0.95,
            cost_usd=0.0,
            model_used="mock",
            abbreviated="IMP CAES AVG",
            expanded="Imperator Caesar Augustus",
        )
        assert result.abbreviated == "IMP CAES AVG"
        assert result.expanded == "Imperator Caesar Augustus"


class TestProvenanceParseResult:
    """Tests for ProvenanceParseResult."""
    
    def test_provenance_chain(self):
        """ProvenanceParseResult should store chain."""
        entries = [
            ProvenanceEntry(
                source="Heritage",
                source_type="auction",
                year=2022,
                sale="Sale 100",
                lot="234"
            ),
            ProvenanceEntry(
                source="Hunt Collection",
                source_type="collection",
                year=1990,
            ),
        ]
        result = ProvenanceParseResult(
            content="{}",
            confidence=0.88,
            cost_usd=0.0,
            model_used="mock",
            raw_text="Ex Heritage...",
            provenance_chain=entries,
            earliest_known=1990,
        )
        assert len(result.provenance_chain) == 2
        assert result.earliest_known == 1990


class TestAuctionParseResult:
    """Tests for AuctionParseResult."""
    
    def test_auction_fields(self):
        """AuctionParseResult should store extracted fields."""
        result = AuctionParseResult(
            content="{}",
            confidence=0.85,
            cost_usd=0.0,
            model_used="mock",
            raw_text="Trajan AR Denarius...",
            issuer="Trajan",
            denomination="Denarius",
            metal="silver",
            mint="Rome",
            year_start=103,
            year_end=111,
            weight_g=3.15,
            diameter_mm=19.0,
            obverse_legend="IMP TRAIANO AVG",
            references=["RIC II 118", "RSC 76"],
        )
        assert result.issuer == "Trajan"
        assert result.metal == "silver"
        assert result.year_start == 103
        assert len(result.references) == 2


# =============================================================================
# ENRICHMENT TYPES TESTS
# =============================================================================

class TestEnrichmentDiff:
    """Tests for EnrichmentDiff."""
    
    def test_add_safe_fill(self):
        """add_safe_fill should add to safe_fills dict."""
        diff = EnrichmentDiff()
        diff.add_safe_fill("issuer", "Augustus", "vocab_normalize")
        
        assert "issuer" in diff.safe_fills
        assert diff.safe_fills["issuer"] == "Augustus"
        assert len(diff.notes) == 1
    
    def test_add_conflict(self):
        """add_conflict should add to conflicts dict."""
        diff = EnrichmentDiff()
        diff.add_conflict(
            field_name="issuer",
            current="IMP CAES",
            suggested="Augustus",
            reason="LLM normalized abbreviation",
            confidence=0.85
        )
        
        assert "issuer" in diff.conflicts
        assert diff.conflicts["issuer"]["current"] == "IMP CAES"
        assert diff.conflicts["issuer"]["suggested"] == "Augustus"
        assert diff.conflicts["issuer"]["confidence"] == 0.85
    
    def test_to_dict(self):
        """to_dict should serialize properly."""
        diff = EnrichmentDiff()
        diff.add_safe_fill("mint", "Rome", "llm")
        diff.warnings.append("Low confidence")
        
        d = diff.to_dict()
        assert "safe_fills" in d
        assert "conflicts" in d
        assert "warnings" in d


class TestEnrichmentResult:
    """Tests for EnrichmentResult."""
    
    def test_enrichment_result(self):
        """EnrichmentResult should aggregate diff and metadata."""
        diff = EnrichmentDiff()
        diff.add_safe_fill("issuer", "Augustus", "llm")
        
        result = EnrichmentResult(
            coin_id=42,
            diff=diff,
            total_cost_usd=0.002,
            tasks_completed=["vocab_normalize"],
            tasks_skipped=[],
            errors=[],
            request_id="abc-123"
        )
        
        assert result.coin_id == 42
        assert result.total_cost_usd == 0.002
        assert result.has_safe_fills is True
        assert result.has_conflicts is False
    
    def test_has_conflicts(self):
        """has_conflicts should detect conflicts."""
        diff = EnrichmentDiff()
        diff.add_conflict("x", "a", "b", "r", 0.5)
        
        result = EnrichmentResult(
            coin_id=1, diff=diff, total_cost_usd=0,
            tasks_completed=[], tasks_skipped=[], errors=[]
        )
        
        assert result.has_conflicts is True
    
    def test_to_dict(self):
        """to_dict should include all fields."""
        diff = EnrichmentDiff()
        result = EnrichmentResult(
            coin_id=1, diff=diff, total_cost_usd=0.001,
            tasks_completed=["t1"], tasks_skipped=["t2"],
            errors=["e1"], request_id="xyz"
        )
        
        d = result.to_dict()
        assert d["coin_id"] == 1
        assert d["request_id"] == "xyz"
        assert "has_conflicts" in d


# =============================================================================
# FUZZY MATCH TESTS
# =============================================================================

class TestFuzzyMatch:
    """Tests for FuzzyMatch value object."""
    
    def test_fuzzy_match(self):
        """FuzzyMatch should store match info."""
        match = FuzzyMatch(
            canonical_name="Augustus",
            score=0.85,
            vocab_type="issuer",
            vocab_id=1
        )
        assert match.canonical_name == "Augustus"
        assert match.score == 0.85
        assert match.vocab_type == "issuer"
        assert match.vocab_id == 1
    
    def test_frozen(self):
        """FuzzyMatch should be immutable."""
        match = FuzzyMatch("Augustus", 0.85, "issuer", 1)
        with pytest.raises(AttributeError):
            match.score = 0.9  # type: ignore


# =============================================================================
# P1 RESULT TYPES TESTS
# =============================================================================

class TestCoinIdentificationResult:
    """Tests for CoinIdentificationResult."""
    
    def test_identification_result(self):
        """CoinIdentificationResult should store identification."""
        result = CoinIdentificationResult(
            content="{}",
            confidence=0.85,
            cost_usd=0.01,
            model_used="gemini-pro",
            ruler="Trajan",
            denomination="Denarius",
            mint="Rome",
            date_range="103-111 AD",
            suggested_references=["RIC II 118"]
        )
        assert result.ruler == "Trajan"
        assert len(result.suggested_references) == 1


class TestReferenceValidationResult:
    """Tests for ReferenceValidationResult."""
    
    def test_valid_reference(self):
        """ReferenceValidationResult for valid reference."""
        result = ReferenceValidationResult(
            content="{}",
            confidence=0.95,
            cost_usd=0.0,
            model_used="mock",
            reference="RIC II 207",
            is_valid=True,
            normalized="RIC II 207",
            alternatives=["RSC 253"],
            notes="Cross-ref matches"
        )
        assert result.is_valid is True
        assert "RSC 253" in result.alternatives
    
    def test_invalid_reference(self):
        """ReferenceValidationResult for invalid reference."""
        result = ReferenceValidationResult(
            content="{}",
            confidence=0.8,
            cost_usd=0.0,
            model_used="mock",
            reference="RIC XXIV 9999",
            is_valid=False,
            normalized="",
            alternatives=[],
            notes="Volume XXIV does not exist"
        )
        assert result.is_valid is False


class TestSearchAssistResult:
    """Tests for SearchAssistResult."""
    
    def test_search_result(self):
        """SearchAssistResult should store parsed query."""
        result = SearchAssistResult(
            content="{}",
            confidence=0.85,
            cost_usd=0.0,
            model_used="mock",
            query="Flavian silver",
            extracted_keywords=["Flavian", "silver"],
            suggested_filters={"metal": "silver"},
            interpretation="Silver coins from Flavian dynasty",
            needs_clarification=False,
        )
        assert result.query == "Flavian silver"
        assert result.suggested_filters.get("metal") == "silver"
        assert result.needs_clarification is False
