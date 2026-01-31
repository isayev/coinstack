"""
SaveLLMEnrichmentUseCase - Application service for dual-write LLM enrichment operations.

Extracts dual-write logic from LLM router endpoints into a reusable use case,
following Clean Architecture principles.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.domain.coin import LLMEnrichment
from src.domain.repositories import ILLMEnrichmentRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EnrichmentResult:
    """Result of saving an LLM enrichment."""
    success: bool
    enrichment_id: Optional[int] = None
    error: Optional[str] = None


class SaveLLMEnrichmentUseCase:
    """
    Use case for saving LLM enrichment records.

    Provides a clean interface for dual-write operations, ensuring consistent
    hash computation, error handling, and logging across all LLM endpoints.
    """

    # Minimum hash length for collision resistance (32 chars = 128 bits)
    HASH_LENGTH = 32

    def __init__(self, enrichment_repo: ILLMEnrichmentRepository):
        self._enrichment_repo = enrichment_repo

    def execute(
        self,
        coin_id: int,
        capability: str,
        output_content: dict[str, Any],
        input_data: dict[str, Any],
        model_id: str,
        confidence: Optional[float] = None,
        cost_usd: float = 0.0,
        raw_response: str = "",
        cached: bool = False,
        needs_review: bool = False,
        capability_version: int = 1,
    ) -> EnrichmentResult:
        """
        Save an LLM enrichment record.

        Args:
            coin_id: ID of the coin being enriched
            capability: LLM capability name (e.g., "identify_coin", "generate_context")
            output_content: Parsed output content as dict
            input_data: Input data used for the LLM call (for hashing/deduplication)
            model_id: ID of the model used
            confidence: Confidence score (None if unknown, NOT a default like 0.8)
            cost_usd: Cost of the LLM call in USD
            raw_response: Raw LLM response string
            cached: Whether the response was cached
            needs_review: Whether the enrichment needs manual review
            capability_version: Version of the capability (default 1)

        Returns:
            EnrichmentResult with success status and enrichment ID
        """
        try:
            # Compute input hash for deduplication
            input_snapshot = json.dumps(input_data, sort_keys=True, default=str)
            input_hash = hashlib.sha256(input_snapshot.encode()).hexdigest()[:self.HASH_LENGTH]

            enrichment = LLMEnrichment(
                coin_id=coin_id,
                capability=capability,
                capability_version=capability_version,
                model_id=model_id,
                model_version=None,
                input_hash=input_hash,
                input_snapshot=input_snapshot,
                output_content=json.dumps(output_content),
                raw_response=raw_response,
                confidence=confidence,  # None if unknown - NOT a misleading default
                needs_review=needs_review,
                quality_flags=None,
                cost_usd=cost_usd,
                input_tokens=None,
                output_tokens=None,
                cached=cached,
                review_status="pending",
                created_at=datetime.now(timezone.utc),
            )

            saved = self._enrichment_repo.create(enrichment)
            logger.info(
                "Coin %d: Saved %s enrichment #%d to llm_enrichments table",
                coin_id, capability, saved.id
            )

            return EnrichmentResult(success=True, enrichment_id=saved.id)

        except Exception as e:
            logger.exception(
                "Failed to save %s enrichment for coin %d: %s",
                capability, coin_id, e
            )
            return EnrichmentResult(
                success=False,
                error=f"Failed to save enrichment: {type(e).__name__}"
            )

    def compute_image_hash(self, image_b64: str) -> str:
        """
        Compute a hash for an image for input tracking.

        Uses full 32-char hash for adequate collision resistance.
        """
        if not image_b64:
            return "no_image"
        return hashlib.sha256(image_b64.encode()).hexdigest()[:self.HASH_LENGTH]
