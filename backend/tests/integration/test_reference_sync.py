"""Integration tests for reference sync (canonical local_ref, dedupe)."""
import pytest
from decimal import Decimal
from sqlalchemy import select

from src.application.services.reference_sync import sync_coin_references
from src.infrastructure.persistence.orm import ReferenceTypeModel, CoinReferenceModel
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.domain.coin import (
    Coin,
    Category,
    Metal,
    Dimensions,
    Attribution,
    GradingDetails,
    GradingState,
    GradeService,
    AcquisitionDetails,
)


def _make_coin(issuer: str = "Trajan") -> Coin:
    return Coin(
        id=None,
        category=Category.ROMAN_IMPERIAL,
        metal=Metal.SILVER,
        dimensions=Dimensions(weight_g=Decimal("3.5"), diameter_mm=Decimal("18.0")),
        attribution=Attribution(issuer=issuer, year_start=98, year_end=117),
        grading=GradingDetails(
            grading_state=GradingState.SLABBED,
            grade="VF",
            service=GradeService.NGC,
            certification_number="test-001",
        ),
        acquisition=AcquisitionDetails(
            price=Decimal("100"),
            currency="USD",
            source="Test",
        ),
    )


@pytest.mark.integration
def test_sync_dedupe_equivalent_refs_one_reference_type_row(db_session):
    """Two equivalent refs (string and dict) produce one reference_types row via canonical local_ref."""
    repo = SqlAlchemyCoinRepository(db_session)
    coin = repo.save(_make_coin())
    db_session.flush()

    # Equivalent refs: same logical reference in different forms
    refs = [
        "RIC IV.1 351b",  # string
        {"catalog": "RIC", "volume": "IV.1", "number": "351b"},  # dict from API
    ]
    sync_coin_references(db_session, coin.id, refs, "user")
    db_session.flush()

    # Should have exactly one ReferenceTypeModel for this ref
    rts = db_session.scalars(
        select(ReferenceTypeModel).where(
            ReferenceTypeModel.system == "ric",
            ReferenceTypeModel.local_ref == "RIC IV.1 351b",
        )
    ).all()
    assert len(rts) == 1, "Equivalent refs should dedupe to one reference_types row"
    assert rts[0].volume == "IV.1"
    assert rts[0].number == "351b"

    # Coin should have two coin_references links to the same reference_type (or one if we dedupe refs list too)
    links = db_session.scalars(
        select(CoinReferenceModel).where(CoinReferenceModel.coin_id == coin.id)
    ).all()
    assert len(links) == 1, "Sync dedupes by (system, local_ref) so one link to the single reference_type"
