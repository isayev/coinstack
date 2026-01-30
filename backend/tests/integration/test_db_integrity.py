import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect
from src.infrastructure.persistence.orm import CoinModel, AuctionDataModel, CoinImageModel
from src.domain.coin import Category, Metal, GradingState

def test_db_constraint_die_axis(db_session):
    """Verify that the CheckConstraint for die_axis (0-12) is enforced."""
    # Valid coin
    valid_coin = CoinModel(
        category=Category.ROMAN_IMPERIAL.value,
        metal=Metal.SILVER.value,
        diameter_mm=Decimal("19.0"),
        weight_g=Decimal("3.5"),
        die_axis=6,
        issuer="Valid Issuer",
        grading_state=GradingState.RAW.value,
        grade="VF"
    )
    db_session.add(valid_coin)
    db_session.commit()
    
    # Invalid coin (die_axis=13)
    invalid_coin = CoinModel(
        category=Category.ROMAN_IMPERIAL.value,
        metal=Metal.SILVER.value,
        diameter_mm=Decimal("19.0"),
        weight_g=Decimal("3.5"),
        die_axis=13,
        issuer="Invalid Issuer",
        grading_state=GradingState.RAW.value,
        grade="VF"
    )
    db_session.add(invalid_coin)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_db_precision_weight(db_session):
    """Verify that weight_g stores 3 decimal places without rounding."""
    precise_weight = Decimal("3.141")
    coin = CoinModel(
        category=Category.GREEK.value,
        metal=Metal.SILVER.value,
        diameter_mm=Decimal("20.0"),
        weight_g=precise_weight,
        issuer="Athens",
        grading_state=GradingState.RAW.value,
        grade="VF"
    )
    db_session.add(coin)
    db_session.commit()
    db_session.refresh(coin)
    
    assert coin.weight_g == precise_weight
    # Ensure it didn't round to 2 decimals
    assert coin.weight_g != Decimal("3.14")

def test_cascade_delete_orphans(db_session):
    """Verify that deleting a Coin deletes its associated AuctionData and Images."""
    coin = CoinModel(
        category=Category.GREEK.value,
        metal=Metal.SILVER.value,
        diameter_mm=Decimal("20.0"),
        issuer="Athens",
        grading_state=GradingState.RAW.value,
        grade="VF"
    )
    db_session.add(coin)
    db_session.flush()
    
    # Add Auction Data
    auction_data = AuctionDataModel(
        coin_id=coin.id,
        url="http://example.com/lot/orphan_test",
        source="Heritage",
        source_lot_id="123"
    )
    db_session.add(auction_data)
    
    # Add Images
    img = CoinImageModel(coin_id=coin.id, url="img_orphan.jpg", image_type="obverse")
    db_session.add(img)
    
    db_session.commit()
    
    # Verify existence
    assert db_session.query(AuctionDataModel).count() == 1
    assert db_session.query(CoinImageModel).count() == 1
    
    # Delete parent Coin
    db_session.delete(coin)
    db_session.commit()
    
    # Verify orphans are gone
    assert db_session.query(AuctionDataModel).count() == 0
    assert db_session.query(CoinImageModel).count() == 0

def test_indexes_exist(db_session):
    """Verify that expected indexes are present in the database."""
    inspector = inspect(db_session.bind)
    indexes = inspector.get_indexes("coins_v2")
    
    # Extract just the column names covered by indexes
    indexed_columns = []
    for idx in indexes:
        indexed_columns.extend(idx["column_names"])
        
    assert "denomination" in indexed_columns
    assert "portrait_subject" in indexed_columns
    assert "category" in indexed_columns
    assert "issue_status" in indexed_columns