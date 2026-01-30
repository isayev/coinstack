"""
Normalization Service - P0 Capability.

Handles:
- vocab_normalize
- legend_expand
- reference_validate
"""
import json
import logging
from typing import Optional, Dict, List, Any

from src.domain.llm import (
    LLMCapability,
    VocabNormalizationResult,
    LegendExpansionResult,
    ReferenceValidationResult,
    LLMError,
    LLMProviderUnavailable,
)
from src.infrastructure.services.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)

class NormalizationService:
    def __init__(self, client: BaseLLMClient):
        self.client = client

    async def normalize_vocab(
        self,
        raw_text: str,
        vocab_type: str,
        context: Optional[dict] = None,
        vocab_repo: Any = None,
    ) -> VocabNormalizationResult:
        """Normalize vocabulary term to canonical form."""
        prompt = f"Vocab type: {vocab_type}\nRaw text: \"{raw_text}\""
        if context:
            prompt += f"\nContext: {json.dumps(context)}"
        
        try:
            result = await self.client.execute_prompt(
                capability=LLMCapability.VOCAB_NORMALIZE,
                user_input=prompt,
                context={"vocab_type": vocab_type, "raw_text": raw_text},
            )
            
            content = result["content"]
            parsed_confidence = 0.8 # Default if missing
            reasoning = []
            
            if isinstance(content, dict):
                canonical = content.get("canonical_name", raw_text)
                reasoning = content.get("reasoning", [])
                parsed_confidence = content.get("confidence", 0.8)
            else:
                # Fallback text parsing
                canonical = content.strip()
            
            return VocabNormalizationResult(
                content=json.dumps(content) if isinstance(content, dict) else content,
                confidence=parsed_confidence,
                cost_usd=result["cost"],
                model_used=result["model"],
                cached=result["cached"],
                reasoning=reasoning,
                raw_input=raw_text,
                canonical_name=canonical,
                vocab_type=vocab_type,
            )
        
        except LLMProviderUnavailable:
            if vocab_repo:
                return await self._vocab_normalize_fallback(raw_text, vocab_type, vocab_repo)
            raise

    async def _vocab_normalize_fallback(
        self,
        raw_text: str,
        vocab_type: str,
        vocab_repo: Any,
    ) -> VocabNormalizationResult:
        from src.domain.llm import FuzzyMatch
        matches: List[FuzzyMatch] = vocab_repo.fuzzy_search(
            query=raw_text,
            vocab_type=vocab_type,
            limit=3,
            min_score=0.5,
        )
        if matches and matches[0].score > 0.7:
            best = matches[0]
            confidence = best.score * 0.8
            return VocabNormalizationResult(
                content=json.dumps({"canonical_name": best.canonical_name}),
                confidence=confidence,
                cost_usd=0.0,
                model_used="fuzzy_match_fallback",
                cached=False,
                reasoning=["Fuzzy match fallback"],
                raw_input=raw_text,
                canonical_name=best.canonical_name,
                vocab_type=vocab_type,
            )
        return VocabNormalizationResult(
            content="{}",
            confidence=0.0,
            cost_usd=0.0,
            model_used="fuzzy_match_fallback",
            cached=False,
            reasoning=["No match found"],
            raw_input=raw_text,
            canonical_name="",
            vocab_type=vocab_type,
        )

    async def expand_legend(self, abbreviation: str) -> LegendExpansionResult:
        """Expand abbreviated Latin legend."""
        result = await self.client.execute_prompt(
            capability=LLMCapability.LEGEND_EXPAND,
            user_input=f"Expand: {abbreviation}",
            context={"abbreviation": abbreviation},
        )
        
        content = result["content"]
        expanded = content.get("expanded", abbreviation) if isinstance(content, dict) else content.strip()
        
        return LegendExpansionResult(
            content=json.dumps(content) if isinstance(content, dict) else content,
            confidence=0.9, # High confidence for legends generally
            cost_usd=result["cost"],
            model_used=result["model"],
            cached=result["cached"],
            reasoning=[],
            abbreviated=abbreviation,
            expanded=expanded,
        )

    async def validate_reference(
        self,
        reference: str,
        coin_context: Optional[dict] = None,
    ) -> ReferenceValidationResult:
        """Validate catalog reference."""
        prompt = f"Validate this catalog reference: {reference}"
        if coin_context:
            prompt += f"\n\nCoin context: {json.dumps(coin_context)}"
        
        result = await self.client.execute_prompt(
            capability=LLMCapability.REFERENCE_VALIDATE,
            user_input=prompt,
            context={"reference": reference},
        )
        
        content = result["content"]
        parsed = content if isinstance(content, dict) else {}
        
        return ReferenceValidationResult(
            content=json.dumps(content) if isinstance(content, dict) else content,
            confidence=parsed.get("confidence", 0.8),
            cost_usd=result["cost"],
            model_used=result["model"],
            cached=result["cached"],
            reasoning=parsed.get("reasoning", []),
            reference=reference,
            is_valid=parsed.get("is_valid", False),
            normalized=parsed.get("normalized", reference),
            alternatives=parsed.get("alternatives", []),
            notes=parsed.get("notes", ""),
        )
