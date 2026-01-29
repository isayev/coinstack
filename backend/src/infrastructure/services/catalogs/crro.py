"""CRRO (Coinage of the Roman Republic Online) service for Crawford lookups."""
import json
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from src.infrastructure.services.catalogs.base import (
    CatalogService, CatalogResult, CatalogPayload, CatalogCandidate
)
from src.infrastructure.services.catalogs.parser import parser

logger = logging.getLogger(__name__)


class CRROService(CatalogService):
    """
    CRRO catalog service for Roman Republican Coinage (Crawford).
    
    API Documentation: http://numismatics.org/crro/apis
    """
    
    BASE_URL = "http://numismatics.org/crro"
    RECONCILE_URL = f"{BASE_URL}/apis/reconcile"
    SYSTEM = "crawford"
    CACHE_TTL_DAYS = 180  # 6 months
    
    # Request timeout in seconds
    TIMEOUT = 30.0
    
    def normalize_reference(self, raw: str) -> Optional[str]:
        """
        Convert Crawford reference to normalized form.
        
        Examples:
            "Crawford 335/1c" -> "crawford.335.1c"
            "Cr. 335/1" -> "crawford.335.1"
            "RRC 335/1c" -> "crawford.335.1c"
        """
        result = parser.parse(raw)
        if result.system == "crawford":
            return result.normalized
        return None
    
    def parse_reference(self, raw: str) -> Optional[Dict]:
        """
        Parse Crawford reference string into components.
        
        Handles various formats using the centralized parser:
            - "Crawford 335/1c"
            - "Cr. 335/1"
            - "RRC 335/1c"
            - "335/1c" (if context suggests Crawford)
        """
        result = parser.parse(raw)
        if result.system != "crawford":
            return None
        # Derive main/sub from number (e.g. "335/1" -> 335, 1)
        number = result.number or ""
        parts = number.split("/")
        main_number = parts[0] if parts else None
        sub_number = parts[1] if len(parts) > 1 else None
        return {
            "system": "crawford",
            "number": result.number,
            "main_number": main_number,
            "sub_number": sub_number,
            "subtype": result.subtype,
        }
    
    async def build_reconcile_query(
        self, 
        ref: str, 
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Build OpenRefine reconciliation query for CRRO.
        
        CRRO uses the same reconciliation format as OCRE.
        Note: The reconciliation API doesn't support properties filtering.
        """
        # Clean up the reference for query
        parsed = self.parse_reference(ref)
        if parsed:
            # Reconstruct cleaner string for search
            # CRRO API prefers "335/1c" or "RRC 335/1c"
            # "Crawford 335/1c" yields no results
            
            # Use just the number + subtype if available
            main_num = parsed.get("number")
            subtype = parsed.get("subtype")
            
            if subtype and subtype not in main_num:
                 query_str = f"{main_num}{subtype}"
            else:
                 query_str = main_num
                 
            # Note: Experiment showed "335/1c" works best.
            # "RRC 335/1c" also works.
        else:
            query_str = ref
        
        return {"q0": {"query": query_str}}
    
    async def reconcile(self, query: Dict) -> CatalogResult:
        """
        Hit CRRO reconciliation API.
        
        Returns best match or list of candidates if ambiguous.
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                # CRRO reconciliation uses POST with form data
                queries_json = json.dumps(query)
                response = await client.post(
                    self.RECONCILE_URL,
                    data={"queries": queries_json}
                )
                response.raise_for_status()
                
                # Parse response
                content = response.text.strip()
                
                # CRRO returns response without outer braces: "q0":{...}
                # Need to wrap it in {} to make valid JSON
                if content.startswith('"q0"'):
                    content = '{' + content + '}'
                
                # Try to extract JSON from potential JSONP wrapper
                if content.startswith("("):
                    content = content[1:-1]
                
                data = json.loads(content)
                
                # Parse reconciliation response
                if "q0" not in data:
                    return CatalogResult(
                        status="error",
                        error_message="Invalid response from CRRO API"
                    )
                
                results = data["q0"].get("result", [])
                
                if not results:
                    return CatalogResult(
                        status="not_found",
                        lookup_timestamp=datetime.now(timezone.utc)
                    )
                
                # Convert to candidates
                candidates = []
                for r in results:
                    score = r.get("score", 0)
                    candidates.append(CatalogCandidate(
                        external_id=r.get("id", ""),
                        external_url=self.build_url(r.get("id", "")),
                        score=score,
                        confidence=score / 100.0,
                        name=r.get("name"),
                        description=r.get("description"),
                        match_type="exact" if r.get("match") else "partial"
                    ))
                
                # Check for exact match
                best = candidates[0]
                if best.confidence >= 0.8 or (results[0].get("match") is True):
                    return CatalogResult(
                        status="success",
                        external_id=best.external_id,
                        external_url=best.external_url,
                        confidence=best.confidence,
                        candidates=candidates if len(candidates) > 1 else None,
                        lookup_timestamp=datetime.now(timezone.utc)
                    )
                
                # Ambiguous - multiple candidates
                return CatalogResult(
                    status="ambiguous",
                    candidates=candidates,
                    confidence=best.confidence,
                    lookup_timestamp=datetime.now(timezone.utc)
                )
                
        except httpx.TimeoutException:
            return CatalogResult(
                status="deferred",
                error_message="CRRO API timeout - will retry later",
                lookup_timestamp=datetime.now(timezone.utc)
            )
        except httpx.HTTPStatusError as e:
            return CatalogResult(
                status="error",
                error_message=f"CRRO API error: {e.response.status_code}",
                lookup_timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"CRRO reconcile error: {e}", exc_info=True)
            return CatalogResult(
                status="error",
                error_message=str(e),
                lookup_timestamp=datetime.now(timezone.utc)
            )
    
    async def fetch_type_data(self, external_id: str) -> Optional[Dict]:
        """
        Fetch full JSON-LD for a matched type.
        
        URL pattern: http://numismatics.org/crro/id/{id}.jsonld
        """
        if not external_id:
            return None
        
        url = f"{self.BASE_URL}/id/{external_id}.jsonld"
        
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"CRRO fetch error for {external_id}: {e}")
            return None
    
    def parse_payload(self, jsonld: Dict) -> CatalogPayload:
        """
        Extract structured fields from CRRO JSON-LD.
        
        CRRO uses Nomisma ontology (nmo:) prefixes similar to OCRE.
        """
        def get_label(obj: Any) -> Optional[str]:
            """Extract label from JSON-LD object."""
            if isinstance(obj, dict):
                return obj.get("label") or obj.get("prefLabel") or obj.get("@value")
            if isinstance(obj, str):
                return obj
            if isinstance(obj, list) and obj:
                return get_label(obj[0])
            return None
        
        def get_uri(obj: Any) -> Optional[str]:
            """Extract URI from JSON-LD object."""
            if isinstance(obj, dict):
                return obj.get("@id") or obj.get("uri")
            if isinstance(obj, str) and obj.startswith("http"):
                return obj
            return None
        
        def parse_date(date_obj: Any) -> Optional[int]:
            """Parse date from JSON-LD to year integer."""
            if isinstance(date_obj, dict):
                val = date_obj.get("@value")
                if val:
                    try:
                        if val.startswith("-"):
                            return int(val.split("-")[1]) * -1
                            
                        # Handle "677" -> 677
                        return int(val.split("-")[0])
                    except (ValueError, IndexError):
                        pass
            if isinstance(date_obj, (int, float)):
                return int(date_obj)
            return None
        
        # Extract fields - CRRO uses similar structure to OCRE
        # but "authority" is typically the moneyer for Republic coins
        authority = jsonld.get("nmo:hasAuthority") or jsonld.get("hasAuthority")
        denomination = jsonld.get("nmo:hasDenomination") or jsonld.get("hasDenomination")
        mint = jsonld.get("nmo:hasMint") or jsonld.get("hasMint")
        material = jsonld.get("nmo:hasMaterial") or jsonld.get("hasMaterial")
        obverse = jsonld.get("nmo:hasObverse") or jsonld.get("hasObverse") or {}
        reverse = jsonld.get("nmo:hasReverse") or jsonld.get("hasReverse") or {}
        
        start_date = jsonld.get("nmo:hasStartDate") or jsonld.get("hasStartDate")
        end_date = jsonld.get("nmo:hasEndDate") or jsonld.get("hasEndDate")
        
        return CatalogPayload(
            authority=get_label(authority),  # Moneyer for Republic
            authority_uri=get_uri(authority),
            denomination=get_label(denomination),
            denomination_uri=get_uri(denomination),
            mint=get_label(mint),
            mint_uri=get_uri(mint),
            material=get_label(material),
            material_uri=get_uri(material),
            date_from=parse_date(start_date),
            date_to=parse_date(end_date),
            obverse_description=get_label(obverse.get("dc:description") or obverse.get("description")),
            obverse_legend=get_label(obverse.get("nmo:hasLegend") or obverse.get("hasLegend")),
            obverse_portrait=get_label(obverse.get("nmo:hasPortrait") or obverse.get("hasPortrait")),
            reverse_description=get_label(reverse.get("dc:description") or reverse.get("description")),
            reverse_legend=get_label(reverse.get("nmo:hasLegend") or reverse.get("hasLegend")),
            reverse_type=get_label(reverse.get("nmo:hasType") or reverse.get("hasType")),
            type_series="Crawford",
        )
    
    def build_url(self, external_id: str) -> str:
        """Generate CRRO URL for a type ID."""
        return f"{self.BASE_URL}/id/{external_id}"
