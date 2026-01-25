"""
Event Store Implementation for CoinStack.

SQLite-based implementation of the IEventStore interface for persisting
domain events. Uses a simple append-only table with JSON serialization.

This implementation is optimized for:
1. Fast appends (write-heavy workload)
2. Efficient queries by coin_id and event_type
3. Aggregate queries for accuracy statistics
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from src.domain.events import (
    DomainEvent,
    IEventStore,
    # Coin Mutation Events
    CoinCreated,
    CoinAttributeChanged,
    CoinImageAdded,
    CoinDeleted,
    CoinProvenanceAdded,
    # LLM Feedback Events
    LLMSuggestionAccepted,
    LLMSuggestionRejected,
    LLMSuggestionAutoApplied,
    LLMEnrichmentCompleted,
    # Aggregates
    AccuracyStats,
    ConfidenceBucket,
)

logger = logging.getLogger(__name__)


# =============================================================================
# EVENT SERIALIZATION
# =============================================================================

EVENT_TYPE_MAP: Dict[str, Type[DomainEvent]] = {
    # Coin Mutation Events
    "CoinCreated": CoinCreated,
    "CoinAttributeChanged": CoinAttributeChanged,
    "CoinImageAdded": CoinImageAdded,
    "CoinDeleted": CoinDeleted,
    "CoinProvenanceAdded": CoinProvenanceAdded,
    # LLM Feedback Events
    "LLMSuggestionAccepted": LLMSuggestionAccepted,
    "LLMSuggestionRejected": LLMSuggestionRejected,
    "LLMSuggestionAutoApplied": LLMSuggestionAutoApplied,
    "LLMEnrichmentCompleted": LLMEnrichmentCompleted,
}


def serialize_event(event: DomainEvent) -> Dict[str, Any]:
    """Serialize event to dictionary for JSON storage."""
    data = {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "occurred_at": event.occurred_at.isoformat(),
    }
    
    # Add type-specific fields
    if isinstance(event, LLMSuggestionAccepted):
        data.update({
            "coin_id": event.coin_id,
            "capability": event.capability,
            "field_name": event.field_name,
            "suggested_value": event.suggested_value,
            "confidence": event.confidence,
            "model_used": event.model_used,
        })
    elif isinstance(event, LLMSuggestionRejected):
        data.update({
            "coin_id": event.coin_id,
            "capability": event.capability,
            "field_name": event.field_name,
            "suggested_value": event.suggested_value,
            "user_correction": event.user_correction,
            "rejection_reason": event.rejection_reason,
            "confidence": event.confidence,
            "model_used": event.model_used,
        })
    elif isinstance(event, LLMSuggestionAutoApplied):
        data.update({
            "coin_id": event.coin_id,
            "capability": event.capability,
            "field_name": event.field_name,
            "value": event.value,
            "confidence": event.confidence,
            "model_used": event.model_used,
        })
    elif isinstance(event, LLMEnrichmentCompleted):
        data.update({
            "coin_id": event.coin_id,
            "request_id": event.request_id,
            "capabilities_run": event.capabilities_run,
            "safe_fills_count": event.safe_fills_count,
            "conflicts_count": event.conflicts_count,
            "total_cost_usd": event.total_cost_usd,
        })
    # Coin Mutation Events
    elif isinstance(event, CoinCreated):
        data.update({
            "coin_id": event.coin_id,
            "category": event.category,
            "issuer": event.issuer,
            "denomination": event.denomination,
            "source": event.source,
        })
    elif isinstance(event, CoinAttributeChanged):
        data.update({
            "coin_id": event.coin_id,
            "field_name": event.field_name,
            "old_value": event.old_value,
            "new_value": event.new_value,
            "source": event.source,
            "confidence": event.confidence,
        })
    elif isinstance(event, CoinImageAdded):
        data.update({
            "coin_id": event.coin_id,
            "image_url": event.image_url,
            "image_type": event.image_type,
            "is_primary": event.is_primary,
            "source": event.source,
        })
    elif isinstance(event, CoinDeleted):
        data.update({
            "coin_id": event.coin_id,
            "reason": event.reason,
        })
    elif isinstance(event, CoinProvenanceAdded):
        data.update({
            "coin_id": event.coin_id,
            "event_type": event.event_type,
            "source_name": event.source_name,
            "event_date": event.event_date,
            "lot_number": event.lot_number,
            "price": event.price,
            "currency": event.currency,
            "source": event.source,
        })
    
    return data


def deserialize_event(data: Dict[str, Any]) -> DomainEvent:
    """Deserialize event from dictionary."""
    event_type = data.get("event_type", "")
    event_class = EVENT_TYPE_MAP.get(event_type)
    
    if not event_class:
        # Return base event if type unknown
        return DomainEvent(
            event_id=data.get("event_id", ""),
            occurred_at=datetime.fromisoformat(data.get("occurred_at", "")),
        )
    
    # Parse common fields
    kwargs = {
        "event_id": data.get("event_id", ""),
        "occurred_at": datetime.fromisoformat(data.get("occurred_at", "")),
    }
    
    # Add type-specific fields
    if event_class == LLMSuggestionAccepted:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "capability": data.get("capability", ""),
            "field_name": data.get("field_name", ""),
            "suggested_value": data.get("suggested_value"),
            "confidence": data.get("confidence", 0.0),
            "model_used": data.get("model_used", ""),
        })
    elif event_class == LLMSuggestionRejected:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "capability": data.get("capability", ""),
            "field_name": data.get("field_name", ""),
            "suggested_value": data.get("suggested_value"),
            "user_correction": data.get("user_correction"),
            "rejection_reason": data.get("rejection_reason"),
            "confidence": data.get("confidence", 0.0),
            "model_used": data.get("model_used", ""),
        })
    elif event_class == LLMSuggestionAutoApplied:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "capability": data.get("capability", ""),
            "field_name": data.get("field_name", ""),
            "value": data.get("value"),
            "confidence": data.get("confidence", 0.0),
            "model_used": data.get("model_used", ""),
        })
    elif event_class == LLMEnrichmentCompleted:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "request_id": data.get("request_id", ""),
            "capabilities_run": data.get("capabilities_run", []),
            "safe_fills_count": data.get("safe_fills_count", 0),
            "conflicts_count": data.get("conflicts_count", 0),
            "total_cost_usd": data.get("total_cost_usd", 0.0),
        })
    # Coin Mutation Events
    elif event_class == CoinCreated:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "category": data.get("category", ""),
            "issuer": data.get("issuer", ""),
            "denomination": data.get("denomination"),
            "source": data.get("source", "manual"),
        })
    elif event_class == CoinAttributeChanged:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "field_name": data.get("field_name", ""),
            "old_value": data.get("old_value"),
            "new_value": data.get("new_value"),
            "source": data.get("source", "manual"),
            "confidence": data.get("confidence"),
        })
    elif event_class == CoinImageAdded:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "image_url": data.get("image_url", ""),
            "image_type": data.get("image_type", ""),
            "is_primary": data.get("is_primary", False),
            "source": data.get("source", "manual"),
        })
    elif event_class == CoinDeleted:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "reason": data.get("reason"),
        })
    elif event_class == CoinProvenanceAdded:
        kwargs.update({
            "coin_id": data.get("coin_id", 0),
            "event_type": data.get("event_type", ""),
            "source_name": data.get("source_name", ""),
            "event_date": data.get("event_date"),
            "lot_number": data.get("lot_number"),
            "price": data.get("price"),
            "currency": data.get("currency"),
            "source": data.get("source", "manual"),
        })
    
    return event_class(**kwargs)


# =============================================================================
# SQLITE EVENT STORE
# =============================================================================

class SqliteEventStore(IEventStore):
    """
    SQLite implementation of event store.
    
    Uses a single append-only table with JSON payload for flexibility.
    Indexes on coin_id, event_type, and occurred_at for efficient queries.
    """
    
    def __init__(self, db_path: str = "data/llm_events.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(self.db_path))
        return self._local.conn
    
    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                coin_id INTEGER,
                capability TEXT,
                confidence REAL,
                payload TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_coin_id
            ON events(coin_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type
            ON events(event_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_occurred
            ON events(occurred_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_capability
            ON events(capability)
        """)
        conn.commit()
    
    def append(self, event: DomainEvent) -> None:
        """Append an event to the store."""
        data = serialize_event(event)
        
        # Extract commonly queried fields
        coin_id = data.get("coin_id")
        capability = data.get("capability")
        confidence = data.get("confidence")
        
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO events 
            (event_id, event_type, occurred_at, coin_id, capability, confidence, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.event_type,
                event.occurred_at.isoformat(),
                coin_id,
                capability,
                confidence,
                json.dumps(data),
            )
        )
        conn.commit()
        logger.debug(f"Appended event: {event.event_type} for coin {coin_id}")
    
    def get_by_coin_id(self, coin_id: int, limit: int = 100) -> List[DomainEvent]:
        """Get events for a specific coin."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT payload FROM events
            WHERE coin_id = ?
            ORDER BY occurred_at DESC
            LIMIT ?
            """,
            (coin_id, limit)
        )
        
        events = []
        for row in cursor.fetchall():
            data = json.loads(row[0])
            events.append(deserialize_event(data))
        
        return events
    
    def get_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[DomainEvent]:
        """Get events of a specific type."""
        conn = self._get_conn()
        
        if since:
            cursor = conn.execute(
                """
                SELECT payload FROM events
                WHERE event_type = ? AND occurred_at >= ?
                ORDER BY occurred_at DESC
                LIMIT ?
                """,
                (event_type, since.isoformat(), limit)
            )
        else:
            cursor = conn.execute(
                """
                SELECT payload FROM events
                WHERE event_type = ?
                ORDER BY occurred_at DESC
                LIMIT ?
                """,
                (event_type, limit)
            )
        
        events = []
        for row in cursor.fetchall():
            data = json.loads(row[0])
            events.append(deserialize_event(data))
        
        return events
    
    def count_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None
    ) -> int:
        """Count events of a specific type."""
        conn = self._get_conn()
        
        if since:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM events
                WHERE event_type = ? AND occurred_at >= ?
                """,
                (event_type, since.isoformat())
            )
        else:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM events WHERE event_type = ?",
                (event_type,)
            )
        
        return cursor.fetchone()[0]
    
    # -------------------------------------------------------------------------
    # Accuracy Statistics
    # -------------------------------------------------------------------------
    
    def get_accuracy_stats(
        self,
        capability: str,
        days: int = 30
    ) -> AccuracyStats:
        """
        Get accuracy statistics for a capability.
        
        Args:
            capability: Capability name
            days: Number of days to look back
        
        Returns:
            AccuracyStats with aggregated counts
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)
        conn = self._get_conn()
        
        # Count accepted
        cursor = conn.execute(
            """
            SELECT COUNT(*) FROM events
            WHERE capability = ? AND event_type = 'LLMSuggestionAccepted'
            AND occurred_at >= ?
            """,
            (capability, since.isoformat())
        )
        accepted = cursor.fetchone()[0]
        
        # Count rejected
        cursor = conn.execute(
            """
            SELECT COUNT(*) FROM events
            WHERE capability = ? AND event_type = 'LLMSuggestionRejected'
            AND occurred_at >= ?
            """,
            (capability, since.isoformat())
        )
        rejected = cursor.fetchone()[0]
        
        # Count auto-applied
        cursor = conn.execute(
            """
            SELECT COUNT(*) FROM events
            WHERE capability = ? AND event_type = 'LLMSuggestionAutoApplied'
            AND occurred_at >= ?
            """,
            (capability, since.isoformat())
        )
        auto_applied = cursor.fetchone()[0]
        
        return AccuracyStats(
            capability=capability,
            sample_size=accepted + rejected,
            accepted_count=accepted,
            rejected_count=rejected,
            auto_applied_count=auto_applied,
        )
    
    def get_confidence_buckets(
        self,
        capability: str,
        bucket_size: float = 0.1,
        days: int = 30
    ) -> List[ConfidenceBucket]:
        """
        Get accuracy by confidence bucket.
        
        Used for confidence calibration - if we report 0.9 confidence
        but only get 75% acceptance, we need to recalibrate.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)
        buckets = []
        
        # Create buckets from 0.0 to 1.0
        confidence = 0.0
        while confidence < 1.0:
            min_conf = confidence
            max_conf = min(confidence + bucket_size, 1.0)
            
            conn = self._get_conn()
            
            # Count accepted in bucket
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM events
                WHERE capability = ? AND event_type = 'LLMSuggestionAccepted'
                AND confidence >= ? AND confidence < ?
                AND occurred_at >= ?
                """,
                (capability, min_conf, max_conf, since.isoformat())
            )
            accepted = cursor.fetchone()[0]
            
            # Count rejected in bucket
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM events
                WHERE capability = ? AND event_type = 'LLMSuggestionRejected'
                AND confidence >= ? AND confidence < ?
                AND occurred_at >= ?
                """,
                (capability, min_conf, max_conf, since.isoformat())
            )
            rejected = cursor.fetchone()[0]
            
            total = accepted + rejected
            if total > 0:
                buckets.append(ConfidenceBucket(
                    confidence_min=min_conf,
                    confidence_max=max_conf,
                    total=total,
                    accepted=accepted,
                    rejected=rejected,
                ))
            
            confidence += bucket_size
        
        return buckets
    
    def get_calibration_factor(
        self,
        capability: str,
        confidence: float,
        days: int = 30
    ) -> float:
        """
        Get confidence calibration factor.
        
        If actual accuracy differs from reported confidence,
        this returns a multiplier to adjust future confidences.
        
        Example:
        - Reporting 0.9 confidence but 75% actual accuracy
        - Factor = 0.75 / 0.9 = 0.833
        - Calibrated = 0.9 * 0.833 = 0.75
        """
        # Find the bucket containing this confidence
        bucket_size = 0.1
        bucket_min = (confidence // bucket_size) * bucket_size
        
        buckets = self.get_confidence_buckets(capability, bucket_size, days)
        
        for bucket in buckets:
            if bucket.confidence_min <= confidence < bucket.confidence_max:
                if bucket.actual_accuracy is not None and confidence > 0:
                    return bucket.actual_accuracy / confidence
        
        # No data, return neutral factor
        return 1.0
