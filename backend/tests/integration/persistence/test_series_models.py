import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.models_series import SeriesModel, SeriesSlotModel

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_series_persistence(db_session):
    series = SeriesModel(
        name="Twelve Caesars",
        slug="twelve-caesars",
        series_type="canonical",
        target_count=12
    )
    db_session.add(series)
    db_session.commit()

    loaded = db_session.scalar(select(SeriesModel).where(SeriesModel.slug == "twelve-caesars"))
    assert loaded.name == "Twelve Caesars"
    assert len(loaded.slots) == 0

def test_series_slots(db_session):
    series = SeriesModel(name="Test", slug="test", series_type="user", target_count=2)
    db_session.add(series)
    db_session.commit()

    slot = SeriesSlotModel(
        series_id=series.id,
        slot_number=1,
        name="Slot 1",
        status="empty"
    )
    db_session.add(slot)
    db_session.commit()

    loaded_series = db_session.get(SeriesModel, series.id)
    assert len(loaded_series.slots) == 1
    assert loaded_series.slots[0].name == "Slot 1"
