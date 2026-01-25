"""
LLM Metrics Service for CoinStack.

Tracks LLM performance, errors, and usage metrics for observability.
Provides aggregated statistics for dashboard and monitoring.

Metrics tracked:
- Call latency by capability/model
- Success/failure rates
- Cache hit rates
- Parse failures
- Hallucination detections
- Cost by capability/model
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# METRICS DATA STRUCTURES
# =============================================================================

@dataclass
class LLMCallMetric:
    """Single LLM call metric."""
    timestamp: datetime
    capability: str
    model: str
    latency_ms: float
    success: bool
    cached: bool
    cost_usd: float
    input_tokens: int = 0
    output_tokens: int = 0
    error_type: Optional[str] = None


@dataclass
class MetricsSummary:
    """Aggregated metrics summary."""
    period_hours: int
    total_calls: int
    successful_calls: int
    failed_calls: int
    cached_calls: int
    total_cost_usd: float
    avg_latency_ms: float
    p95_latency_ms: float
    cache_hit_rate: float
    success_rate: float
    calls_by_capability: Dict[str, int] = field(default_factory=dict)
    calls_by_model: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)


@dataclass
class CapabilityMetrics:
    """Metrics for a single capability."""
    capability: str
    period_hours: int
    total_calls: int
    success_rate: float
    avg_latency_ms: float
    cache_hit_rate: float
    total_cost_usd: float
    parse_failures: int
    hallucinations: int


# =============================================================================
# METRICS SERVICE
# =============================================================================

class LLMMetrics:
    """
    Track LLM performance and errors.
    
    Uses SQLite for persistence with efficient aggregation queries.
    Designed for low-overhead recording during LLM calls.
    """
    
    def __init__(self, db_path: str = "data/llm_metrics.sqlite"):
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
        
        # Main metrics table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                capability TEXT NOT NULL,
                model TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                success INTEGER NOT NULL,
                cached INTEGER NOT NULL,
                cost_usd REAL DEFAULT 0.0,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                error_type TEXT
            )
        """)
        
        # Indexes for aggregation queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
            ON llm_metrics(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_capability
            ON llm_metrics(capability)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_model
            ON llm_metrics(model)
        """)
        
        # Parse failures table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_parse_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                capability TEXT NOT NULL,
                model TEXT NOT NULL,
                raw_output TEXT NOT NULL,
                error_message TEXT
            )
        """)
        
        # Hallucinations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_hallucinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                capability TEXT NOT NULL,
                model TEXT NOT NULL,
                field TEXT NOT NULL,
                invalid_value TEXT NOT NULL,
                validation_error TEXT
            )
        """)
        
        conn.commit()
    
    # -------------------------------------------------------------------------
    # Recording Methods
    # -------------------------------------------------------------------------
    
    async def record_call(
        self,
        capability: str,
        model: str,
        latency_ms: float,
        success: bool,
        cached: bool,
        cost_usd: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error_type: Optional[str] = None,
    ):
        """Record an LLM call metric."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO llm_metrics 
            (timestamp, capability, model, latency_ms, success, cached, 
             cost_usd, input_tokens, output_tokens, error_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                capability,
                model,
                latency_ms,
                1 if success else 0,
                1 if cached else 0,
                cost_usd,
                input_tokens,
                output_tokens,
                error_type,
            )
        )
        conn.commit()
    
    async def record_parse_failure(
        self,
        capability: str,
        model: str,
        raw_output: str,
        error_message: Optional[str] = None,
    ):
        """Log unparseable LLM output for debugging."""
        logger.warning(
            f"Parse failure in {capability} ({model}): {raw_output[:200]}..."
        )
        
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO llm_parse_failures 
            (timestamp, capability, model, raw_output, error_message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                capability,
                model,
                raw_output[:5000],  # Limit storage
                error_message,
            )
        )
        conn.commit()
    
    async def record_hallucination(
        self,
        capability: str,
        model: str,
        field: str,
        invalid_value: str,
        validation_error: Optional[str] = None,
    ):
        """Log suspected hallucination."""
        logger.warning(
            f"Hallucination in {capability}.{field} ({model}): {invalid_value}"
        )
        
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO llm_hallucinations 
            (timestamp, capability, model, field, invalid_value, validation_error)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                capability,
                model,
                field,
                str(invalid_value)[:1000],
                validation_error,
            )
        )
        conn.commit()
    
    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------
    
    def get_summary(self, hours: int = 24) -> MetricsSummary:
        """Get aggregated metrics summary."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        conn = self._get_conn()
        
        # Total counts
        cursor = conn.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cached_count,
                COALESCE(SUM(cost_usd), 0) as total_cost,
                COALESCE(AVG(latency_ms), 0) as avg_latency
            FROM llm_metrics
            WHERE timestamp >= ?
            """,
            (since.isoformat(),)
        )
        row = cursor.fetchone()
        
        total = row[0] or 0
        successful = row[1] or 0
        failed = row[2] or 0
        cached_count = row[3] or 0
        total_cost = row[4] or 0.0
        avg_latency = row[5] or 0.0
        
        # P95 latency
        cursor = conn.execute(
            """
            SELECT latency_ms FROM llm_metrics
            WHERE timestamp >= ? AND cached = 0
            ORDER BY latency_ms
            """,
            (since.isoformat(),)
        )
        latencies = [r[0] for r in cursor.fetchall()]
        p95_latency = 0.0
        if latencies:
            idx = int(len(latencies) * 0.95)
            p95_latency = latencies[min(idx, len(latencies) - 1)]
        
        # Calls by capability
        cursor = conn.execute(
            """
            SELECT capability, COUNT(*) FROM llm_metrics
            WHERE timestamp >= ?
            GROUP BY capability
            """,
            (since.isoformat(),)
        )
        calls_by_capability = {r[0]: r[1] for r in cursor.fetchall()}
        
        # Calls by model
        cursor = conn.execute(
            """
            SELECT model, COUNT(*) FROM llm_metrics
            WHERE timestamp >= ?
            GROUP BY model
            """,
            (since.isoformat(),)
        )
        calls_by_model = {r[0]: r[1] for r in cursor.fetchall()}
        
        # Errors by type
        cursor = conn.execute(
            """
            SELECT error_type, COUNT(*) FROM llm_metrics
            WHERE timestamp >= ? AND error_type IS NOT NULL
            GROUP BY error_type
            """,
            (since.isoformat(),)
        )
        errors_by_type = {r[0]: r[1] for r in cursor.fetchall()}
        
        return MetricsSummary(
            period_hours=hours,
            total_calls=total,
            successful_calls=successful,
            failed_calls=failed,
            cached_calls=cached_count,
            total_cost_usd=total_cost,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            cache_hit_rate=cached_count / total if total > 0 else 0.0,
            success_rate=successful / total if total > 0 else 0.0,
            calls_by_capability=calls_by_capability,
            calls_by_model=calls_by_model,
            errors_by_type=errors_by_type,
        )
    
    def get_capability_metrics(
        self,
        capability: str,
        hours: int = 24
    ) -> CapabilityMetrics:
        """Get metrics for a specific capability."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        conn = self._get_conn()
        
        # Main metrics
        cursor = conn.execute(
            """
            SELECT 
                COUNT(*) as total,
                AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(latency_ms) as avg_latency,
                AVG(CASE WHEN cached = 1 THEN 1.0 ELSE 0.0 END) as cache_rate,
                SUM(cost_usd) as total_cost
            FROM llm_metrics
            WHERE capability = ? AND timestamp >= ?
            """,
            (capability, since.isoformat())
        )
        row = cursor.fetchone()
        
        # Parse failures count
        cursor = conn.execute(
            """
            SELECT COUNT(*) FROM llm_parse_failures
            WHERE capability = ? AND timestamp >= ?
            """,
            (capability, since.isoformat())
        )
        parse_failures = cursor.fetchone()[0]
        
        # Hallucinations count
        cursor = conn.execute(
            """
            SELECT COUNT(*) FROM llm_hallucinations
            WHERE capability = ? AND timestamp >= ?
            """,
            (capability, since.isoformat())
        )
        hallucinations = cursor.fetchone()[0]
        
        return CapabilityMetrics(
            capability=capability,
            period_hours=hours,
            total_calls=row[0] or 0,
            success_rate=row[1] or 0.0,
            avg_latency_ms=row[2] or 0.0,
            cache_hit_rate=row[3] or 0.0,
            total_cost_usd=row[4] or 0.0,
            parse_failures=parse_failures,
            hallucinations=hallucinations,
        )
    
    def get_recent_parse_failures(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent parse failures for debugging."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT timestamp, capability, model, raw_output, error_message
            FROM llm_parse_failures
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
        
        return [
            {
                "timestamp": row[0],
                "capability": row[1],
                "model": row[2],
                "raw_output": row[3],
                "error_message": row[4],
            }
            for row in cursor.fetchall()
        ]
    
    def get_recent_hallucinations(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent hallucinations for analysis."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT timestamp, capability, model, field, invalid_value, validation_error
            FROM llm_hallucinations
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
        
        return [
            {
                "timestamp": row[0],
                "capability": row[1],
                "model": row[2],
                "field": row[3],
                "invalid_value": row[4],
                "validation_error": row[5],
            }
            for row in cursor.fetchall()
        ]
    
    def cleanup_old_data(self, days: int = 90):
        """Remove old metrics data."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        conn = self._get_conn()
        
        conn.execute(
            "DELETE FROM llm_metrics WHERE timestamp < ?",
            (cutoff.isoformat(),)
        )
        conn.execute(
            "DELETE FROM llm_parse_failures WHERE timestamp < ?",
            (cutoff.isoformat(),)
        )
        conn.execute(
            "DELETE FROM llm_hallucinations WHERE timestamp < ?",
            (cutoff.isoformat(),)
        )
        conn.commit()
        logger.info(f"Cleaned up metrics older than {days} days")
