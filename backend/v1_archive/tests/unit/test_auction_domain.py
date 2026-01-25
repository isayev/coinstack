import pytest
from src.domain.auction import AuctionLot
from decimal import Decimal

def test_auction_lot_creation():
    lot = AuctionLot(
        source="Heritage",
        lot_id="123",
        url="http://example.com",
        hammer_price=Decimal("100.00")
    )
    assert lot.source == "Heritage"
    assert lot.hammer_price == Decimal("100.00")
