"""
Parsing Service - P0/P2 Capability.

Handles:
- auction_parse
- provenance_parse
- catalog_parse
"""
import json
import logging
from typing import Optional

from src.domain.llm import (
    LLMCapability,
    AuctionParseResult,
    ProvenanceParseResult,
    CatalogParseResult,
    ProvenanceEntry,
    LLMParseError,
)
from src.infrastructure.services.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)

class ParsingService:
    def __init__(self, client: BaseLLMClient):
        self.client = client

    async def parse_auction(
        self,
        description: str,
        hints: Optional[dict] = None,
    ) -> AuctionParseResult:
        """Parse auction lot description."""
        prompt = f"Parse this auction lot description:\n\n{description}"
        if hints:
            prompt += f"\n\nHints: {json.dumps(hints)}"
        
        result = await self.client.execute_prompt(
            capability=LLMCapability.AUCTION_PARSE,
            user_input=prompt,
            context={"description": description[:100]},
        )
        
        parsed = result["content"]
        if not isinstance(parsed, dict):
             raise LLMParseError("Response was not JSON", str(parsed), "auction_parse")
        
        return AuctionParseResult(
            content=json.dumps(parsed),
            confidence=parsed.get("confidence", 0.8),
            cost_usd=result["cost"],
            model_used=result["model"],
            cached=result["cached"],
            reasoning=[],
            raw_text=description,
            issuer=parsed.get("issuer"),
            denomination=parsed.get("denomination"),
            metal=parsed.get("metal"),
            mint=parsed.get("mint"),
            year_start=parsed.get("year_start"),
            year_end=parsed.get("year_end"),
            weight_g=parsed.get("weight_g"),
            diameter_mm=parsed.get("diameter_mm"),
            obverse_legend=parsed.get("obverse_legend"),
            obverse_description=parsed.get("obverse_description"),
            reverse_legend=parsed.get("reverse_legend"),
            reverse_description=parsed.get("reverse_description"),
            references=parsed.get("references", []),
            grade=parsed.get("grade"),
        )

    async def parse_provenance(
        self,
        description: str,
    ) -> ProvenanceParseResult:
        """Extract provenance chain."""
        result = await self.client.execute_prompt(
            capability=LLMCapability.PROVENANCE_PARSE,
            user_input=f"Extract provenance from:\n\n{description}",
            context={"description": description[:100]},
        )
        
        parsed = result["content"]
        if not isinstance(parsed, dict):
             raise LLMParseError("Response was not JSON", str(parsed), "provenance_parse")
        
        chain = [
            ProvenanceEntry(
                source=entry.get("source", ""),
                source_type=entry.get("source_type", "unknown"),
                year=entry.get("year"),
                sale=entry.get("sale"),
                lot=entry.get("lot"),
            )
            for entry in parsed.get("provenance_chain", [])
        ]
        
        return ProvenanceParseResult(
            content=json.dumps(parsed),
            confidence=parsed.get("confidence", 0.8),
            cost_usd=result["cost"],
            model_used=result["model"],
            cached=result["cached"],
            reasoning=[],
            raw_text=description,
            provenance_chain=chain,
            earliest_known=parsed.get("earliest_known"),
        )

    async def parse_catalog(self, reference: str) -> CatalogParseResult:
        """Parse catalog reference string."""
        result = await self.client.execute_prompt(
            capability=LLMCapability.CATALOG_PARSE,
            user_input=f"Parse: {reference}",
            context={"reference": reference},
        )
        
        parsed = result["content"]
        if not isinstance(parsed, dict):
             parsed = {}
        
        return CatalogParseResult(
            content=json.dumps(parsed),
            confidence=parsed.get("confidence", 0.8),
            cost_usd=result["cost"],
            model_used=result["model"],
            cached=result["cached"],
            reasoning=[],
            raw_reference=reference,
            catalog_system=parsed.get("catalog_system", ""),
            volume=parsed.get("volume"),
            number=parsed.get("number", ""),
            issuer=parsed.get("issuer"),
            mint=parsed.get("mint"),
            alternatives=parsed.get("alternatives", []),
        )
