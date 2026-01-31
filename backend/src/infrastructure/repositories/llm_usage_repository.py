"""
LLM Usage Repository Implementation.

Handles persistence of aggregated LLM usage metrics for cost monitoring and analytics.
Implements ILLMUsageRepository protocol.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.domain.coin import LLMUsageDaily
from src.domain.repositories import ILLMUsageRepository
from src.infrastructure.persistence.orm import LLMUsageDailyModel


class SqlAlchemyLLMUsageRepository(ILLMUsageRepository):
    """
    Repository for managing LLM usage metrics.

    Provides aggregated daily metrics for cost monitoring, performance tracking,
    and capacity planning.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_daily(
        self,
        date: str,
        capability: str,
        model_id: str
    ) -> Optional[LLMUsageDaily]:
        """Get usage metrics for a specific day/capability/model."""
        model = self.session.query(LLMUsageDailyModel).filter(
            LLMUsageDailyModel.date == date,
            LLMUsageDailyModel.capability == capability,
            LLMUsageDailyModel.model_id == model_id
        ).first()

        return self._to_domain(model) if model else None

    def upsert(self, usage: LLMUsageDaily) -> LLMUsageDaily:
        """Create or update daily usage metrics."""
        model = self.session.query(LLMUsageDailyModel).filter(
            LLMUsageDailyModel.date == usage.date,
            LLMUsageDailyModel.capability == usage.capability,
            LLMUsageDailyModel.model_id == usage.model_id
        ).first()

        if model:
            # Update existing
            model.request_count = usage.request_count
            model.cache_hits = usage.cache_hits
            model.error_count = usage.error_count
            model.total_cost_usd = Decimal(str(usage.total_cost_usd))
            model.total_input_tokens = usage.total_input_tokens
            model.total_output_tokens = usage.total_output_tokens
            model.avg_confidence = Decimal(str(usage.avg_confidence)) if usage.avg_confidence else None
            model.review_approved = usage.review_approved
            model.review_rejected = usage.review_rejected
            model.avg_latency_ms = Decimal(str(usage.avg_latency_ms)) if usage.avg_latency_ms else None
        else:
            # Create new
            model = self._to_model(usage)
            self.session.add(model)

        self.session.flush()
        return self._to_domain(model)

    def increment(
        self,
        date: str,
        capability: str,
        model_id: str,
        request_count: int = 1,
        cache_hits: int = 0,
        error_count: int = 0,
        cost_usd: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> LLMUsageDaily:
        """Atomically increment usage counters."""
        model = self.session.query(LLMUsageDailyModel).filter(
            LLMUsageDailyModel.date == date,
            LLMUsageDailyModel.capability == capability,
            LLMUsageDailyModel.model_id == model_id
        ).with_for_update().first()

        if model:
            # Increment existing counters
            model.request_count = (model.request_count or 0) + request_count
            model.cache_hits = (model.cache_hits or 0) + cache_hits
            model.error_count = (model.error_count or 0) + error_count
            model.total_cost_usd = (model.total_cost_usd or Decimal(0)) + Decimal(str(cost_usd))
            model.total_input_tokens = (model.total_input_tokens or 0) + input_tokens
            model.total_output_tokens = (model.total_output_tokens or 0) + output_tokens
        else:
            # Create new with initial values
            model = LLMUsageDailyModel(
                date=date,
                capability=capability,
                model_id=model_id,
                request_count=request_count,
                cache_hits=cache_hits,
                error_count=error_count,
                total_cost_usd=Decimal(str(cost_usd)),
                total_input_tokens=input_tokens,
                total_output_tokens=output_tokens,
            )
            self.session.add(model)

        self.session.flush()
        return self._to_domain(model)

    def list_by_date_range(
        self,
        start_date: str,
        end_date: str,
        capability: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> List[LLMUsageDaily]:
        """List usage metrics for a date range."""
        query = self.session.query(LLMUsageDailyModel).filter(
            LLMUsageDailyModel.date >= start_date,
            LLMUsageDailyModel.date <= end_date
        )

        if capability:
            query = query.filter(LLMUsageDailyModel.capability == capability)

        if model_id:
            query = query.filter(LLMUsageDailyModel.model_id == model_id)

        query = query.order_by(LLMUsageDailyModel.date.desc())
        models = query.all()

        return [self._to_domain(m) for m in models]

    def get_total_cost(
        self,
        start_date: str,
        end_date: str,
        capability: Optional[str] = None
    ) -> float:
        """Get total cost for a date range."""
        query = self.session.query(func.sum(LLMUsageDailyModel.total_cost_usd)).filter(
            LLMUsageDailyModel.date >= start_date,
            LLMUsageDailyModel.date <= end_date
        )

        if capability:
            query = query.filter(LLMUsageDailyModel.capability == capability)

        result = query.scalar()
        return float(result) if result else 0.0

    def get_capability_summary(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get usage summary grouped by capability.

        Returns dict with totals for each capability.
        """
        results = self.session.query(
            LLMUsageDailyModel.capability,
            func.sum(LLMUsageDailyModel.request_count).label("total_requests"),
            func.sum(LLMUsageDailyModel.cache_hits).label("total_cache_hits"),
            func.sum(LLMUsageDailyModel.error_count).label("total_errors"),
            func.sum(LLMUsageDailyModel.total_cost_usd).label("total_cost"),
            func.sum(LLMUsageDailyModel.total_input_tokens).label("total_input_tokens"),
            func.sum(LLMUsageDailyModel.total_output_tokens).label("total_output_tokens"),
            func.avg(LLMUsageDailyModel.avg_confidence).label("avg_confidence"),
            func.sum(LLMUsageDailyModel.review_approved).label("total_approved"),
            func.sum(LLMUsageDailyModel.review_rejected).label("total_rejected"),
        ).filter(
            LLMUsageDailyModel.date >= start_date,
            LLMUsageDailyModel.date <= end_date
        ).group_by(LLMUsageDailyModel.capability).all()

        summary = {}
        for row in results:
            summary[row.capability] = {
                "total_requests": row.total_requests or 0,
                "total_cache_hits": row.total_cache_hits or 0,
                "total_errors": row.total_errors or 0,
                "total_cost_usd": float(row.total_cost) if row.total_cost else 0.0,
                "total_input_tokens": row.total_input_tokens or 0,
                "total_output_tokens": row.total_output_tokens or 0,
                "avg_confidence": float(row.avg_confidence) if row.avg_confidence else None,
                "total_approved": row.total_approved or 0,
                "total_rejected": row.total_rejected or 0,
                "cache_hit_rate": (
                    (row.total_cache_hits or 0) / (row.total_requests or 1)
                ) if row.total_requests else 0.0,
                "error_rate": (
                    (row.total_errors or 0) / (row.total_requests or 1)
                ) if row.total_requests else 0.0,
            }

        return summary

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: LLMUsageDailyModel) -> LLMUsageDaily:
        """Convert ORM model to domain value object."""
        return LLMUsageDaily(
            date=model.date,
            capability=model.capability,
            model_id=model.model_id,
            request_count=model.request_count or 0,
            cache_hits=model.cache_hits or 0,
            error_count=model.error_count or 0,
            total_cost_usd=float(model.total_cost_usd) if model.total_cost_usd else 0.0,
            total_input_tokens=model.total_input_tokens or 0,
            total_output_tokens=model.total_output_tokens or 0,
            avg_confidence=float(model.avg_confidence) if model.avg_confidence else None,
            review_approved=model.review_approved or 0,
            review_rejected=model.review_rejected or 0,
            avg_latency_ms=float(model.avg_latency_ms) if model.avg_latency_ms else None,
        )

    def _to_model(self, usage: LLMUsageDaily) -> LLMUsageDailyModel:
        """Convert domain value object to ORM model."""
        return LLMUsageDailyModel(
            date=usage.date,
            capability=usage.capability,
            model_id=usage.model_id,
            request_count=usage.request_count,
            cache_hits=usage.cache_hits,
            error_count=usage.error_count,
            total_cost_usd=Decimal(str(usage.total_cost_usd)),
            total_input_tokens=usage.total_input_tokens,
            total_output_tokens=usage.total_output_tokens,
            avg_confidence=Decimal(str(usage.avg_confidence)) if usage.avg_confidence else None,
            review_approved=usage.review_approved,
            review_rejected=usage.review_rejected,
            avg_latency_ms=Decimal(str(usage.avg_latency_ms)) if usage.avg_latency_ms else None,
        )
