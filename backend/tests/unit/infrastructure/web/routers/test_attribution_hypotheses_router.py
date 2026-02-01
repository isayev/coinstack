"""Unit tests for attribution hypotheses router."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from decimal import Decimal

from src.domain.coin import (
    AttributionHypothesis, AttributionCertainty, Coin,
    Category, Metal, Dimensions, Attribution, GradingDetails, GradingState
)
from decimal import Decimal
from src.infrastructure.web.main import create_app
from src.infrastructure.web.routers.attribution_hypotheses import get_attribution_hypothesis_repo
from src.infrastructure.web.dependencies import get_coin_repo

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_coin():
    """Create mock coin."""
    return Coin(
        id=1,
        category=Category.ROMAN_IMPERIAL,
        metal=Metal.SILVER,
        dimensions=Dimensions(diameter_mm=Decimal("20.0"), weight_g=Decimal("3.5")),
        attribution=Attribution(issuer="Augustus"),
        grading=GradingDetails(grading_state=GradingState.RAW, grade="VF")
    )


@pytest.fixture
def mock_hypothesis():
    """Create mock attribution hypothesis."""
    return AttributionHypothesis(
        id=1,
        coin_id=1,
        hypothesis_rank=1,
        issuer="Augustus",
        issuer_confidence=AttributionCertainty.CERTAIN,
        mint="Rome",
        mint_confidence=AttributionCertainty.PROBABLE,
        year_start=-27,
        year_end=-14,
        date_confidence=AttributionCertainty.PROBABLE,
        denomination="Denarius",
        denomination_confidence=AttributionCertainty.CERTAIN,
        overall_certainty=AttributionCertainty.CERTAIN,
        confidence_score=Decimal("0.95"),
        attribution_notes="Primary attribution",  # Correct field name
        reference_support="RIC I Augustus 207",
        source="expert_opinion"
    )


@pytest.fixture
def mock_repo():
    """Create mock attribution hypothesis repository."""
    return MagicMock()


@pytest.fixture
def mock_coin_repo(mock_coin):
    """Create mock coin repository."""
    repo = MagicMock()
    repo.get_by_id.return_value = mock_coin
    return repo


@pytest.fixture
def client(mock_repo, mock_coin_repo):
    """Create test client with mocked repositories."""
    app = create_app()
    app.dependency_overrides[get_attribution_hypothesis_repo] = lambda: mock_repo
    app.dependency_overrides[get_coin_repo] = lambda: mock_coin_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


# =============================================================================
# LIST HYPOTHESES
# =============================================================================

def test_list_hypotheses_for_coin(client, mock_repo, mock_hypothesis):
    """Test listing hypotheses for a coin."""
    mock_repo.get_by_coin_id.return_value = [mock_hypothesis]

    response = client.get("/api/v2/coins/1/attribution-hypotheses")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["hypothesis_rank"] == 1
    assert data[0]["issuer"] == "Augustus"


def test_list_hypotheses_returns_empty_for_coin_with_no_hypotheses(client, mock_repo):
    """Test listing hypotheses returns empty list for coin with none."""
    mock_repo.get_by_coin_id.return_value = []

    response = client.get("/api/v2/coins/1/attribution-hypotheses")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


# =============================================================================
# CREATE HYPOTHESIS
# =============================================================================

def test_create_hypothesis_success(client, mock_repo, mock_hypothesis):
    """Test successful hypothesis creation."""
    mock_repo.create.return_value = mock_hypothesis

    request_data = {
        "coin_id": 1,
        "hypothesis_rank": 1,
        "issuer": "Augustus",
        "issuer_confidence": "certain",
        "mint": "Rome",
        "mint_confidence": "probable",
        "year_start": -27,
        "year_end": -14,
        "date_confidence": "probable",
        "denomination": "Denarius",
        "denomination_confidence": "certain",
        "attribution_notes": "Primary attribution"
    }

    response = client.post("/api/v2/coins/1/attribution-hypotheses", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["issuer"] == "Augustus"
    assert data["issuer_confidence"] == "certain"
    assert data["hypothesis_rank"] == 1


def test_create_hypothesis_with_invalid_confidence(client, mock_repo):
    """Test that invalid confidence enum is rejected."""
    request_data = {
        "coin_id": 1,
        "hypothesis_rank": 1,
        "issuer": "Augustus",
        "issuer_confidence": "invalid_confidence"
    }

    response = client.post("/api/v2/coins/1/attribution-hypotheses", json=request_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid" in response.json()["detail"].lower()
    assert "confidence" in response.json()["detail"].lower()


def test_create_hypothesis_duplicate_rank(client, mock_repo):
    """Test that duplicate rank for same coin returns 409."""
    mock_repo.create.side_effect = Exception("UNIQUE constraint failed")

    request_data = {
        "coin_id": 1,
        "hypothesis_rank": 1,
        "issuer": "Augustus"
    }

    response = client.post("/api/v2/coins/1/attribution-hypotheses", json=request_data)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"].lower()


# =============================================================================
# GET HYPOTHESIS BY ID
# =============================================================================

def test_get_hypothesis_by_id_success(client, mock_repo, mock_hypothesis):
    """Test getting hypothesis by ID."""
    mock_repo.get_by_id.return_value = mock_hypothesis

    response = client.get("/api/v2/attribution-hypotheses/1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1
    assert data["issuer"] == "Augustus"


def test_get_hypothesis_by_id_not_found(client, mock_repo):
    """Test getting non-existent hypothesis returns 404."""
    mock_repo.get_by_id.return_value = None

    response = client.get("/api/v2/attribution-hypotheses/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# =============================================================================
# GET PRIMARY HYPOTHESIS
# =============================================================================

def test_get_primary_hypothesis_success(client, mock_repo, mock_hypothesis):
    """Test getting primary hypothesis (rank=1) for coin."""
    mock_repo.get_primary.return_value = mock_hypothesis

    response = client.get("/api/v2/coins/1/attribution-hypotheses/primary")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["hypothesis_rank"] == 1
    assert data["issuer"] == "Augustus"


def test_get_primary_hypothesis_not_found(client, mock_repo):
    """Test getting primary hypothesis when none exists returns 404."""
    mock_repo.get_primary.return_value = None

    response = client.get("/api/v2/coins/1/attribution-hypotheses/primary")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "no primary" in response.json()["detail"].lower()


# =============================================================================
# SET PRIMARY HYPOTHESIS
# =============================================================================

def test_set_primary_hypothesis_success(client, mock_repo, mock_hypothesis):
    """Test promoting hypothesis to primary (rank=1)."""
    mock_repo.set_primary.return_value = mock_hypothesis

    response = client.post("/api/v2/attribution-hypotheses/2/set-primary")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["hypothesis_rank"] == 1
    mock_repo.set_primary.assert_called_once_with(2)


def test_set_primary_hypothesis_not_found(client, mock_repo):
    """Test promoting non-existent hypothesis returns 404."""
    mock_repo.set_primary.side_effect = ValueError("Hypothesis 999 not found")

    response = client.post("/api/v2/attribution-hypotheses/999/set-primary")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# =============================================================================
# UPDATE HYPOTHESIS
# =============================================================================

def test_update_hypothesis_success(client, mock_repo, mock_hypothesis):
    """Test successful hypothesis update."""
    # Mock get_by_id to return existing hypothesis first
    mock_repo.get_by_id.return_value = mock_hypothesis

    updated_hypothesis = AttributionHypothesis(
        id=1,
        coin_id=1,
        hypothesis_rank=1,
        issuer="Augustus",
        issuer_confidence=AttributionCertainty.PROBABLE,  # Changed
        mint="Rome",
        mint_confidence=AttributionCertainty.PROBABLE,
        year_start=-27,
        year_end=-14,
        date_confidence=AttributionCertainty.PROBABLE,
        denomination="Denarius",
        denomination_confidence=AttributionCertainty.CERTAIN,
        overall_certainty=AttributionCertainty.PROBABLE,
        confidence_score=Decimal("0.85"),
        attribution_notes="Updated notes",
        reference_support="RIC I Augustus 207",
        source="expert_opinion"
    )
    mock_repo.update.return_value = updated_hypothesis

    request_data = {
        "issuer_confidence": "probable",
        "attribution_notes": "Updated notes"
    }

    response = client.put("/api/v2/attribution-hypotheses/1", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["issuer_confidence"] == "probable"
    assert data["attribution_notes"] == "Updated notes"


def test_update_hypothesis_not_found(client, mock_repo):
    """Test updating non-existent hypothesis returns 404."""
    mock_repo.get_by_id.return_value = None

    request_data = {
        "attribution_notes": "Updated notes"
    }

    response = client.put("/api/v2/attribution-hypotheses/999", json=request_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_hypothesis_duplicate_rank(client, mock_repo, mock_hypothesis):
    """Test updating to duplicate rank returns 409."""
    # Mock get_by_id to return existing hypothesis first
    mock_repo.get_by_id.return_value = mock_hypothesis
    mock_repo.update.side_effect = Exception("UNIQUE constraint failed")

    request_data = {
        "hypothesis_rank": 1
    }

    response = client.put("/api/v2/attribution-hypotheses/2", json=request_data)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"].lower()


# =============================================================================
# DELETE HYPOTHESIS
# =============================================================================

def test_delete_hypothesis_success(client, mock_repo):
    """Test successful hypothesis deletion."""
    mock_repo.delete.return_value = True

    response = client.delete("/api/v2/attribution-hypotheses/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_repo.delete.assert_called_once_with(1)


def test_delete_hypothesis_not_found(client, mock_repo):
    """Test deleting non-existent hypothesis returns 404."""
    mock_repo.delete.return_value = False

    response = client.delete("/api/v2/attribution-hypotheses/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()
