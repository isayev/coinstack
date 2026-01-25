import pytest
from unittest.mock import MagicMock
from src.infrastructure.services.series_service import SeriesService
from src.infrastructure.persistence.models_series import SeriesModel, SeriesSlotModel

@pytest.fixture
def mock_session():
    return MagicMock()

def test_create_series(mock_session):
    service = SeriesService(mock_session)
    
    # Setup
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    # Ensure slug check returns None (no collision)
    mock_session.scalar.return_value = None
    
    series = service.create_series(
        name="Twelve Caesars",
        series_type="canonical",
        target_count=12
    )
    
    assert series.name == "Twelve Caesars"
    assert series.slug == "twelve-caesars" # Auto-generated
    mock_session.add.assert_called()
    mock_session.commit.assert_called()

def test_add_slot(mock_session):
    service = SeriesService(mock_session)
    
    mock_series = SeriesModel(id=1, name="Test", slots=[])
    mock_session.get.return_value = mock_series
    
    slot = service.add_slot(
        series_id=1,
        slot_number=1,
        name="Julius Caesar"
    )
    
    assert slot.name == "Julius Caesar"
    mock_session.add.assert_called()

def test_generate_slug_uniqueness(mock_session):
    service = SeriesService(mock_session)
    
    # Mock existing slug check: first call finds match, second returns None
    # We use side_effect to simulate sequence of return values
    mock_session.scalar.side_effect = [MagicMock(), None]
    
    slug = service._generate_slug("Test Series")
    
    assert slug == "test-series-1"