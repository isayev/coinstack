"""RPC (Roman Provincial Coins) service - URL builder only (no API)."""
import re
import logging
from datetime import datetime

from app.services.catalogs.base import (
    CatalogService, CatalogResult, CatalogPayload
)

logger = logging.getLogger(__name__)


class RPCService(CatalogService):
    """
    RPC catalog service for Roman Provincial Coins.
    
    Note: RPC Online (rpc.ashmus.ox.ac.uk) does not have a public API.
    This service only generates URLs for manual lookup.
    """
    
    BASE_URL = "https://rpc.ashmus.ox.ac.uk"
    SYSTEM = "rpc"
    CACHE_TTL_DAYS = 365  # URLs don't change often
    
    # RPC volume info
    RPC_VOLUMES = {
        "I": {"arabic": 1, "period": "44 BC – AD 69"},
        "II": {"arabic": 2, "period": "AD 69–96"},
        "III": {"arabic": 3, "period": "AD 96–138"},
        "IV": {"arabic": 4, "period": "AD 138–192"},
        "V": {"arabic": 5, "period": "AD 193–211"},
        "VI": {"arabic": 6, "period": "AD 211–244"},
        "VII": {"arabic": 7, "period": "AD 244–268"},
        "VIII": {"arabic": 8, "period": "AD 268–276"},
        "IX": {"arabic": 9, "period": "AD 276–295"},
        "X": {"arabic": 10, "period": "AD 295–313"},
    }
    
    def normalize_reference(self, raw: str) -> str | None:
        """
        Convert RPC reference to normalized form.
        
        Examples:
            "RPC I 1234" -> "rpc.1.1234"
            "RPC 1 5678" -> "rpc.1.5678"
        """
        parsed = self.parse_reference(raw)
        if not parsed:
            return None
        
        vol = parsed.get("volume", "")
        num = parsed.get("number", "")
        
        return f"rpc.{vol}.{num}".lower()
    
    def parse_reference(self, raw: str) -> dict | None:
        """
        Parse RPC reference string into components.
        
        Handles various formats:
            - "RPC I 1234"
            - "RPC 1 5678"
            - "RPC I/1234" (slash separator)
        """
        if not raw:
            return None
        
        raw = raw.strip()
        
        # Pattern with Roman numeral volume
        pattern_roman = r"RPC\s+([IVX]+)[/\s]+(\d+)"
        match = re.match(pattern_roman, raw, re.IGNORECASE)
        
        if match:
            roman_vol = match.group(1).upper()
            number = match.group(2)
            arabic_vol = self._roman_to_arabic(roman_vol)
            
            return {
                "system": "rpc",
                "volume": str(arabic_vol),
                "volume_roman": roman_vol,
                "number": number,
            }
        
        # Pattern with Arabic numeral volume
        pattern_arabic = r"RPC\s+(\d+)[/\s]+(\d+)"
        match = re.match(pattern_arabic, raw, re.IGNORECASE)
        
        if match:
            arabic_vol = match.group(1)
            number = match.group(2)
            
            return {
                "system": "rpc",
                "volume": arabic_vol,
                "volume_roman": self._arabic_to_roman(int(arabic_vol)) if int(arabic_vol) <= 10 else arabic_vol,
                "number": number,
            }
        
        # Pattern without volume (just RPC number)
        pattern_no_vol = r"RPC\s+(\d+)$"
        match = re.match(pattern_no_vol, raw, re.IGNORECASE)
        
        if match:
            number = match.group(1)
            return {
                "system": "rpc",
                "volume": None,
                "number": number,
            }
        
        return None
    
    async def build_reconcile_query(
        self, 
        ref: str, 
        context: dict | None = None
    ) -> dict:
        """
        Build query dict - for RPC this is just for URL building.
        
        RPC doesn't have a reconciliation API.
        """
        parsed = self.parse_reference(ref)
        return {
            "raw": ref,
            "parsed": parsed,
            "context": context
        }
    
    async def reconcile(self, query: dict) -> CatalogResult:
        """
        RPC doesn't have a reconciliation API.
        
        Returns deferred status with URL for manual lookup.
        """
        parsed = query.get("parsed")
        
        if not parsed:
            return CatalogResult(
                status="error",
                error_message="Could not parse RPC reference"
            )
        
        # Build URL for manual lookup
        volume = parsed.get("volume")
        number = parsed.get("number")
        
        if volume and number:
            external_id = f"rpc-{volume}-{number}"
            external_url = self.build_url_from_parts(volume, number)
        elif number:
            # No volume - try generic search URL
            external_id = f"rpc-{number}"
            external_url = f"{self.BASE_URL}/search?q={number}"
        else:
            return CatalogResult(
                status="error",
                error_message="Missing RPC number"
            )
        
        return CatalogResult(
            status="deferred",
            external_id=external_id,
            external_url=external_url,
            confidence=0.0,  # No confidence since we can't verify
            error_message="RPC Online has no API - URL provided for manual lookup",
            lookup_timestamp=datetime.utcnow()
        )
    
    async def fetch_type_data(self, external_id: str) -> dict | None:
        """
        RPC doesn't have a JSON API.
        
        Returns None - data cannot be fetched automatically.
        """
        logger.info(f"RPC fetch not available for {external_id} - manual lookup required")
        return None
    
    def parse_payload(self, jsonld: dict) -> CatalogPayload:
        """
        RPC doesn't return JSON-LD.
        
        Returns empty payload.
        """
        return CatalogPayload()
    
    def build_url(self, external_id: str) -> str:
        """
        Generate RPC Online URL from external_id.
        
        External ID format: "rpc-{volume}-{number}"
        """
        # Parse external_id
        match = re.match(r"rpc-(\d+)-(\d+)", external_id, re.IGNORECASE)
        if match:
            volume = match.group(1)
            number = match.group(2)
            return self.build_url_from_parts(volume, number)
        
        # Fallback to search
        number = external_id.replace("rpc-", "").replace("rpc.", "")
        return f"{self.BASE_URL}/search?q={number}"
    
    def build_url_from_parts(self, volume: str, number: str) -> str:
        """Generate RPC URL from volume and number."""
        # RPC Online URL pattern
        return f"{self.BASE_URL}/coins/{volume}/{number}"
