"""Integration tests for catalog parse API (POST /api/v2/catalog/parse, GET /api/v2/catalog/systems)."""
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


@pytest.mark.integration
def test_parse_sng_returns_ref_with_collection(client: TestClient):
    """POST /api/v2/catalog/parse with SNG Cop 123 returns ref with catalog SNG and collection Cop."""
    r = client.post("/api/v2/catalog/parse", json={"raw": "SNG Cop 123"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ref") is not None
    assert data["ref"]["catalog"] == "SNG"
    assert data["ref"]["number"] == "123"
    assert data["ref"]["collection"] == "Cop"
    assert data.get("confidence", 0) >= 0


@pytest.mark.integration
def test_parse_bmcrr_cohen_calico_response_shape(client: TestClient):
    """POST /api/v2/catalog/parse with BMCRR, Cohen, Calicó returns ref with expected shape."""
    cases = [
        ("BMCRR 456", "BMCRR", "456"),
        ("Cohen 382a", "Cohen", "382a"),
        ("Calicó 123", "Calicó", "123"),
    ]
    for raw, expected_catalog, expected_number in cases:
        r = client.post("/api/v2/catalog/parse", json={"raw": raw})
        assert r.status_code == 200, f"{raw}: {r.text}"
        data = r.json()
        assert data.get("ref") is not None, raw
        assert data["ref"]["catalog"] == expected_catalog, raw
        assert expected_number in (data["ref"].get("number") or ""), raw


@pytest.mark.integration
def test_get_catalog_systems_includes_new_catalogs(client: TestClient):
    """GET /api/v2/catalog/systems returns all supported catalogs including DOC, BMCRR, SNG, Cohen, Calicó."""
    r = client.get("/api/v2/catalog/systems")
    assert r.status_code == 200, r.text
    systems = r.json()
    for key in ["ric", "rpc", "doc", "bmcrr", "bmcre", "sng", "cohen", "calico", "sear", "sydenham"]:
        assert key in systems, f"Missing system: {key}"
    assert systems.get("sng") == "SNG"
    assert systems.get("bmcrr") == "BMCRR"
    assert systems.get("cohen") == "Cohen"
    assert systems.get("calico") == "Calicó"
