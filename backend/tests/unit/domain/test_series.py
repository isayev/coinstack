import pytest
from src.domain.series import Series, SeriesSlot, SeriesType, SlotStatus

def test_series_completion():
    slots = [
        SeriesSlot(id=1, series_id=1, slot_number=1, name="Slot 1", status=SlotStatus.FILLED),
        SeriesSlot(id=2, series_id=1, slot_number=2, name="Slot 2", status=SlotStatus.EMPTY),
    ]
    series = Series(
        id=1,
        name="My Series",
        series_type=SeriesType.USER_DEFINED,
        slots=slots,
        target_count=4
    )
    
    assert series.completion_percentage == 25.0

def test_series_defaults():
    series = Series(id=1, name="Test", series_type=SeriesType.SMART)
    assert series.slots == []
    assert series.completion_percentage == 0.0