import pytest
from unittest.mock import MagicMock, patch
from src.infrastructure.services.vocab_normalizer import VocabNormalizer, NormalizationResult
from src.infrastructure.persistence.models_vocab import IssuerModel, IssuerAliasModel

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def normalizer(mock_session):
    return VocabNormalizer(mock_session)

def test_exact_match(normalizer, mock_session):
    mock_issuer = IssuerModel(id=1, canonical_name="Trajan", nomisma_id="trajan")
    mock_session.scalar.return_value = mock_issuer

    result = normalizer.normalize_issuer("Trajan")

    assert result.success
    assert result.canonical_id == 1
    assert result.confidence == 1.0
    assert result.method == "exact_match"

def test_alias_match(normalizer, mock_session):
    # Setup mock for exact match failure then alias match success
    mock_alias = IssuerAliasModel(
        issuer_id=2, 
        normalized_form="imp traiano", 
        issuer=IssuerModel(id=2, canonical_name="Trajan", nomisma_id="trajan")
    )
    
    # Side effect: first call (exact) returns None, second (alias) returns mock_alias
    mock_session.scalar.side_effect = [None, mock_alias]

    result = normalizer.normalize_issuer("IMP TRAIANO")

    assert result.success
    assert result.canonical_id == 2
    assert result.method == "alias_match"

def test_fuzzy_match(normalizer, mock_session):
    # Mock no exact or alias match
    mock_session.scalar.return_value = None
    
    # Mock DB return for cache build
    # We return one issuer and one alias to populate the cache
    mock_issuer = IssuerModel(id=3, canonical_name="Hadrian", nomisma_id="hadrian")
    mock_alias = IssuerAliasModel(id=1, issuer_id=3, normalized_form="hadrianus", alias="Hadrianus")
    
    # execute() is called twice: once for issuers, once for aliases
    mock_result_issuers = MagicMock()
    mock_result_issuers.scalars.return_value.all.return_value = [mock_issuer]
    
    mock_result_aliases = MagicMock()
    mock_result_aliases.scalars.return_value.all.return_value = [mock_alias]
    
    mock_session.execute.side_effect = [mock_result_issuers, mock_result_aliases]
    
    # Mock get() for final retrieval
    mock_session.get.return_value = mock_issuer

    # "Hadrin" is close to "Hadrian" (normalized "hadrian")
    result = normalizer.normalize_issuer("Hadrin")

    assert result.success
    assert result.canonical_id == 3
    assert result.method == "fuzzy_match"
    assert result.confidence > 0.8