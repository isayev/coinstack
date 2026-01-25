"""
Domain Events for CoinStack.

This module defines domain events following the Event Sourcing pattern.
Events represent facts that have occurred in the system and are immutable
once created.

Coin Mutation Events:
- CoinCreated: A new coin was added to the collection
- CoinAttributeChanged: A coin attribute was modified
- CoinImageAdded: An image was added to a coin
- CoinDeleted: A coin was removed from the collection

LLM Feedback Events:
- LLMSuggestionAccepted: User accepted an LLM suggestion
- LLMSuggestionRejected: User rejected an LLM suggestion
- LLMSuggestionAutoApplied: High-confidence suggestion was auto-applied

These events enable:
1. Complete audit trail of all coin changes
2. Source attribution (manual, LLM, scraper, import)
3. Undo/revert capability
4. Change history visualization
5. Accuracy tracking for LLM improvement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, List
from uuid import uuid4


# =============================================================================
# BASE EVENT
# =============================================================================

@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.
    
    Events are immutable records of something that happened in the system.
    They include metadata for ordering and identification.
    """
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def event_type(self) -> str:
        """Return the event type name."""
        return self.__class__.__name__


# =============================================================================
# COIN MUTATION EVENTS
# =============================================================================

@dataclass(frozen=True)
class CoinCreated(DomainEvent):
    """
    A new coin was added to the collection.
    
    Records the initial creation with key identifying information.
    Source indicates how the coin was added (manual entry, import, scraper).
    """
    coin_id: int = 0
    category: str = ""
    issuer: str = ""
    denomination: Optional[str] = None
    source: str = "manual"  # manual, import, scraper
    
    def __str__(self) -> str:
        return f"CoinCreated(id={self.coin_id}, {self.category}, {self.issuer}, via {self.source})"


@dataclass(frozen=True)
class CoinAttributeChanged(DomainEvent):
    """
    A coin attribute was modified.
    
    Records both old and new values for audit trail and potential undo.
    Source indicates what triggered the change.
    """
    coin_id: int = 0
    field_name: str = ""
    old_value: Any = None
    new_value: Any = None
    source: str = "manual"  # manual, llm, scraper, import
    confidence: Optional[float] = None  # For LLM-driven changes
    
    def __str__(self) -> str:
        return f"CoinAttributeChanged(coin={self.coin_id}, {self.field_name}: {self.old_value} -> {self.new_value}, via {self.source})"


@dataclass(frozen=True)
class CoinImageAdded(DomainEvent):
    """
    An image was added to a coin.
    
    Records the image URL and type (obverse, reverse, slab, etc.).
    """
    coin_id: int = 0
    image_url: str = ""
    image_type: str = ""  # obverse, reverse, slab, detail
    is_primary: bool = False
    source: str = "manual"  # manual, scraper
    
    def __str__(self) -> str:
        primary = " (primary)" if self.is_primary else ""
        return f"CoinImageAdded(coin={self.coin_id}, {self.image_type}{primary}, via {self.source})"


@dataclass(frozen=True)
class CoinDeleted(DomainEvent):
    """
    A coin was removed from the collection.
    
    This is a soft delete marker - the coin may still exist in DB
    but is marked as deleted. Reason is optional but recommended.
    """
    coin_id: int = 0
    reason: Optional[str] = None
    
    def __str__(self) -> str:
        reason_str = f", reason={self.reason}" if self.reason else ""
        return f"CoinDeleted(coin={self.coin_id}{reason_str})"


@dataclass(frozen=True)
class CoinProvenanceAdded(DomainEvent):
    """
    A provenance entry was added to a coin.
    
    Records ownership history events (auctions, collections, dealers).
    """
    coin_id: int = 0
    event_type: str = ""  # auction, collection, dealer, private_sale
    source_name: str = ""  # Hunt Collection, Heritage, CNG, etc.
    event_date: Optional[str] = None  # ISO date string
    lot_number: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    source: str = "manual"  # manual, llm, scraper
    
    def __str__(self) -> str:
        return f"CoinProvenanceAdded(coin={self.coin_id}, {self.event_type}: {self.source_name}, via {self.source})"


# =============================================================================
# LLM FEEDBACK EVENTS
# =============================================================================

@dataclass(frozen=True)
class LLMSuggestionAccepted(DomainEvent):
    """
    User accepted an LLM suggestion.
    
    This event is recorded when a user explicitly accepts a suggestion
    from an LLM capability, confirming its accuracy.
    """
    coin_id: int = 0
    capability: str = ""  # e.g., "vocab_normalize", "legend_expand"
    field_name: str = ""  # e.g., "issuing_authority_id", "obverse_legend_expanded"
    suggested_value: Any = None
    confidence: float = 0.0
    model_used: str = ""
    
    def __str__(self) -> str:
        return f"LLMSuggestionAccepted(coin={self.coin_id}, {self.capability}.{self.field_name}={self.suggested_value})"


@dataclass(frozen=True)
class LLMSuggestionRejected(DomainEvent):
    """
    User rejected an LLM suggestion.
    
    This event is recorded when a user explicitly rejects a suggestion.
    The user_correction field captures what the user entered instead,
    which is valuable for improving prompts.
    """
    coin_id: int = 0
    capability: str = ""
    field_name: str = ""
    suggested_value: Any = None
    user_correction: Optional[Any] = None  # What user entered instead
    rejection_reason: Optional[str] = None  # Optional explanation
    confidence: float = 0.0
    model_used: str = ""
    
    def __str__(self) -> str:
        return f"LLMSuggestionRejected(coin={self.coin_id}, {self.capability}.{self.field_name}, correction={self.user_correction})"


@dataclass(frozen=True)
class LLMSuggestionAutoApplied(DomainEvent):
    """
    High-confidence suggestion was auto-applied.
    
    This event is recorded when a suggestion with sufficiently high
    confidence is automatically applied without user review.
    """
    coin_id: int = 0
    capability: str = ""
    field_name: str = ""
    value: Any = None
    confidence: float = 0.0
    model_used: str = ""
    
    def __str__(self) -> str:
        return f"LLMSuggestionAutoApplied(coin={self.coin_id}, {self.capability}.{self.field_name}={self.value})"


@dataclass(frozen=True)
class LLMEnrichmentCompleted(DomainEvent):
    """
    Coin enrichment completed.
    
    Aggregates all results from an enrichment operation.
    """
    coin_id: int = 0
    request_id: str = ""
    capabilities_run: List[str] = field(default_factory=list)
    safe_fills_count: int = 0
    conflicts_count: int = 0
    total_cost_usd: float = 0.0
    
    def __str__(self) -> str:
        return f"LLMEnrichmentCompleted(coin={self.coin_id}, safe={self.safe_fills_count}, conflicts={self.conflicts_count})"


# =============================================================================
# EVENT STORE INTERFACE
# =============================================================================

from typing import Protocol


class IEventStore(Protocol):
    """Interface for event persistence."""
    
    def append(self, event: DomainEvent) -> None:
        """Append an event to the store."""
        ...
    
    def get_by_coin_id(self, coin_id: int, limit: int = 100) -> List[DomainEvent]:
        """Get events for a specific coin."""
        ...
    
    def get_by_type(
        self, 
        event_type: str, 
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[DomainEvent]:
        """Get events of a specific type."""
        ...
    
    def count_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None
    ) -> int:
        """Count events of a specific type."""
        ...


# =============================================================================
# FEEDBACK AGGREGATES
# =============================================================================

@dataclass
class AccuracyStats:
    """Aggregated accuracy statistics for a capability."""
    capability: str
    sample_size: int
    accepted_count: int
    rejected_count: int
    auto_applied_count: int
    
    @property
    def acceptance_rate(self) -> Optional[float]:
        """Calculate acceptance rate."""
        total = self.accepted_count + self.rejected_count
        if total == 0:
            return None
        return self.accepted_count / total
    
    @property
    def total_suggestions(self) -> int:
        """Total suggestions including auto-applied."""
        return self.accepted_count + self.rejected_count + self.auto_applied_count


@dataclass
class ConfidenceBucket:
    """Statistics for a confidence range."""
    confidence_min: float
    confidence_max: float
    total: int
    accepted: int
    rejected: int
    
    @property
    def actual_accuracy(self) -> Optional[float]:
        """Actual accuracy in this confidence bucket."""
        total = self.accepted + self.rejected
        if total == 0:
            return None
        return self.accepted / total
