"""
Unit tests for P2 LLM domain types.

Tests AttributionAssistResult, LegendTranscribeResult, CatalogParseResult,
ConditionObservationsResult, and related helpers.
"""

import pytest
from src.domain.llm import (
    LLMCapability,
    AttributionSuggestion,
    AttributionAssistResult,
    LegendTranscribeResult,
    CatalogParseResult,
    ConditionObservationsResult,
)


# =============================================================================
# CAPABILITY HELPERS TESTS
# =============================================================================

class TestLLMCapabilityP2Helpers:
    """Tests for P2 capability helper methods."""
    
    def test_p2_capabilities_returns_correct_list(self):
        """p2_capabilities() returns all P2 capabilities."""
        p2 = LLMCapability.p2_capabilities()
        
        assert len(p2) == 4
        assert LLMCapability.ATTRIBUTION_ASSIST in p2
        assert LLMCapability.LEGEND_TRANSCRIBE in p2
        assert LLMCapability.CATALOG_PARSE in p2
        assert LLMCapability.CONDITION_OBSERVATIONS in p2
    
    def test_p2_capabilities_are_distinct_from_p0_p1(self):
        """P2 capabilities don't overlap with P0/P1."""
        p0 = set(LLMCapability.p0_capabilities())
        p1 = set(LLMCapability.p1_capabilities())
        p2 = set(LLMCapability.p2_capabilities())
        
        assert p0.isdisjoint(p2)
        assert p1.isdisjoint(p2)
    
    def test_p3_capabilities_returns_correct_list(self):
        """p3_capabilities() returns all P3 capabilities."""
        p3 = LLMCapability.p3_capabilities()
        
        assert len(p3) == 4
        assert LLMCapability.SEARCH_ASSIST in p3
        assert LLMCapability.COLLECTION_INSIGHTS in p3
        assert LLMCapability.DESCRIPTION_GENERATE in p3
        assert LLMCapability.DIE_STUDY in p3


# =============================================================================
# ATTRIBUTION SUGGESTION TESTS
# =============================================================================

class TestAttributionSuggestion:
    """Tests for AttributionSuggestion value object."""
    
    def test_create_suggestion(self):
        """Can create attribution suggestion."""
        suggestion = AttributionSuggestion(
            attribution="Caracalla, Denarius, Rome, 213 AD",
            reference="RIC IV 223",
            confidence=0.85,
            reasoning=["Legend matches", "Weight consistent"],
        )
        
        assert suggestion.attribution == "Caracalla, Denarius, Rome, 213 AD"
        assert suggestion.reference == "RIC IV 223"
        assert suggestion.confidence == 0.85
        assert len(suggestion.reasoning) == 2
    
    def test_suggestion_is_frozen(self):
        """AttributionSuggestion is immutable."""
        suggestion = AttributionSuggestion(
            attribution="Test",
            reference="RIC 1",
            confidence=0.5,
        )
        
        with pytest.raises(AttributeError):
            suggestion.confidence = 0.9  # type: ignore


# =============================================================================
# ATTRIBUTION ASSIST RESULT TESTS
# =============================================================================

class TestAttributionAssistResult:
    """Tests for AttributionAssistResult."""
    
    def test_create_result(self):
        """Can create attribution assist result."""
        suggestion = AttributionSuggestion(
            attribution="Trajan, Denarius",
            reference="RIC II 207",
            confidence=0.9,
        )
        
        result = AttributionAssistResult(
            content='{"test": "data"}',
            confidence=0.85,
            cost_usd=0.01,
            model_used="test-model",
            suggestions=[suggestion],
            questions_to_resolve=["What is the reverse legend?"],
        )
        
        assert len(result.suggestions) == 1
        assert result.suggestions[0].reference == "RIC II 207"
        assert len(result.questions_to_resolve) == 1
    
    def test_empty_suggestions(self):
        """Result can have empty suggestions."""
        result = AttributionAssistResult(
            content="{}",
            confidence=0.1,
            cost_usd=0.0,
            model_used="mock",
            suggestions=[],
            questions_to_resolve=["Need more information"],
        )
        
        assert len(result.suggestions) == 0
        assert result.needs_review  # Low confidence


# =============================================================================
# LEGEND TRANSCRIBE RESULT TESTS
# =============================================================================

class TestLegendTranscribeResult:
    """Tests for LegendTranscribeResult."""
    
    def test_create_result(self):
        """Can create legend transcribe result."""
        result = LegendTranscribeResult(
            content='{"test": "data"}',
            confidence=0.9,
            cost_usd=0.02,
            model_used="gemini-pro",
            obverse_legend="IMP TRAIANO AVG GER",
            obverse_legend_expanded="Imperator Traiano Augustus Germanicus",
            reverse_legend="COS V P P",
            reverse_legend_expanded="Consul V Pater Patriae",
        )
        
        assert result.obverse_legend == "IMP TRAIANO AVG GER"
        assert "Imperator" in result.obverse_legend_expanded
    
    def test_result_with_uncertain_portions(self):
        """Result can include uncertain portions."""
        result = LegendTranscribeResult(
            content="{}",
            confidence=0.6,
            cost_usd=0.01,
            model_used="mock",
            obverse_legend="IMP [...] AVG",
            uncertain_portions=["Central text worn"],
        )
        
        assert "[...]" in result.obverse_legend
        assert len(result.uncertain_portions) == 1
        assert result.needs_review  # Low confidence
    
    def test_result_with_exergue(self):
        """Result can include exergue content."""
        result = LegendTranscribeResult(
            content="{}",
            confidence=0.8,
            cost_usd=0.01,
            model_used="mock",
            exergue="SMANT",
        )
        
        assert result.exergue == "SMANT"


# =============================================================================
# CATALOG PARSE RESULT TESTS
# =============================================================================

class TestCatalogParseResult:
    """Tests for CatalogParseResult."""
    
    def test_create_ric_result(self):
        """Can create catalog parse result for RIC."""
        result = CatalogParseResult(
            content='{"catalog_system": "RIC"}',
            confidence=0.95,
            cost_usd=0.001,
            model_used="phi3",
            raw_reference="RIC II 207",
            catalog_system="RIC",
            volume="II",
            number="207",
            issuer="Trajan",
        )
        
        assert result.catalog_system == "RIC"
        assert result.volume == "II"
        assert result.number == "207"
        assert result.issuer == "Trajan"
    
    def test_create_crawford_result(self):
        """Can create catalog parse result for Crawford."""
        result = CatalogParseResult(
            content="{}",
            confidence=0.92,
            cost_usd=0.001,
            model_used="mock",
            raw_reference="Crawford 443/1",
            catalog_system="Crawford",
            number="443/1",
            issuer="L. Hostilius Saserna",
            alternatives=["RRC 443/1"],
        )
        
        assert result.catalog_system == "Crawford"
        assert result.volume is None
        assert len(result.alternatives) == 1
    
    def test_result_with_alternatives(self):
        """Result can include cross-reference alternatives."""
        result = CatalogParseResult(
            content="{}",
            confidence=0.9,
            cost_usd=0.001,
            model_used="mock",
            raw_reference="RIC II 207",
            catalog_system="RIC",
            number="207",
            alternatives=["RSC 253", "Sear 3129"],
        )
        
        assert len(result.alternatives) == 2
        assert "RSC 253" in result.alternatives


# =============================================================================
# CONDITION OBSERVATIONS RESULT TESTS
# =============================================================================

class TestConditionObservationsResult:
    """Tests for ConditionObservationsResult."""
    
    def test_create_result(self):
        """Can create condition observations result."""
        result = ConditionObservationsResult(
            content='{"wear_observations": "..."}',
            confidence=0.8,
            cost_usd=0.03,
            model_used="gemini-pro",
            wear_observations="High points show moderate wear",
            surface_notes="Gray cabinet toning",
            strike_quality="Well-centered",
            notable_features=["Banker's mark"],
        )
        
        assert "moderate wear" in result.wear_observations
        assert "toning" in result.surface_notes
        assert len(result.notable_features) == 1
    
    def test_default_recommendation(self):
        """Default recommendation is professional grading."""
        result = ConditionObservationsResult(
            content="{}",
            confidence=0.7,
            cost_usd=0.01,
            model_used="mock",
        )
        
        assert "Professional grading" in result.recommendation
        assert "sale" in result.recommendation or "insurance" in result.recommendation
    
    def test_result_with_concerns(self):
        """Result can include concerns."""
        result = ConditionObservationsResult(
            content="{}",
            confidence=0.65,
            cost_usd=0.02,
            model_used="mock",
            concerns=[
                "Possible tooling near nose",
                "Edge smoothing may indicate cleaning"
            ],
        )
        
        assert len(result.concerns) == 2
        assert result.needs_review  # Low confidence
    
    def test_no_grade_terminology_allowed(self):
        """
        Condition observations should NOT contain grade terminology.
        
        This test verifies the data model doesn't have grade fields.
        The actual filtering is done in the service layer.
        """
        result = ConditionObservationsResult(
            content="{}",
            confidence=0.8,
            cost_usd=0.01,
            model_used="mock",
            wear_observations="Moderate wear on high points",
        )
        
        # Verify no grade-related fields exist in the result type
        assert not hasattr(result, "grade")
        assert not hasattr(result, "grade_estimate")
        assert not hasattr(result, "numeric_grade")
        
        # The wear_observations should describe wear, not assign grades
        output = result.wear_observations.upper()
        grade_terms = [" VF", " EF", " AU", " MS", "VERY FINE", "EXTREMELY FINE"]
        for term in grade_terms:
            assert term not in output, f"Grade term '{term}' found in output"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestP2ResultIntegration:
    """Integration tests for P2 result types."""
    
    def test_all_results_inherit_from_llm_result(self):
        """All P2 results inherit confidence validation."""
        from src.domain.llm import LLMResult
        
        results = [
            AttributionAssistResult(
                content="{}", confidence=0.5, cost_usd=0.0, model_used="test"
            ),
            LegendTranscribeResult(
                content="{}", confidence=0.5, cost_usd=0.0, model_used="test"
            ),
            CatalogParseResult(
                content="{}", confidence=0.5, cost_usd=0.0, model_used="test"
            ),
            ConditionObservationsResult(
                content="{}", confidence=0.5, cost_usd=0.0, model_used="test"
            ),
        ]
        
        for result in results:
            assert isinstance(result, LLMResult)
            assert result.confidence == 0.5
    
    def test_invalid_confidence_rejected(self):
        """All P2 results reject invalid confidence."""
        with pytest.raises(ValueError, match="Confidence"):
            AttributionAssistResult(
                content="{}", confidence=1.5, cost_usd=0.0, model_used="test"
            )
        
        with pytest.raises(ValueError, match="Confidence"):
            ConditionObservationsResult(
                content="{}", confidence=-0.1, cost_usd=0.0, model_used="test"
            )
    
    def test_negative_cost_rejected(self):
        """All P2 results reject negative cost."""
        with pytest.raises(ValueError, match="Cost"):
            CatalogParseResult(
                content="{}", confidence=0.5, cost_usd=-0.01, model_used="test"
            )
