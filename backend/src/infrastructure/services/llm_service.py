"""
LLM Service Implementation - Facade.

This module implements the ILLMService protocol by delegating to specialized
services in src.infrastructure.services.llm.*.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Dict, List

from src.domain.llm import (
    ILLMService,
    LLMCapability,
    LLMResult,
    VocabNormalizationResult,
    LegendExpansionResult,
    AuctionParseResult,
    ProvenanceParseResult,
    CoinIdentificationResult,
    ReferenceValidationResult,
    AttributionAssistResult,
    LegendTranscribeResult,
    CatalogParseResult,
    ConditionObservationsResult,
)
from src.infrastructure.services.llm.base_client import BaseLLMClient
from src.infrastructure.services.llm.identification import IdentificationService
from src.infrastructure.services.llm.context import ContextService
from src.infrastructure.services.llm.parsing import ParsingService
from src.infrastructure.services.llm.normalization import NormalizationService

logger = logging.getLogger(__name__)

class LLMService(ILLMService):
    """
    Facade for LLM functionality.
    Delegates to specialized services.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.base_client = BaseLLMClient(config_path)
        
        self.identification = IdentificationService(self.base_client)
        self.context_service = ContextService(self.base_client)
        self.parsing = ParsingService(self.base_client)
        self.normalization = NormalizationService(self.base_client)
        
        # Expose components for admin access (cost tracker, etc.)
        self.cost_tracker = self.base_client.cost_tracker
        self.config = self.base_client.config

    # --- Generic ---
    
    async def complete(
        self,
        capability: LLMCapability,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[dict] = None,
        image_b64: Optional[str] = None,
    ) -> LLMResult:
        result = await self.base_client.execute_prompt(
            capability=capability,
            user_input=prompt,
            system_override=system,
            context=context,
            image_data=image_b64
        )
        return LLMResult(
            content=result["content"] if isinstance(result["content"], str) else str(result["content"]),
            confidence=0.8,
            cost_usd=result["cost"],
            model_used=result["model"],
            cached=result["cached"],
        )

    # --- P0 Capabilities (Normalization/Parsing) ---

    async def normalize_vocab(
        self,
        raw_text: str,
        vocab_type: str,
        context: Optional[dict] = None,
    ) -> VocabNormalizationResult:
        return await self.normalization.normalize_vocab(raw_text, vocab_type, context)

    async def expand_legend(self, abbreviation: str) -> LegendExpansionResult:
        return await self.normalization.expand_legend(abbreviation)

    async def parse_auction(
        self,
        description: str,
        hints: Optional[dict] = None,
    ) -> AuctionParseResult:
        return await self.parsing.parse_auction(description, hints)

    async def parse_provenance(self, description: str) -> ProvenanceParseResult:
        return await self.parsing.parse_provenance(description)

    # --- P1 Capabilities (Core) ---

    async def identify_coin(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> CoinIdentificationResult:
        return await self.identification.identify_coin(image_b64, hints)

    async def validate_reference(
        self,
        reference: str,
        coin_context: Optional[dict] = None,
    ) -> ReferenceValidationResult:
        return await self.normalization.validate_reference(reference, coin_context)

    async def generate_context(self, coin_data: dict) -> LLMResult:
        # Note: Returns LLMResult but content is enriched with citations dict
        return await self.context_service.generate_context(coin_data)

    # --- P2 Capabilities (Advanced) ---

    async def assist_attribution(self, known_info: dict) -> AttributionAssistResult:
        return await self.identification.assist_attribution(known_info)

    async def transcribe_legend(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> LegendTranscribeResult:
        return await self.identification.transcribe_legend(image_b64, hints)

    async def parse_catalog(self, reference: str) -> CatalogParseResult:
        return await self.parsing.parse_catalog(reference)

    async def observe_condition(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> ConditionObservationsResult:
        return await self.identification.observe_condition(image_b64, hints)

    # --- Admin ---

    def get_monthly_cost(self) -> float:
        if self.cost_tracker:
            return self.cost_tracker.get_monthly_cost()
        return 0.0

    def get_active_profile(self) -> str:
        return self.base_client.config.active_profile

    def is_capability_available(self, capability: LLMCapability) -> bool:
        return self.base_client.is_capability_available(capability)