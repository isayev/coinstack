"""LLM-based disambiguator for reference matching."""
import json
import logging
from typing import Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DisambiguationResult(BaseModel):
    """Result from LLM disambiguation."""
    
    # Resolved reference
    system: str | None = None
    volume: str | None = None
    number: str | None = None
    subtype: str | None = None
    normalized: str | None = None
    
    # Confidence in the resolution
    confidence: float = 0.0
    
    # If multiple candidates, which one was chosen
    selected_candidate_id: str | None = None
    
    # Explanation from LLM
    reasoning: str | None = None
    
    # If disambiguation failed
    failed: bool = False
    failure_reason: str | None = None


class LegendExpansion(BaseModel):
    """Result from legend expansion."""
    
    latin_expansion: str | None = None   # Full Latin text
    english_translation: str | None = None  # English meaning
    notes: str | None = None              # Additional context


class LLMDisambiguator:
    """
    LLM-based service for handling ambiguous references.
    
    Handles the hard 10-20% that rule-based parsing can't match:
    1. No volume specified: "RIC 207" + ruler context -> RIC I 207
    2. Multiple candidates from reconciliation
    3. Variant matching: "RIC I 207 var." -> specific subtype
    """
    
    def __init__(self, anthropic_client=None):
        """
        Initialize with optional Anthropic client.
        
        If not provided, will try to import and create one.
        """
        self.client = anthropic_client
        self._initialized = False
    
    async def _ensure_client(self):
        """Lazy initialization of Anthropic client."""
        if self._initialized:
            return
        
        if self.client is None:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic()
            except ImportError:
                logger.warning("anthropic package not installed - LLM features disabled")
                self.client = None
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
                self.client = None
        
        self._initialized = True
    
    async def disambiguate_reference(
        self,
        raw_ref: str,
        coin_context: dict | None = None,
        candidates: list[dict] | None = None
    ) -> DisambiguationResult:
        """
        Disambiguate an ambiguous reference using LLM.
        
        Args:
            raw_ref: The original reference string
            coin_context: Coin metadata (ruler, denomination, mint, date)
            candidates: List of candidate matches from reconciliation API
        
        Returns:
            DisambiguationResult with resolved reference or failure reason
        """
        await self._ensure_client()
        
        if not self.client:
            return DisambiguationResult(
                failed=True,
                failure_reason="LLM client not available"
            )
        
        prompt = self._build_disambiguation_prompt(raw_ref, coin_context, candidates)
        
        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_disambiguation_response(response.content[0].text)
            
        except Exception as e:
            logger.error(f"LLM disambiguation error: {e}", exc_info=True)
            return DisambiguationResult(
                failed=True,
                failure_reason=str(e)
            )
    
    def _build_disambiguation_prompt(
        self,
        raw_ref: str,
        coin_context: dict | None,
        candidates: list[dict] | None
    ) -> str:
        """Build prompt for reference disambiguation."""
        
        prompt_parts = [
            "You are a numismatic expert helping to identify coin catalog references.",
            "",
            f"Reference to identify: {raw_ref}",
        ]
        
        if coin_context:
            prompt_parts.append("")
            prompt_parts.append("Coin context:")
            if coin_context.get("ruler") or coin_context.get("authority"):
                prompt_parts.append(f"  - Ruler/Authority: {coin_context.get('ruler') or coin_context.get('authority')}")
            if coin_context.get("denomination"):
                prompt_parts.append(f"  - Denomination: {coin_context['denomination']}")
            if coin_context.get("mint"):
                prompt_parts.append(f"  - Mint: {coin_context['mint']}")
            if coin_context.get("date_from") or coin_context.get("date_to"):
                date_str = f"{coin_context.get('date_from', '?')} to {coin_context.get('date_to', '?')}"
                prompt_parts.append(f"  - Date range: {date_str}")
            if coin_context.get("metal"):
                prompt_parts.append(f"  - Metal: {coin_context['metal']}")
        
        if candidates:
            prompt_parts.append("")
            prompt_parts.append("Candidate matches from catalog:")
            for i, c in enumerate(candidates[:5], 1):  # Limit to 5 candidates
                prompt_parts.append(f"  {i}. {c.get('name', c.get('external_id', 'Unknown'))}")
                if c.get('description'):
                    prompt_parts.append(f"     Description: {c['description']}")
                if c.get('confidence'):
                    prompt_parts.append(f"     Confidence: {c['confidence']:.0%}")
        
        prompt_parts.extend([
            "",
            "Based on the reference and context, identify the correct catalog entry.",
            "If the reference is ambiguous (e.g., 'RIC 207' without volume), use the ruler context to determine the correct volume.",
            "",
            "Respond in JSON format:",
            "{",
            '  "system": "ric|crawford|rpc|other",',
            '  "volume": "volume number or null",',
            '  "number": "reference number",',
            '  "subtype": "variant letter or null",',
            '  "normalized": "full normalized reference like ric.1.207",',
            '  "confidence": 0.0-1.0,',
            '  "selected_candidate_id": "if choosing from candidates",',
            '  "reasoning": "brief explanation of your choice"',
            "}",
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_disambiguation_response(self, response_text: str) -> DisambiguationResult:
        """Parse LLM response into DisambiguationResult."""
        
        # Try to extract JSON from response
        try:
            # Find JSON block in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                return DisambiguationResult(
                    system=data.get("system"),
                    volume=data.get("volume"),
                    number=data.get("number"),
                    subtype=data.get("subtype"),
                    normalized=data.get("normalized"),
                    confidence=float(data.get("confidence", 0)),
                    selected_candidate_id=data.get("selected_candidate_id"),
                    reasoning=data.get("reasoning"),
                    failed=False
                )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
        
        return DisambiguationResult(
            failed=True,
            failure_reason="Could not parse LLM response",
            reasoning=response_text[:500]  # Keep some of the response for debugging
        )
    
    async def expand_legend(
        self,
        abbreviated: str,
        context: dict | None = None
    ) -> LegendExpansion:
        """
        Expand abbreviated coin legend using LLM.
        
        Args:
            abbreviated: Abbreviated legend text (e.g., "IMP CAESAR DIVI F")
            context: Coin context for better accuracy
        
        Returns:
            LegendExpansion with Latin expansion and English translation
        """
        await self._ensure_client()
        
        if not self.client:
            return LegendExpansion()
        
        prompt_parts = [
            "You are a numismatic expert specializing in Roman coin legends.",
            "",
            f"Expand this abbreviated coin legend: {abbreviated}",
        ]
        
        if context:
            if context.get("ruler"):
                prompt_parts.append(f"Ruler: {context['ruler']}")
            if context.get("denomination"):
                prompt_parts.append(f"Denomination: {context['denomination']}")
            if context.get("date_from"):
                prompt_parts.append(f"Date: circa {context['date_from']}")
        
        prompt_parts.extend([
            "",
            "Respond in JSON format:",
            "{",
            '  "latin_expansion": "full Latin text",',
            '  "english_translation": "English meaning",',
            '  "notes": "any relevant historical context (optional)"',
            "}",
        ])
        
        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": "\n".join(prompt_parts)}]
            )
            
            response_text = response.content[0].text
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
                return LegendExpansion(
                    latin_expansion=data.get("latin_expansion"),
                    english_translation=data.get("english_translation"),
                    notes=data.get("notes")
                )
                
        except Exception as e:
            logger.error(f"Legend expansion error: {e}")
        
        return LegendExpansion()
    
    async def select_best_candidate(
        self,
        candidates: list[dict],
        coin_context: dict | None = None
    ) -> dict | None:
        """
        Select the best candidate from multiple reconciliation results.
        
        Uses coin context to pick the most appropriate match.
        """
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Try LLM selection
        result = await self.disambiguate_reference(
            raw_ref=candidates[0].get("name", ""),
            coin_context=coin_context,
            candidates=candidates
        )
        
        if result.selected_candidate_id:
            for c in candidates:
                if c.get("external_id") == result.selected_candidate_id:
                    return c
        
        # Fallback to highest confidence
        return max(candidates, key=lambda x: x.get("confidence", 0))


# Singleton instance
disambiguator = LLMDisambiguator()
