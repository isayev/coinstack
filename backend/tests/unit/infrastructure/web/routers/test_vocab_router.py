import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session
from src.infrastructure.web.routers.vocab import router
from src.infrastructure.web.dependencies import get_db

# Mock DB Dependency
mock_session = MagicMock()
def override_get_db():
    try:
        yield mock_session
    finally:
        pass

app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_list_issuers(monkeypatch):
    # Mock database query
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    
    mock_issuer = MagicMock()
    mock_issuer.id = 1
    mock_issuer.canonical_name = "Augustus"
    mock_issuer.nomisma_id = "augustus"
    mock_issuer.issuer_type = "emperor"
    mock_issuer.reign_start = -27
    mock_issuer.reign_end = 14
    
    mock_query.filter.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [mock_issuer]
    mock_query.count.return_value = 1

    response = client.get("/api/vocab/issuers")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["canonical_name"] == "Augustus"

def test_normalize_issuer():
    with patch("src.infrastructure.web.routers.vocab.VocabNormalizer") as MockNormalizer:
        instance = MockNormalizer.return_value
        instance.normalize_issuer.return_value = MagicMock(
            success=True, 
            canonical_id=1, 
            canonical_name="Augustus",
            confidence=1.0,
            method="exact_match",
            alternatives=[],
            needs_review=False,
            details={}
        )
        instance.normalize_issuer.return_value.method = MagicMock()
        instance.normalize_issuer.return_value.method.value = "exact_match"
        
        response = client.post("/api/vocab/normalize/issuer", params={"raw": "Augustus"})
        
        assert response.status_code == 200
        assert response.json()["canonical_name"] == "Augustus"

def test_sync_trigger():
    # Mock BackgroundTasks and Service
    with patch("src.infrastructure.web.routers.vocab.VocabSyncService") as MockSync:
        instance = MockSync.return_value
        instance.sync_nomisma_issuers = AsyncMock() # Fix: Make it async
        
        response = client.post("/api/vocab/sync/nomisma")
        assert response.status_code == 202
        assert response.json()["status"] == "started"
