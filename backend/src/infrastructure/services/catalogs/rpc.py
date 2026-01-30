"""RPC (Roman Provincial Coins) service - URL builder; optional HTML scraper."""
import re
import logging
from datetime import datetime
from typing import Dict, Optional, Any

from src.infrastructure.services.catalogs.base import (
    CatalogService, CatalogResult, CatalogPayload
)
from src.infrastructure.config import get_settings

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
    
    def normalize_reference(self, raw: str) -> Optional[str]:
        """Convert RPC reference to normalized form."""
        from src.infrastructure.services.catalogs.parser import parser
        result = parser.parse(raw)
        if result.system == "rpc":
            return result.normalized
        return None
    
    def parse_reference(self, raw: str) -> Optional[Dict]:
        """Parse RPC reference string using centralized parser."""
        from src.infrastructure.services.catalogs.parser import parser
        result = parser.parse(raw)
        
        if result.system != "rpc":
            return None
            
        return {
            "system": "rpc",
            "volume": result.volume,
            "number": (result.number or "") + (result.subtype or ""),
        }
    
    async def build_reconcile_query(
        self, 
        ref: str, 
        context: Optional[Dict] = None
    ) -> Dict:
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
    
    async def reconcile(self, query: Dict) -> CatalogResult:
        """
        RPC has no reconciliation API. When scraper is enabled, fetches type page
        and returns success with payload; otherwise returns deferred with URL.
        """
        parsed = query.get("parsed")

        if not parsed:
            return CatalogResult(
                status="error",
                error_message="Could not parse RPC reference"
            )

        volume = parsed.get("volume")
        number = parsed.get("number")

        if volume and number:
            external_id = f"rpc-{volume}-{number}"
            external_url = self.build_url_from_parts(volume, number)
        elif number:
            external_id = f"rpc-{number}"
            external_url = f"{self.BASE_URL}/search?q={number}"
        else:
            return CatalogResult(
                status="error",
                error_message="Missing RPC number"
            )

        settings = get_settings()
        if settings.CATALOG_SCRAPER_RPC_ENABLED and volume and number:
            from src.infrastructure.services.catalogs.rpc_scraper import (
                build_rpc_type_url,
                fetch_rpc_type_page,
            )
            url = build_rpc_type_url(volume, number)
            scrape = await fetch_rpc_type_page(
                url,
                user_agent=settings.CATALOG_SCRAPER_USER_AGENT,
                rate_limit_sec=settings.CATALOG_SCRAPER_RPC_RATE_LIMIT_SEC,
            )
            if scrape.status in ("full", "partial") and scrape.payload:
                confidence = 0.9 if scrape.status == "full" else 0.6
                return CatalogResult(
                    status="success",
                    external_id=external_id,
                    external_url=external_url,
                    confidence=confidence,
                    payload=scrape.payload.model_dump(),
                    error_message=scrape.message,
                    lookup_timestamp=datetime.utcnow(),
                )
            # disallowed, failed, or no payload: fall back to deferred
            msg = scrape.message or "RPC Online has no API - URL provided for manual lookup"
            return CatalogResult(
                status="deferred",
                external_id=external_id,
                external_url=external_url,
                confidence=0.0,
                error_message=msg,
                lookup_timestamp=datetime.utcnow(),
            )

        return CatalogResult(
            status="deferred",
            external_id=external_id,
            external_url=external_url,
            confidence=0.0,
            error_message="RPC Online has no API - URL provided for manual lookup",
            lookup_timestamp=datetime.utcnow(),
        )
    
    async def fetch_type_data(self, external_id: str) -> Optional[Dict[str, Any]]:
        """
        RPC has no JSON API. When scraper is enabled, fetches type page and returns
        payload dict for parse_payload; otherwise returns None.
        """
        settings = get_settings()
        if not settings.CATALOG_SCRAPER_RPC_ENABLED:
            logger.info("RPC fetch not available for %s - scraper disabled", external_id)
            return None
        match = re.match(r"rpc-([^-]+)-(\d+)", external_id, re.IGNORECASE)
        if not match:
            logger.info("RPC fetch: invalid external_id %s", external_id)
            return None
        volume, number = match.group(1), match.group(2)
        from src.infrastructure.services.catalogs.rpc_scraper import (
            build_rpc_type_url,
            fetch_rpc_type_page,
        )
        url = build_rpc_type_url(volume, number)
        scrape = await fetch_rpc_type_page(
            url,
            user_agent=settings.CATALOG_SCRAPER_USER_AGENT,
            rate_limit_sec=settings.CATALOG_SCRAPER_RPC_RATE_LIMIT_SEC,
        )
        if scrape.payload:
            return scrape.payload.model_dump()
        return None

    def parse_payload(self, jsonld: Dict[str, Any]) -> CatalogPayload:
        """
        RPC has no JSON-LD. Accepts scraper payload dict (CatalogPayload-shaped)
        or returns empty payload.
        """
        if not isinstance(jsonld, dict):
            return CatalogPayload()
        allowed = {k: jsonld[k] for k in CatalogPayload.model_fields if k in jsonld}
        if allowed:
            return CatalogPayload(**allowed)
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
        """Generate RPC URL from volume and number (volume can be Roman or Arabic)."""
        vol_upper = (volume or "").strip().upper()
        num_clean = (number or "").strip().split("/")[0].split(" ")[0]
        if vol_upper in self.RPC_VOLUMES:
            vol_str = str(self.RPC_VOLUMES[vol_upper]["arabic"])
        else:
            vol_str = volume
        return f"{self.BASE_URL}/coins/{vol_str}/{num_clean}"
