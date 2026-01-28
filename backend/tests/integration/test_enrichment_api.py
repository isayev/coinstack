"""
Integration tests for enrichment API endpoints.

- GET/POST /api/v2/audit/enrichments, bulk-apply, apply, auto-apply-empty
- POST /api/catalog/bulk-enrich, GET /api/catalog/job/{id}
- POST /api/v2/import/enrich-preview
"""
import pytest
from fastapi.testclient import TestClient

from src.infrastructure.web.main import create_app
from src.infrastructure.web.dependencies import get_db


@pytest.fixture
def app(db_session):
    """App with conftest's in-memory db_session."""
    def override_get_db():
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# --- Audit enrichments ---


def test_audit_enrichments_list_returns_200_and_shape(client: TestClient):
    """GET /api/v2/audit/enrichments returns paginated shape."""
    r = client.get("/api/v2/audit/enrichments", params={"page": 1, "per_page": 20})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "pages" in data
    assert isinstance(data["items"], list)


def test_audit_enrichments_apply_requires_body(client: TestClient):
    """POST /api/v2/audit/enrichments/apply without body returns 422."""
    r = client.post("/api/v2/audit/enrichments/apply", json={})
    assert r.status_code == 422


def test_audit_enrichments_apply_coin_not_found(client: TestClient):
    """POST /api/v2/audit/enrichments/apply with non-existent coin returns 400 or 404."""
    r = client.post(
        "/api/v2/audit/enrichments/apply",
        json={"coin_id": 999999, "field_name": "issuer", "value": "Augustus"},
    )
    # ApplyEnrichmentService returns failure; router returns 400 with detail
    assert r.status_code in (400, 404)


def test_audit_enrichments_bulk_apply_empty(client: TestClient):
    """POST /api/v2/audit/enrichments/bulk-apply with empty applications returns applied=0."""
    r = client.post(
        "/api/v2/audit/enrichments/bulk-apply",
        json={"applications": []},
    )
    assert r.status_code == 200
    assert r.json()["applied"] == 0


def test_audit_enrichments_auto_apply_empty(client: TestClient):
    """POST /api/v2/audit/enrichments/auto-apply-empty returns 200 and applied count."""
    r = client.post("/api/v2/audit/enrichments/auto-apply-empty")
    assert r.status_code == 200
    data = r.json()
    assert "applied" in data


# --- Catalog bulk enrich ---


def test_catalog_bulk_enrich_returns_job(client: TestClient):
    """POST /api/catalog/bulk-enrich returns job_id, total_coins, status."""
    r = client.post(
        "/api/catalog/bulk-enrich",
        json={"dry_run": True, "max_coins": 5},
    )
    assert r.status_code == 200
    data = r.json()
    assert "job_id" in data
    assert "total_coins" in data
    assert "status" in data
    assert data["status"] == "queued"


def test_catalog_bulk_enrich_with_coin_ids(client: TestClient):
    """POST /api/catalog/bulk-enrich with coin_ids returns job with total = len(coin_ids)."""
    r = client.post(
        "/api/catalog/bulk-enrich",
        json={"coin_ids": [1, 2, 3], "dry_run": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total_coins"] == 3
    job_id = data["job_id"]


def test_catalog_job_status_404_unknown(client: TestClient):
    """GET /api/catalog/job/{id} returns 404 for unknown job."""
    r = client.get("/api/catalog/job/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


# --- Import enrich-preview ---


def test_import_enrich_preview_empty_refs(client: TestClient):
    """POST /api/v2/import/enrich-preview with empty references returns success and empty suggestions."""
    r = client.post(
        "/api/v2/import/enrich-preview",
        json={"references": []},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("success") is True
    assert "suggestions" in data
    assert "lookup_results" in data
    assert data["lookup_results"] == []


def test_import_enrich_preview_with_refs(client: TestClient):
    """POST /api/v2/import/enrich-preview with references returns success, suggestions, lookup_results."""
    r = client.post(
        "/api/v2/import/enrich-preview",
        json={"references": ["RIC I 207"], "context": {}},
    )
    # May succeed or fail depending on OCRE/network; we only assert response shape
    assert r.status_code == 200
    data = r.json()
    assert "success" in data
    assert "suggestions" in data
    assert "lookup_results" in data
    assert isinstance(data["suggestions"], dict)
    assert isinstance(data["lookup_results"], list)
