import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock, patch
from src.infrastructure.web.routers.series import router
from src.infrastructure.web.dependencies import get_db

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

def test_create_series():
    with patch("src.infrastructure.web.routers.series.SeriesService") as MockService:
        instance = MockService.return_value
        
        # Explicitly set mock attributes to strings for Pydantic
        mock_series = MagicMock()
        mock_series.id = 1
        mock_series.name = "Test"
        mock_series.slug = "test"
        mock_series.series_type = "user_defined"
        mock_series.target_count = 10
        mock_series.is_complete = False
        mock_series.slots = []
        
        instance.create_series.return_value = mock_series
        
        response = client.post("/api/v2/series", json={
            "name": "Test",
            "series_type": "user_defined",
            "target_count": 10
        })
        
        assert response.status_code == 201
        assert response.json()["name"] == "Test"

def test_add_slot():
    with patch("src.infrastructure.web.routers.series.SeriesService") as MockService:
        instance = MockService.return_value
        
        mock_slot = MagicMock()
        mock_slot.id = 1
        mock_slot.series_id = 1
        mock_slot.slot_number = 1
        mock_slot.name = "Slot 1"
        mock_slot.status = "empty"
        
        instance.add_slot.return_value = mock_slot
        
        response = client.post("/api/v2/series/1/slots", json={
            "slot_number": 1,
            "name": "Slot 1"
        })
        
        assert response.status_code == 201
        assert response.json()["name"] == "Slot 1"

def test_add_coin_to_series():
    with patch("src.infrastructure.web.routers.series.SeriesService") as MockService:
        instance = MockService.return_value
        instance.add_coin_to_series.return_value = MagicMock(
            id=1, series_id=1, coin_id=1, slot_id=None
        )
        
        response = client.post("/api/v2/series/1/coins/1")
        assert response.status_code == 201
        assert response.json()["coin_id"] == 1

def test_remove_coin_from_series():
    with patch("src.infrastructure.web.routers.series.SeriesService") as MockService:
        instance = MockService.return_value
        instance.remove_coin_from_series.return_value = True
        
        response = client.delete("/api/v2/series/1/coins/1")
        assert response.status_code == 204