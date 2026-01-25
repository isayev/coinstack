"""OCRE (Online Coins of the Roman Empire) service for RIC lookups."""
import re
import json
import httpx
import logging
from datetime import datetime
from typing import Any

from app.services.catalogs.base import (
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
    
    # Volume mapping for RIC editions
    # RIC has multiple editions, indicated by superscript numbers
    RIC_VOLUMES = {
        "I": {"arabic": 1, "editions": ["1", "2"]},  # Augustus to Vitellius
        "II": {"arabic": 2, "editions": ["1", "3"]},  # Vespasian to Hadrian  
        "III": {"arabic": 3, "editions": ["1"]},      # Antoninus Pius to Commodus
        "IV": {"arabic": 4, "editions": ["1"]},       # Pertinax to Uranius Antoninus
        "V": {"arabic": 5, "editions": ["1"]},        # Valerian to Florian
        "VI": {"arabic": 6, "editions": ["1"]},       # Probus to Maximian
        "VII": {"arabic": 7, "editions": ["1"]},      # Constantine I
        "VIII": {"arabic": 8, "editions": ["1"]},     # Family of Constantine
        "IX": {"arabic": 9, "editions": ["1"]},       # Valentinian I to Theodosius I
        "X": {"arabic": 10, "editions": ["1"]},       # Arcadius to Zeno
    }
    
    def normalize_reference(self, raw: str) -> str | None:
        """
        Convert RIC reference to normalized form.
        
        Examples:
            "RIC I 207" -> "ric.1.207"
            "RIC II³ 430" -> "ric.2_3.430"
            "RIC 1 207" -> "ric.1.207"
        """
        parsed = self.parse_reference(raw)
        if not parsed:
            return None
        
        vol = parsed.get("volume", "")
        num = parsed.get("number", "")
        edition = parsed.get("edition")
        
        if edition:
            return f"ric.{vol}_{edition}.{num}".lower()
        return f"ric.{vol}.{num}".lower()
    
    def parse_reference(self, raw: str) -> dict | None:
        """
        Parse RIC reference string into components.
        
        Handles various formats:
            - "RIC I 207"
            - "RIC II³ 430" (with edition superscript)
            - "RIC 1 207" (Arabic numerals)
            - "RIC I² 207a" (with subtype)
        """
        if not raw:
            return None
        
        raw = raw.strip()
        
        # Pattern for RIC with Roman numeral volume and optional edition
        # Matches: RIC I 207, RIC II³ 430, RIC I² 207a
        pattern_roman = r"RIC\s+([IVX]+)([²³]|[23])?\s+(\d+[a-z]?)"
        match = re.match(pattern_roman, raw, re.IGNORECASE)
        
        if match:
            roman_vol = match.group(1).upper()
            edition_marker = match.group(2)
            number = match.group(3)
            
            # Convert Roman to Arabic
            arabic_vol = self._roman_to_arabic(roman_vol)
            
            # Parse edition marker
            edition = None
            if edition_marker:
                if edition_marker in ["²", "2"]:
                    edition = "2"
                elif edition_marker in ["³", "3"]:
                    edition = "3"
            
            return {
                "system": "ric",
                "volume": str(arabic_vol),
                "volume_roman": roman_vol,
                "number": number,
                "edition": edition,
            }
        
        # Pattern for RIC with Arabic numeral volume
        # Matches: RIC 1 207, RIC 2.3 430 (vol.edition)
        pattern_arabic = r"RIC\s+(\d+)(?:\.(\d))?\s+(\d+[a-z]?)"
        match = re.match(pattern_arabic, raw, re.IGNORECASE)
        
        if match:
            arabic_vol = match.group(1)
            edition = match.group(2)
            number = match.group(3)
            
            return {
                "system": "ric",
                "volume": arabic_vol,
                "volume_roman": self._arabic_to_roman(int(arabic_vol)),
                "number": number,
                "edition": edition,
            }
        
        return None
    
    async def build_reconcile_query(
        self, 
        ref: str, 
        context: dict | None = None
    ) -> dict:
        """
        Build OpenRefine reconciliation query for OCRE.
        
        OCRE reconciliation works best with queries like:
        - "RIC I(2) Augustus 207" (with edition and authority)
        - "RIC VII Rome 207" (with volume and mint)
        
        Note: OCRE's reconciliation API doesn't support properties filtering.
        """
        # Parse reference to get components
        parsed = self.parse_reference(ref)
        
        if parsed:
            volume = parsed.get("volume_roman") or parsed.get("volume")
            number = parsed["number"]
            # Default to second edition if not specified (most common)
            edition = parsed.get("edition") or "2"
            
            # Format: "RIC I(2) Augustus 207"
            vol_str = f"{volume}({edition})"
            query_str = f"RIC {vol_str} {number}"
            
            # Add authority if provided in context
            if context:
                authority = context.get("ruler") or context.get("authority")
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
    
    async def reconcile(self, query: dict) -> CatalogResult:
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
                        lookup_timestamp=datetime.utcnow()
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
                        lookup_timestamp=datetime.utcnow()
                    )
                
                # Ambiguous - multiple candidates
                return CatalogResult(
                    status="ambiguous",
                    candidates=candidates,
                    confidence=best.confidence,
                    lookup_timestamp=datetime.utcnow()
                )
                
        except httpx.TimeoutException:
            return CatalogResult(
                status="deferred",
                error_message="OCRE API timeout - will retry later",
                lookup_timestamp=datetime.utcnow()
            )
        except httpx.HTTPStatusError as e:
            return CatalogResult(
                status="error",
                error_message=f"OCRE API error: {e.response.status_code}",
                lookup_timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"OCRE reconcile error: {e}", exc_info=True)
            return CatalogResult(
                status="error",
                error_message=str(e),
                lookup_timestamp=datetime.utcnow()
            )
    
    async def fetch_type_data(self, external_id: str) -> dict | None:
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
    
    def parse_payload(self, jsonld: dict) -> CatalogPayload:
        """
        Extract structured fields from OCRE JSON-LD.
        
        OCRE uses Nomisma ontology (nmo:) prefixes.
        The structure is:
        {
            "@context": {...},
            "@graph": [
                {main type object},
                {obverse object},
                {reverse object}
            ]
        }
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
        
        def extract_label_from_uri(uri: str) -> str | None:
            """Extract human-readable label from Nomisma URI."""
            if not uri or not isinstance(uri, str):
                return None
            # http://nomisma.org/id/denarius -> Denarius
            if "nomisma.org/id/" in uri:
                label = uri.split("/")[-1]
                return label.replace("_", " ").title()
            return uri.split("/")[-1]
        
        def get_value(obj: Any) -> str | None:
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
        
        def get_uri(obj: Any) -> str | None:
            """Extract URI from JSON-LD object."""
            if isinstance(obj, list) and obj:
                obj = obj[0]
            if isinstance(obj, dict):
                return obj.get("@id")
            if isinstance(obj, str) and obj.startswith("http"):
                return obj
            return None
        
        def parse_date(date_obj: Any) -> int | None:
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
        
        def get_nested_value(parent_ref: Any, field: str) -> str | None:
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
            reverse_type=None,  # TODO: extract from nested
            type_series=get_value(main.get("dcterms:source")),
        )
    
    def build_url(self, external_id: str) -> str:
        """Generate OCRE URL for a type ID."""
        return f"{self.BASE_URL}/id/{external_id}"
