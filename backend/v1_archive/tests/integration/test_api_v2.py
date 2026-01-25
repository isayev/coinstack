from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool # Import StaticPool
from src.infrastructure.web.main import create_app
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.orm import CoinModel
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.domain.repositories import ICoinRepository
import pytest

# Setup in-memory DB for API tests
@pytest.fixture
def api_client():
    # Use StaticPool to share the in-memory DB across connections
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    
    app = create_app()
    
    # Dependency override
    def get_repo_override():
        db = SessionLocal()
        try:
            yield SqlAlchemyCoinRepository(db)
        finally:
            db.close()
    
    # Override the get_coin_repo dependency
    from src.infrastructure.web.dependencies import get_coin_repo
    app.dependency_overrides[get_coin_repo] = get_repo_override
    
    return TestClient(app)

def test_create_coin_api(api_client):
    payload = {
        "category": "roman_imperial",
        "metal": "silver",
        "weight_g": 3.52,
        "diameter_mm": 18.5,
        "issuer": "Augustus",
        "grading_state": "raw",
        "grade": "VF"
    }
    
    response = api_client.post("/api/v2/coins", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["attribution"]["issuer"] == "Augustus"
    assert data["grading"]["grade"] == "VF"
    assert data["dimensions"]["weight_g"] == "3.52"