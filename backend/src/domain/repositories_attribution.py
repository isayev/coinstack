"""Repository interfaces for attribution confidence module.

Follows Protocol pattern for dependency inversion - application layer depends on these interfaces,
infrastructure layer provides concrete implementations.
"""

from typing import Protocol, Optional
from src.domain.coin import AttributionHypothesis


class IAttributionHypothesisRepository(Protocol):
    """Repository for attribution hypotheses with field-level confidence."""

    def get_by_id(self, hypothesis_id: int) -> Optional[AttributionHypothesis]:
        """Get attribution hypothesis by ID."""
        ...

    def get_by_coin_id(self, coin_id: int) -> list[AttributionHypothesis]:
        """Get all attribution hypotheses for a coin (ordered by rank)."""
        ...

    def get_primary(self, coin_id: int) -> Optional[AttributionHypothesis]:
        """Get the primary attribution hypothesis (rank=1) for a coin."""
        ...

    def create(self, hypothesis: AttributionHypothesis) -> AttributionHypothesis:
        """Create new attribution hypothesis."""
        ...

    def update(self, hypothesis_id: int, hypothesis: AttributionHypothesis) -> Optional[AttributionHypothesis]:
        """Update existing attribution hypothesis."""
        ...

    def delete(self, hypothesis_id: int) -> bool:
        """Delete attribution hypothesis."""
        ...

    def set_primary(self, hypothesis_id: int) -> AttributionHypothesis:
        """Promote hypothesis to rank 1, shift others down atomically."""
        ...

    def reorder(self, coin_id: int, hypothesis_ids: list[int]) -> list[AttributionHypothesis]:
        """Reorder hypotheses for a coin (hypothesis_ids in desired rank order)."""
        ...
