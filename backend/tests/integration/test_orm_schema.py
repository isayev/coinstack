import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from src.infrastructure.persistence.orm import CoinModel, AuctionDataModel, CoinImageModel
from src.domain.coin import Category, Metal, GradingState

def test_die_axis_check_constraint(db_session):
    """Test that the database enforces die_axis between 0 and 12."""
    
    # Test valid value
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
    
    # Test upper bound violation
    invalid_upper = CoinModel(
        category=Category.ROMAN_IMPERIAL.value,
        metal=Metal.SILVER.value,
        diameter_mm=Decimal("19.0"),
        weight_g=Decimal("3.5"),
        die_axis=13, # Invalid
        issuer="Invalid Upper",
        grading_state=GradingState.RAW.value,
        grade="VF"
    )
    db_session.add(invalid_upper)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    
    # Test lower bound violation
    invalid_lower = CoinModel(
        category=Category.ROMAN_IMPERIAL.value,
        metal=Metal.SILVER.value,
        diameter_mm=Decimal("19.0"),
        weight_g=Decimal("3.5"),
        die_axis=-1, # Invalid
        issuer="Invalid Lower",
        grading_state=GradingState.RAW.value,
        grade="VF"
    )
    db_session.add(invalid_lower)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_weight_precision(db_session):
    """Test that weight_g stores 3 decimal places correctly."""
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
    # Ensure it didn't round to 3.14
    assert coin.weight_g != Decimal("3.14")

def test_auction_data_cascade_delete(db_session):
    """Test that deleting a coin deletes its associated auction data."""
    # Create coin
    coin = CoinModel(
        category=Category.GREEK.value,
        metal=Metal.SILVER.value,
        diameter_mm=Decimal("20.0"),
        issuer="Athens",
        grading_state=GradingState.RAW.value,
        grade="VF"
    )
    db_session.add(coin)
    db_session.flush() # Get ID
    
    # Create linked auction data
    auction_data = AuctionDataModel(
        coin_id=coin.id,
        url="http://example.com/lot/123",
        source="Heritage",
        source_lot_id="123"
    )
    db_session.add(auction_data)
    db_session.commit()
    
    # Verify link
    assert db_session.query(AuctionDataModel).count() == 1
    
    # Delete coin
    db_session.delete(coin)
    db_session.commit()
    
    # Verify auction data is gone
    assert db_session.query(AuctionDataModel).count() == 0

def test_image_cascade_delete(db_session):
    """Test that deleting a coin deletes its images."""
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
    
    # Add images
    img1 = CoinImageModel(coin_id=coin.id, url="img1.jpg", image_type="obverse")
    img2 = CoinImageModel(coin_id=coin.id, url="img2.jpg", image_type="reverse")
    db_session.add_all([img1, img2])
    db_session.commit()
    
    assert db_session.query(CoinImageModel).count() == 2
    
    # Delete coin
    db_session.delete(coin)
    db_session.commit()
    
    # Verify images are gone
    assert db_session.query(CoinImageModel).count() == 0
