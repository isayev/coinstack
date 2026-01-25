"""
Unit tests for Coin Mutation Domain Events.

Tests CoinCreated, CoinAttributeChanged, CoinImageAdded, CoinDeleted,
and CoinProvenanceAdded events.
"""

import pytest
from datetime import datetime, timezone

from src.domain.events import (
    DomainEvent,
    CoinCreated,
    CoinAttributeChanged,
    CoinImageAdded,
    CoinDeleted,
    CoinProvenanceAdded,
)


class TestCoinCreated:
    """Tests for CoinCreated event."""
    
    def test_create_event(self):
        """Can create a CoinCreated event."""
        event = CoinCreated(
            coin_id=42,
            category="roman_imperial",
            issuer="Trajan",
            denomination="denarius",
            source="manual",
        )
        
        assert event.coin_id == 42
        assert event.category == "roman_imperial"
        assert event.issuer == "Trajan"
        assert event.denomination == "denarius"
        assert event.source == "manual"
    
    def test_event_has_id_and_timestamp(self):
        """Event has auto-generated ID and timestamp."""
        event = CoinCreated(coin_id=1, category="greek", issuer="Athens")
        
        assert event.event_id is not None
        assert len(event.event_id) == 36  # UUID format
        assert event.occurred_at is not None
        assert event.occurred_at.tzinfo is not None
    
    def test_event_type_property(self):
        """event_type returns class name."""
        event = CoinCreated(coin_id=1, category="greek", issuer="Athens")
        assert event.event_type == "CoinCreated"
    
    def test_event_is_frozen(self):
        """Event is immutable."""
        event = CoinCreated(coin_id=1, category="greek", issuer="Athens")
        
        with pytest.raises(AttributeError):
            event.coin_id = 2
    
    def test_str_representation(self):
        """String representation is informative."""
        event = CoinCreated(
            coin_id=42,
            category="roman_imperial",
            issuer="Trajan",
            source="import",
        )
        
        s = str(event)
        assert "42" in s
        assert "roman_imperial" in s
        assert "Trajan" in s
        assert "import" in s


class TestCoinAttributeChanged:
    """Tests for CoinAttributeChanged event."""
    
    def test_create_event(self):
        """Can create a CoinAttributeChanged event."""
        event = CoinAttributeChanged(
            coin_id=42,
            field_name="issuer",
            old_value="Augustus",
            new_value="Augustus Caesar",
            source="llm",
            confidence=0.95,
        )
        
        assert event.coin_id == 42
        assert event.field_name == "issuer"
        assert event.old_value == "Augustus"
        assert event.new_value == "Augustus Caesar"
        assert event.source == "llm"
        assert event.confidence == 0.95
    
    def test_manual_change_no_confidence(self):
        """Manual changes don't require confidence."""
        event = CoinAttributeChanged(
            coin_id=1,
            field_name="grade",
            old_value="VF",
            new_value="EF",
            source="manual",
        )
        
        assert event.confidence is None
    
    def test_str_representation(self):
        """String shows old -> new transition."""
        event = CoinAttributeChanged(
            coin_id=1,
            field_name="grade",
            old_value="VF",
            new_value="EF",
            source="manual",
        )
        
        s = str(event)
        assert "VF" in s
        assert "EF" in s
        assert "->" in s


class TestCoinImageAdded:
    """Tests for CoinImageAdded event."""
    
    def test_create_event(self):
        """Can create a CoinImageAdded event."""
        event = CoinImageAdded(
            coin_id=42,
            image_url="https://example.com/image.jpg",
            image_type="obverse",
            is_primary=True,
            source="scraper",
        )
        
        assert event.coin_id == 42
        assert event.image_url == "https://example.com/image.jpg"
        assert event.image_type == "obverse"
        assert event.is_primary is True
        assert event.source == "scraper"
    
    def test_str_shows_primary(self):
        """String shows if primary image."""
        event = CoinImageAdded(
            coin_id=1,
            image_url="http://test.com/img.jpg",
            image_type="reverse",
            is_primary=True,
        )
        
        s = str(event)
        assert "primary" in s.lower()


class TestCoinDeleted:
    """Tests for CoinDeleted event."""
    
    def test_create_event_with_reason(self):
        """Can create a CoinDeleted event with reason."""
        event = CoinDeleted(
            coin_id=42,
            reason="Duplicate entry",
        )
        
        assert event.coin_id == 42
        assert event.reason == "Duplicate entry"
    
    def test_create_event_without_reason(self):
        """Can create a CoinDeleted event without reason."""
        event = CoinDeleted(coin_id=42)
        
        assert event.coin_id == 42
        assert event.reason is None
    
    def test_str_includes_reason_if_present(self):
        """String includes reason when provided."""
        event = CoinDeleted(coin_id=1, reason="Sold")
        s = str(event)
        assert "Sold" in s


class TestCoinProvenanceAdded:
    """Tests for CoinProvenanceAdded event."""
    
    def test_create_auction_provenance(self):
        """Can create auction provenance event."""
        event = CoinProvenanceAdded(
            coin_id=42,
            event_type="auction",
            source_name="Heritage Auctions",
            event_date="2023-05-15",
            lot_number="3456",
            price=1500.0,
            currency="USD",
            source="scraper",
        )
        
        assert event.coin_id == 42
        assert event.event_type == "auction"
        assert event.source_name == "Heritage Auctions"
        assert event.lot_number == "3456"
        assert event.price == 1500.0
    
    def test_create_collection_provenance(self):
        """Can create collection provenance event."""
        event = CoinProvenanceAdded(
            coin_id=42,
            event_type="collection",
            source_name="Hunt Collection",
            source="llm",
        )
        
        assert event.event_type == "collection"
        assert event.source_name == "Hunt Collection"


class TestEventInheritance:
    """Tests for event inheritance from DomainEvent."""
    
    def test_all_events_inherit_from_domain_event(self):
        """All coin events inherit from DomainEvent."""
        events = [
            CoinCreated(coin_id=1, category="greek", issuer="Test"),
            CoinAttributeChanged(coin_id=1, field_name="test", old_value="a", new_value="b"),
            CoinImageAdded(coin_id=1, image_url="http://test.com", image_type="obverse"),
            CoinDeleted(coin_id=1),
            CoinProvenanceAdded(coin_id=1, event_type="auction", source_name="Test"),
        ]
        
        for event in events:
            assert isinstance(event, DomainEvent)
            assert event.event_id is not None
            assert event.occurred_at is not None
