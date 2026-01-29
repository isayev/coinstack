"""OCRE (Online Coins of the Roman Empire) service for RIC lookups."""
import re
import json
import httpx
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.infrastructure.services.catalogs.base import (
    CatalogService, CatalogResult, CatalogPayload, CatalogCandidate
)

logger = logging.getLogger(__name__)


class OCREService(CatalogService):
    """
    OCRE catalog service for Roman Imperial Coinage (RIC).
    
    API Documentation: https://numismatics.org/ocre/apis
    """
    
    BASE_URL = "http://numismatics.org/ocre"
    RECONCILE_URL = f"{BASE_URL}/apis/reconcile"
    SYSTEM = "ric"
    CACHE_TTL_DAYS = 180  # 6 months
    
    # Request timeout in seconds
    TIMEOUT = 30.0
    
    def normalize_reference(self, raw: str) -> Optional[str]:
        """
        Convert RIC reference to normalized form.
        """
        from src.infrastructure.services.catalogs.parser import parser
        result = parser.parse(raw)
        if result.system == "ric":
            return result.normalized
        return None
    
    def parse_reference(self, raw: str) -> Optional[Dict]:
        """
        Parse RIC reference string using centralized parser.
        """
        from src.infrastructure.services.catalogs.parser import parser
        result = parser.parse(raw)
        
        if result.system != "ric":
            return None
        # Derive edition from volume (e.g. "I.2" or "II.3" for ²/³)
        edition = None
        if result.volume and "." in result.volume:
            tail = result.volume.split(".")[-1]
            edition = tail if tail in ("2", "3") else None
        return {
            "system": "ric",
            "volume": result.volume,
            "volume_roman": self._arabic_to_roman(int(result.volume)) if result.volume and result.volume.isdigit() else None,
            "number": result.number,
            "edition": edition,
        }
    
    async def build_reconcile_query(
        self, 
        ref: str, 
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Build OpenRefine reconciliation query for OCRE.
        
        OCRE reconciliation works best with queries like:
        - "RIC I(2) Augustus 207" (with edition and authority)
        - "RIC VII Rome 207" (with volume and mint)
        """
        # Parse reference to get components
        parsed = self.parse_reference(ref)
        
        if parsed:
            volume = parsed.get("volume_roman") or parsed.get("volume")
            number = parsed["number"]
            authority = context.get("ruler") or context.get("authority") if context else None
            # When volume has a dot (e.g. V.2 = Volume V Part 2), use as-is; don't add (edition)
            # When authority is provided (e.g. Diocletian), OCRE matches "RIC V Diocletian 325" not "RIC V(2) Diocletian 325" - omit edition
            # Otherwise edition (2)/(3) for single-segment volume (e.g. RIC I(2) 207)
            if volume and "." in str(volume):
                vol_str = volume
            elif authority:
                vol_str = volume
            else:
                edition = parsed.get("edition") or "2"
                vol_str = f"{volume}({edition})"
            query_str = f"RIC {vol_str} {number}"
            if authority:
                query_str = f"RIC {vol_str} {authority} {number}"
        else:
            # Fallback to original reference with authority
            query_str = ref
            if context:
                authority = context.get("ruler") or context.get("authority")
                if authority and authority.lower() not in ref.lower():
                    query_str = f"{ref} {authority}"
        
        return {"q0": {"query": query_str}}
    
    async def reconcile(self, query: Dict) -> CatalogResult:
        """
        Hit OCRE reconciliation API.
        
        Returns best match or list of candidates if ambiguous.
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                # OCRE reconciliation uses POST with form data
                # queries parameter must be JSON-encoded
                queries_json = json.dumps(query)
                response = await client.post(
                    self.RECONCILE_URL,
                    data={"queries": queries_json}
                )
                response.raise_for_status()
                
                # Parse response
                content = response.text.strip()
                
                # OCRE returns response without outer braces: "q0":{...}
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
                        error_message="Invalid response from OCRE API"
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
                        confidence=score / 100.0,  # Normalize to 0-1
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
                error_message="OCRE API timeout - will retry later",
                lookup_timestamp=datetime.now(timezone.utc)
            )
        except httpx.HTTPStatusError as e:
            return CatalogResult(
                status="error",
                error_message=f"OCRE API error: {e.response.status_code}",
                lookup_timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"OCRE reconcile error: {e}", exc_info=True)
            return CatalogResult(
                status="error",
                error_message=str(e),
                lookup_timestamp=datetime.now(timezone.utc)
            )
    
    async def fetch_type_data(self, external_id: str) -> Optional[Dict]:
        """
        Fetch full JSON-LD for a matched type.
        
        URL pattern: http://numismatics.org/ocre/id/{id}.jsonld
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
            logger.error(f"OCRE fetch error for {external_id}: {e}")
            return None
    
    def parse_payload(self, jsonld: Dict) -> CatalogPayload:
        """
        Extract structured fields from OCRE JSON-LD.
        """
        # Extract main type from @graph
        graph = jsonld.get("@graph", [])
        if not graph:
            # Fallback to root level if no @graph
            main = jsonld
        else:
            # Find the main type (not obverse/reverse fragments)
            main = graph[0]
            for item in graph:
                item_id = item.get("@id", "")
                if "#" not in item_id:  # Main type doesn't have # fragment
                    main = item
                    break
        
        # Build lookup dict for graph items by @id
        graph_lookup = {item.get("@id"): item for item in graph}
        
        def extract_label_from_uri(uri: str) -> Optional[str]:
            """Extract human-readable label from Nomisma URI."""
            if not uri or not isinstance(uri, str):
                return None
            # http://nomisma.org/id/denarius -> Denarius
            if "nomisma.org/id/" in uri:
                label = uri.split("/")[-1]
                return label.replace("_", " ").title()
            return uri.split("/")[-1]
        
        def get_value(obj: Any) -> Optional[str]:
            """Extract value from JSON-LD object (handles arrays and URIs)."""
            if isinstance(obj, list) and obj:
                obj = obj[0]  # Take first item
            if isinstance(obj, dict):
                # Check for @value (literal)
                if "@value" in obj:
                    return obj["@value"]
                # Check for @id (URI reference)
                if "@id" in obj:
                    return extract_label_from_uri(obj["@id"])
                return obj.get("label") or obj.get("prefLabel")
            if isinstance(obj, str):
                return extract_label_from_uri(obj) if obj.startswith("http") else obj
            return None
        
        def get_uri(obj: Any) -> Optional[str]:
            """Extract URI from JSON-LD object."""
            if isinstance(obj, list) and obj:
                obj = obj[0]
            if isinstance(obj, dict):
                return obj.get("@id")
            if isinstance(obj, str) and obj.startswith("http"):
                return obj
            return None
        
        def parse_date(date_obj: Any) -> Optional[int]:
            """Parse date from JSON-LD to year integer."""
            if isinstance(date_obj, list) and date_obj:
                date_obj = date_obj[0]
            if isinstance(date_obj, dict):
                val = date_obj.get("@value")
                if val:
                    try:
                        # Handle negative years (BCE) like "-0002"
                        val = str(val).strip()
                        if val.startswith("-"):
                            parts = val.lstrip("-").split("-")
                            return -int(parts[0])
                        return int(val.split("-")[0])
                    except (ValueError, IndexError):
                        pass
            if isinstance(date_obj, (int, float)):
                return int(date_obj)
            return None
        
        def get_nested_value(parent_ref: Any, field: str) -> Optional[str]:
            """Get field from a nested object referenced by URI."""
            if isinstance(parent_ref, list) and parent_ref:
                parent_ref = parent_ref[0]
            if isinstance(parent_ref, dict) and "@id" in parent_ref:
                uri = parent_ref["@id"]
                nested_obj = graph_lookup.get(uri, {})
                return get_value(nested_obj.get(field))
            return None
        
        # Extract fields using Nomisma ontology keys
        authority = main.get("nmo:hasAuthority") or main.get("hasAuthority")
        denomination = main.get("nmo:hasDenomination") or main.get("hasDenomination")
        mint = main.get("nmo:hasMint") or main.get("hasMint")
        material = main.get("nmo:hasMaterial") or main.get("hasMaterial")
        
        start_date = main.get("nmo:hasStartDate") or main.get("hasStartDate")
        end_date = main.get("nmo:hasEndDate") or main.get("hasEndDate")
        
        # Get obverse/reverse details from nested objects
        obv_ref = main.get("nmo:hasObverse") or main.get("hasObverse")
        rev_ref = main.get("nmo:hasReverse") or main.get("hasReverse")
        
        obv_desc = get_nested_value(obv_ref, "dc:description") or get_nested_value(obv_ref, "dcterms:description")
        obv_legend = get_nested_value(obv_ref, "nmo:hasLegend")
        obv_portrait = get_nested_value(obv_ref, "nmo:hasPortrait")
        
        rev_desc = get_nested_value(rev_ref, "dc:description") or get_nested_value(rev_ref, "dcterms:description")
        rev_legend = get_nested_value(rev_ref, "nmo:hasLegend")
        
        return CatalogPayload(
            authority=get_value(authority),
            authority_uri=get_uri(authority),
            denomination=get_value(denomination),
            denomination_uri=get_uri(denomination),
            mint=get_value(mint),
            mint_uri=get_uri(mint),
            material=get_value(material),
            material_uri=get_uri(material),
            date_from=parse_date(start_date),
            date_to=parse_date(end_date),
            obverse_description=obv_desc,
            obverse_legend=obv_legend,
            obverse_portrait=obv_portrait,
            reverse_description=rev_desc,
            reverse_legend=rev_legend,
            reverse_type=None,
            type_series=get_value(main.get("dcterms:source")),
        )
    
    def build_url(self, external_id: str) -> str:
        """Generate OCRE URL for a type ID."""
        return f"{self.BASE_URL}/id/{external_id}"
