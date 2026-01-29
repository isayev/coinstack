"""
Integration tests for coins API (create/update with optional weight_g).
"""
import pytest
from fastapi.testclient import TestClient

from src.infrastructure.web.main import create_app
from src.infrastructure.web.dependencies import get_db


@pytest.fixture
def app(db_session):
    def override_get_db():
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_create_coin_without_weight(client: TestClient):
    """POST /api/v2/coins with no weight_g (e.g. slabbed) returns 201 and coin has null weight."""
    payload = {
        "category": "roman_imperial",
        "metal": "silver",
        "diameter_mm": 18.0,
        "issuer": "Augustus",
        "grading_state": "slabbed",
        "grade": "VF",
        "grade_service": "ngc",
        "certification": "123456",
    }
    # Omit weight_g entirely
    r = client.post("/api/v2/coins", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert float(data["dimensions"]["diameter_mm"]) == 18.0
    assert data["dimensions"].get("weight_g") is None


def test_create_coin_with_weight(client: TestClient):
    """POST /api/v2/coins with weight_g still works."""
    payload = {
        "category": "roman_imperial",
        "metal": "silver",
        "weight_g": 3.5,
        "diameter_mm": 18.0,
        "issuer": "Trajan",
        "grading_state": "raw",
        "grade": "VF",
    }
    r = client.post("/api/v2/coins", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert float(data["dimensions"]["weight_g"]) == 3.5
    assert float(data["dimensions"]["diameter_mm"]) == 18.0
