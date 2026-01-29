"""Catalog registry - routes to correct service by reference system."""
import time
from typing import Optional, List, Dict, Tuple, Any
from src.infrastructure.services.catalogs.base import CatalogService, CatalogResult
from src.infrastructure.services.catalogs.parser import parser

# In-memory cache TTL (seconds); 24h
_CACHE_TTL_SEC = 86400
# Rate limit: max requests per window (per system)
_RATE_LIMIT_MAX = 30
_RATE_LIMIT_WINDOW_SEC = 60


class CatalogRegistry:
    """
    Registry for catalog services.
    
    Routes lookups to the appropriate service based on reference system.
    Implements lazy loading of services.
    """
    
    _services: Dict[str, CatalogService] = {}
    _cache: Dict[Tuple[str, ...], Tuple[Any, float]] = {}
    _rate_limit_timestamps: List[Tuple[float, str]] = []

    @classmethod
    def _cache_key_lookup(cls, system: str, reference: str) -> Tuple[str, str, str]:
        return ("lookup", system.lower().strip(), (reference or "").strip())

    @classmethod
    def _cache_key_get_by_id(cls, system: str, external_id: str) -> Tuple[str, str, str]:
        return ("get_by_id", system.lower().strip(), (external_id or "").strip())

    @classmethod
    def _cache_get(cls, key: Tuple[str, ...]) -> Optional[CatalogResult]:
        if key not in cls._cache:
            return None
        result, expiry = cls._cache[key]
        if time.monotonic() > expiry:
            del cls._cache[key]
            return None
        return result

    @classmethod
    def _cache_set(cls, key: Tuple[str, ...], result: CatalogResult) -> None:
        cls._cache[key] = (result, time.monotonic() + _CACHE_TTL_SEC)
        # Prune old entries occasionally (when cache is large)
        if len(cls._cache) > 500:
            now = time.monotonic()
            to_del = [k for k, (_, exp) in cls._cache.items() if exp < now]
            for k in to_del:
                del cls._cache[k]

    @classmethod
    def _rate_limit_acquire(cls, system: str) -> bool:
        """Return True if request allowed, False if rate limited."""
        now = time.monotonic()
        cutoff = now - _RATE_LIMIT_WINDOW_SEC
        cls._rate_limit_timestamps = [(t, s) for t, s in cls._rate_limit_timestamps if t > cutoff]
        system_lower = system.lower() if system else "default"
        count = sum(1 for _, s in cls._rate_limit_timestamps if s == system_lower)
        if count >= _RATE_LIMIT_MAX:
            return False
        cls._rate_limit_timestamps.append((now, system_lower))
        return True

    @classmethod
    def get_service(cls, system: str) -> Optional[CatalogService]:
        """
        Get the catalog service for a given reference system.
        
        Args:
            system: Reference system identifier ("ric", "crawford", "rpc")
        
        Returns:
            CatalogService instance or None if not supported
        """
        system = system.lower()
        if system == "rrc":
            system = "crawford"
        
        if system not in cls._services:
            cls._services[system] = cls._load_service(system)
        
        return cls._services.get(system)
    
    @classmethod
    def _load_service(cls, system: str) -> Optional[CatalogService]:
        """Lazy load a catalog service."""
        try:
            if system == "ric":
                from src.infrastructure.services.catalogs.ocre import OCREService
                return OCREService()
            elif system in ["crawford", "rrc"]:
                from src.infrastructure.services.catalogs.crro import CRROService
                return CRROService()
            elif system == "rpc":
                from src.infrastructure.services.catalogs.rpc import RPCService
                return RPCService()
        except ImportError as e:
            print(f"Failed to load service for {system}: {e}")
            return None
        return None
    
    @classmethod
    def get_supported_systems(cls) -> List[str]:
        """Get list of supported reference systems."""
        return ["ric", "rpc", "crawford"]
    
    @classmethod
    async def lookup(
        cls, 
        system: str, 
        reference: str, 
        context: Optional[Dict] = None
    ) -> CatalogResult:
        """
        Lookup a reference in the appropriate catalog.
        Uses in-memory cache (24h TTL) and per-system rate limit (30/min).
        """
        # Auto-detect system if not forced and reference looks specific
        if not system or system == "unknown" or system == "auto":
            detected = cls.detect_system(reference)
            if detected:
                system = detected

        cache_key = cls._cache_key_lookup(system, reference)
        cached = cls._cache_get(cache_key)
        if cached is not None:
            return cached

        if not cls._rate_limit_acquire(system):
            return CatalogResult(
                status="error",
                error_message="Catalog rate limit exceeded (30 requests per minute per system). Try again later.",
            )
        
        service = cls.get_service(system)
        
        if not service:
            return CatalogResult(
                status="error",
                error_message=f"Unsupported or undetected reference system: {system or reference}"
            )
        
        try:
            # Build and execute reconciliation query
            query = await service.build_reconcile_query(reference, context)
            result = await service.reconcile(query)
            
            # If successful, fetch full type data (Supported by OCRE, CRRO)
            # RPC doesn't support fetch_type_data but implements it returning None
            if result.status == "success" and result.external_id:
                jsonld = await service.fetch_type_data(result.external_id)
                if jsonld:
                    payload = service.parse_payload(jsonld)
                    result.payload = payload.model_dump()
                    result.raw = jsonld

            cls._cache_set(cache_key, result)
            return result
            
        except Exception as e:
            return CatalogResult(
                status="error",
                error_message=str(e)
            )
    
    @classmethod
    async def get_by_id(cls, system: str, external_id: str) -> CatalogResult:
        """
        Fetch full details for a specific catalog ID.
        Uses in-memory cache (24h TTL) and per-system rate limit (30/min).
        """
        system = system.lower()
        if system == "rrc":
            system = "crawford"

        cache_key = cls._cache_key_get_by_id(system, external_id)
        cached = cls._cache_get(cache_key)
        if cached is not None:
            return cached

        if not cls._rate_limit_acquire(system):
            return CatalogResult(
                status="error",
                error_message="Catalog rate limit exceeded (30 requests per minute per system). Try again later.",
            )
            
        service = cls.get_service(system)
        if not service:
             return CatalogResult(
                status="error", 
                error_message=f"Unsupported system: {system}"
            )
            
        try:
            url = service.build_url(external_id)
            jsonld = await service.fetch_type_data(external_id)
            payload = None
            if jsonld:
                parsed = service.parse_payload(jsonld)
                payload = parsed.model_dump()
                
            result = CatalogResult(
                status="success",
                external_id=external_id,
                external_url=url,
                confidence=1.0,
                payload=payload,
                raw=jsonld
            )
            cls._cache_set(cache_key, result)
            return result
            
        except Exception as e:
            return CatalogResult(
                status="error",
                error_message=f"Fetch failed: {str(e)}"
            )
    
    @classmethod
    def detect_system(cls, raw_reference: str) -> Optional[str]:
        """
        Detect which reference system a raw reference belongs to.
        
        Uses the Unified Reference Parser.
        """
        result = parser.parse(raw_reference)
        if result.system:
            return result.system
        return None
    
    @classmethod
    def build_url(cls, system: str, external_id: str) -> Optional[str]:
        """Build catalog URL for a given system and external ID."""
        service = cls.get_service(system)
        if service:
            return service.build_url(external_id)
        return None
