"""Unit tests for dies router."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from src.domain.coin import Die, DieSide, DieState
from src.infrastructure.web.main import create_app
from src.infrastructure.web.dependencies import get_die_repo

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_die():
    """Create mock die."""
    return Die(
        id=1,
        die_identifier="RIC_207_OBV_A",
        die_side=DieSide.OBVERSE,
        die_state=DieState.EARLY,
        has_die_crack=False,
        has_die_clash=False,
        die_rotation_angle=0,
        reference_system="RIC",
        reference_number="207",
        notes="Test die"
    )


@pytest.fixture
def mock_repo():
    """Create mock die repository."""
    return MagicMock()


@pytest.fixture
def client(mock_repo):
    """Create test client with mocked repository."""
    app = create_app()
    app.dependency_overrides[get_die_repo] = lambda: mock_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


# =============================================================================
# LIST DIES
# =============================================================================

def test_list_dies_returns_all(client, mock_repo, mock_die):
    """Test listing dies returns all dies."""
    mock_repo.list_all.return_value = [mock_die]

    response = client.get("/api/v2/dies")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["die_identifier"] == "RIC_207_OBV_A"
    assert data[0]["die_side"] == "obverse"


def test_list_dies_with_pagination(client, mock_repo):
    """Test listing dies with custom pagination."""
    mock_repo.list_all.return_value = []

    response = client.get("/api/v2/dies?skip=20&limit=50")

    assert response.status_code == status.HTTP_200_OK
    mock_repo.list_all.assert_called_once_with(skip=20, limit=50)


def test_list_dies_uses_default_limit(client, mock_repo):
    """Test listing dies uses default limit when not specified."""
    mock_repo.list_all.return_value = []

    response = client.get("/api/v2/dies")

    assert response.status_code == status.HTTP_200_OK
    # Default limit is 100 (from pagination config)
    mock_repo.list_all.assert_called_once_with(skip=0, limit=100)


def test_list_dies_rejects_zero_limit(client, mock_repo):
    """Test that limit=0 is rejected."""
    response = client.get("/api/v2/dies?limit=0")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "must be greater than 0" in response.json()["detail"].lower()


def test_list_dies_rejects_limit_exceeding_max(client, mock_repo):
    """Test that limit exceeding maximum is rejected."""
    response = client.get("/api/v2/dies?limit=1000")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds maximum" in response.json()["detail"].lower()


# =============================================================================
# CREATE DIE
# =============================================================================

def test_create_die_success(client, mock_repo, mock_die):
    """Test successful die creation."""
    mock_repo.create.return_value = mock_die

    request_data = {
        "die_identifier": "RIC_207_OBV_A",
        "die_side": "obverse",
        "die_state": "early",
        "has_die_crack": False,
        "has_die_clash": False,
        "reference_system": "RIC",
        "reference_number": "207",
        "notes": "Test die"
    }

    response = client.post("/api/v2/dies", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["die_identifier"] == "RIC_207_OBV_A"
    assert data["die_side"] == "obverse"
    assert data["die_state"] == "early"


def test_create_die_with_invalid_side(client, mock_repo):
    """Test that invalid die_side is rejected."""
    request_data = {
        "die_identifier": "TEST_001",
        "die_side": "invalid_side"
    }

    response = client.post("/api/v2/dies", json=request_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid die_side" in response.json()["detail"].lower()


def test_create_die_with_invalid_state(client, mock_repo):
    """Test that invalid die_state is rejected."""
    request_data = {
        "die_identifier": "TEST_001",
        "die_state": "invalid_state"
    }

    response = client.post("/api/v2/dies", json=request_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid die_state" in response.json()["detail"].lower()


def test_create_die_duplicate_identifier(client, mock_repo):
    """Test that duplicate die identifier returns 409."""
    mock_repo.create.side_effect = Exception("UNIQUE constraint failed")

    request_data = {
        "die_identifier": "DUPLICATE_001",
        "die_side": "obverse"
    }

    response = client.post("/api/v2/dies", json=request_data)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"].lower()


# =============================================================================
# SEARCH DIES
# =============================================================================

def test_search_dies_by_identifier(client, mock_repo, mock_die):
    """Test searching dies by identifier."""
    mock_repo.search.return_value = [mock_die]

    response = client.get("/api/v2/dies/search?q=RIC_207")

    if response.status_code != status.HTTP_200_OK:
        print(f"Response: {response.status_code}, Body: {response.json()}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["die_identifier"] == "RIC_207_OBV_A"


def test_search_dies_with_side_filter(client, mock_repo, mock_die):
    """Test searching dies with die_side filter."""
    mock_repo.search.return_value = [mock_die]

    response = client.get("/api/v2/dies/search?q=RIC&die_side=obverse")

    assert response.status_code == status.HTTP_200_OK
    mock_repo.search.assert_called_once_with(query="RIC", die_side="obverse")


def test_search_dies_requires_query(client, mock_repo):
    """Test that search requires query parameter."""
    response = client.get("/api/v2/dies/search")

    # FastAPI validation should reject missing required query param
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# GET DIE BY ID
# =============================================================================

def test_get_die_by_id_success(client, mock_repo, mock_die):
    """Test getting die by ID."""
    mock_repo.get_by_id.return_value = mock_die

    response = client.get("/api/v2/dies/1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1
    assert data["die_identifier"] == "RIC_207_OBV_A"


def test_get_die_by_id_not_found(client, mock_repo):
    """Test getting non-existent die returns 404."""
    mock_repo.get_by_id.return_value = None

    response = client.get("/api/v2/dies/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# =============================================================================
# UPDATE DIE
# =============================================================================

def test_update_die_success(client, mock_repo, mock_die):
    """Test successful die update."""
    updated_die = Die(
        id=1,
        die_identifier="RIC_207_OBV_A_UPDATED",
        die_side=DieSide.OBVERSE,
        die_state=DieState.MIDDLE,
        has_die_crack=True,
        has_die_clash=False,
        die_rotation_angle=0,
        reference_system="RIC",
        reference_number="207",
        notes="Updated notes"
    )
    mock_repo.update.return_value = updated_die

    request_data = {
        "die_identifier": "RIC_207_OBV_A_UPDATED",
        "die_state": "middle",
        "has_die_crack": True,
        "notes": "Updated notes"
    }

    response = client.put("/api/v2/dies/1", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["die_identifier"] == "RIC_207_OBV_A_UPDATED"
    assert data["die_state"] == "middle"
    assert data["has_die_crack"] is True


def test_update_die_not_found(client, mock_repo):
    """Test updating non-existent die returns 404."""
    mock_repo.update.return_value = None

    request_data = {
        "die_identifier": "UPDATED_001"
    }

    response = client.put("/api/v2/dies/999", json=request_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_die_duplicate_identifier(client, mock_repo):
    """Test updating to duplicate identifier returns 409."""
    mock_repo.update.side_effect = Exception("UNIQUE constraint failed")

    request_data = {
        "die_identifier": "DUPLICATE_001"
    }

    response = client.put("/api/v2/dies/1", json=request_data)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"].lower()


# =============================================================================
# DELETE DIE
# =============================================================================

def test_delete_die_success(client, mock_repo):
    """Test successful die deletion."""
    mock_repo.delete.return_value = True

    response = client.delete("/api/v2/dies/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_repo.delete.assert_called_once_with(1)


def test_delete_die_not_found(client, mock_repo):
    """Test deleting non-existent die returns 404."""
    mock_repo.delete.return_value = False

    response = client.delete("/api/v2/dies/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()
