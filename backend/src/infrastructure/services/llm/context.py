"""
Context Service - P1 Capability.

Handles:
- context_generate
"""
import json
import logging
import re
from typing import Optional, List, Dict, Any, Tuple

from src.domain.llm import LLMCapability, LLMResult
from src.infrastructure.services.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)

class ContextService:
    # Known catalog reference patterns
    CATALOG_PATTERNS = [
        r'\bRIC\s+[IVX]+(?:\.\d+|i)?\s*,?\s*\d+[a-z]?\b',
        r'\bRSC\s+\d+[a-z]?\b',
        r'\bRRC\s+\d+(?:/\d+)?[a-z]?\b',
        r'\bCrawford\s+\d+(?:/\d+)?[a-z]?\b',
        r'\bSear\s+\d+\b',
        r'\bSear\s+RCV\s+\d+\b',
        r'\bCohen\s+\d+\b',
        r'\bBMC(?:RE)?\s+(?:[IVXLC]+|\d+)?\s*,?\s*\d+\b',
        r'\bRPC\s+[IVXLC]+\s*,?\s*\d+\??\b',
        r'\bSNG\s+\w+\s+\d+\b',
        r'\bCalic[oó]\s+\d+[a-z]?\b',
        r'\bWoytek\s+\d+[a-z]?\b',
        r'\bHill\s+\d+\b',
        r'\bDOC\s+[IVXLC]+\s*,?\s*\d+\b',
        r'\bMIB\s+[IVXLC]+\s+\d+\b',
    ]

    def __init__(self, client: BaseLLMClient):
        self.client = client

    async def generate_context(self, coin_data: dict) -> LLMResult:
        """Generate historical context for this coin."""
        prompt = f"Generate historical context for this coin:\n{json.dumps(coin_data, indent=2)}"
        
        result = await self.client.execute_prompt(
            capability=LLMCapability.CONTEXT_GENERATE,
            user_input=prompt,
            context={"coin_id": coin_data.get("id")}, # If passed
        )
        
        content = result["content"]
        # If model didn't return JSON, it's raw text
        if isinstance(content, str):
            # Try to structure it manually if needed, or just wrap it
            # But prompt template usually enforces JSON.
            # Assuming JSON structure from prompt template
            pass
            
        parsed = content if isinstance(content, dict) else {"raw_content": str(content), "sections": {}}
        
        # Handle flat JSON response (where keys are sections)
        if isinstance(parsed, dict) and not parsed.get("sections"):
            sections = {}
            known_sections = [
                "EPIGRAPHY_AND_TITLES", "ICONOGRAPHY_AND_SYMBOLISM", "ARTISTIC_STYLE",
                "PROPAGANDA_AND_MESSAGING", "ECONOMIC_CONTEXT", "DIE_STUDIES_AND_VARIETIES",
                "ARCHAEOLOGICAL_CONTEXT", "TYPOLOGICAL_RELATIONSHIPS", "MILITARY_HISTORY",
                "HISTORICAL_CONTEXT", "NUMISMATIC_SIGNIFICANCE", "RARITY_ASSESSMENT"
            ]
            for key in list(parsed.keys()):
                if key in known_sections:
                    sections[key] = parsed.pop(key)
            if sections:
                parsed["sections"] = sections

        # Handle Markdown/Plain text response (extract sections from headers)
        if not parsed.get("sections") and isinstance(parsed.get("raw_content"), str):
            sections = {}
            raw = parsed["raw_content"]
            # Pattern to match ## SECTION_NAME followed by content
            # Matches from header to next header or end
            header_pattern = r'##\s+([A-Z_]+)\s*([\s\S]*?)(?=\n##|$)'
            matches = re.finditer(header_pattern, raw)
            for match in matches:
                key = match.group(1).strip()
                content_text = match.group(2).strip()
                if content_text:
                    sections[key] = content_text
            if sections:
                parsed["sections"] = sections

        # Extract Citations
        raw_content = parsed.get("raw_content", "")
        if not raw_content and parsed.get("sections"):
            raw_content = "\n\n".join(parsed["sections"].values())
            parsed["raw_content"] = raw_content  # Ensure it's in the dict for the router to save
            
        llm_citations = self._parse_citations(raw_content)
        existing = coin_data.get("references", [])
        new_refs, matched_refs = self._compare_references(llm_citations, existing)
        
        # Enrich result dict with citation analysis
        # Note: LLMResult is immutable, so we return a dict that the Facade/Router converts
        # or we return LLMResult and let Router handle the extra fields.
        # Ideally, ContextService returns a rich object.
        # But domain LLMResult is generic.
        
        # We'll attach the analysis to the result content for the caller to use
        parsed["llm_citations"] = llm_citations
        parsed["suggested_references"] = new_refs
        parsed["matched_references"] = matched_refs
        
        # Rarity extraction
        if "RARITY_ASSESSMENT" in parsed.get("sections", {}):
            parsed["rarity_info"] = self._parse_rarity(parsed["sections"]["RARITY_ASSESSMENT"])
            
        return LLMResult(
            content=json.dumps(parsed), # Serialize to string
            confidence=0.9,
            cost_usd=result["cost"],
            model_used=result["model"],
            cached=result["cached"],
            reasoning=[],
        )

    def _parse_citations(self, content: str) -> List[str]:
        citations = set()
        for pattern in self.CATALOG_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                cleaned = " ".join(match.split())
                citations.add(cleaned)
        return sorted(citations, key=lambda x: (x.split()[0], x))

    def _normalize_reference(self, ref: str) -> str:
        normalized = " ".join(ref.upper().split())
        normalized = normalized.replace(".", " ").replace(",", " ").replace("-", " ")
        return " ".join(normalized.split())

    def _compare_references(self, llm_refs: List[str], existing_refs: List[str]) -> Tuple[List[str], List[str]]:
        existing_normalized = {self._normalize_reference(r): r for r in existing_refs}
        new_suggestions = []
        matched = []
        
        for llm_ref in llm_refs:
            llm_norm = self._normalize_reference(llm_ref)
            found_match = False
            for exist_norm, exist_orig in existing_normalized.items():
                llm_parts = llm_norm.split()
                exist_parts = exist_norm.split()
                if len(llm_parts) >= 2 and len(exist_parts) >= 2:
                    if llm_parts[0] == exist_parts[0]: # System matches
                        llm_num = llm_parts[-1].rstrip("ABCDEFGHIJ")
                        exist_num = exist_parts[-1].rstrip("ABCDEFGHIJ")
                        if llm_num == exist_num:
                            found_match = True
                            matched.append(exist_orig)
                            break
            if not found_match:
                new_suggestions.append(llm_ref)
        return new_suggestions, matched

    def _parse_rarity(self, content: str) -> Dict[str, Any]:
        result = {"rarity_code": None, "rarity_description": None, "specimens_known": None, "source": None}
        for line in content.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip().upper()
                val = val.strip()
                if key == 'RARITY_CODE': result['rarity_code'] = val
                elif key == 'RARITY_DESCRIPTION': result['rarity_description'] = val
                elif key == 'SOURCE': result['source'] = val
                elif key == 'SPECIMENS_KNOWN': 
                    try: result['specimens_known'] = int(re.search(r'\d+', val).group())
                    except: pass
        return result
