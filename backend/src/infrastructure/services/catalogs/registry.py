"""Catalog registry - routes to correct service by reference system."""
from typing import Optional, List, Dict
from src.infrastructure.services.catalogs.base import CatalogService, CatalogResult
from src.infrastructure.services.catalogs.parser import parser

class CatalogRegistry:
    """
    Registry for catalog services.
    
    Routes lookups to the appropriate service based on reference system.
    Implements lazy loading of services.
    """
    
    _services: Dict[str, CatalogService] = {}
    
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
        
        Args:
            system: Reference system ("ric", "crawford", "rpc")
            reference: The reference string
            context: Optional coin context for disambiguation
        
        Returns:
            CatalogResult with lookup status and data
        """
        # Auto-detect system if not forced and reference looks specific
        if not system or system == "unknown" or system == "auto":
            detected = cls.detect_system(reference)
            if detected:
                system = detected
        
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
        
        Bypasses reconciliation and directly fetches type data.
        """
        # Validate/clean system
        system = system.lower()
        if system == "rrc": system = "crawford"
            
        service = cls.get_service(system)
        if not service:
             return CatalogResult(
                status="error", 
                error_message=f"Unsupported system: {system}"
            )
            
        try:
            # Generate URL if possible
            url = service.build_url(external_id)
            
            # Fetch data
            jsonld = await service.fetch_type_data(external_id)
            payload = None
            
            if jsonld:
                parsed = service.parse_payload(jsonld)
                payload = parsed.model_dump()
                
            return CatalogResult(
                status="success",
                external_id=external_id,
                external_url=url,
                confidence=1.0,
                payload=payload,
                raw=jsonld
            )
            
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
