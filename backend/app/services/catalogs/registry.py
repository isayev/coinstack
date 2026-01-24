"""Catalog registry - routes to correct service by reference system."""
from typing import TYPE_CHECKING
from app.services.catalogs.base import CatalogService, CatalogResult

if TYPE_CHECKING:
    from app.services.catalogs.ocre import OCREService
    from app.services.catalogs.crro import CRROService
    from app.services.catalogs.rpc import RPCService


class CatalogRegistry:
    """
    Registry for catalog services.
    
    Routes lookups to the appropriate service based on reference system.
    Implements lazy loading of services.
    """
    
    _services: dict[str, CatalogService] = {}
    
    @classmethod
    def get_service(cls, system: str) -> CatalogService | None:
        """
        Get the catalog service for a given reference system.
        
        Args:
            system: Reference system identifier ("ric", "crawford", "rpc")
        
        Returns:
            CatalogService instance or None if not supported
        """
        system = system.lower()
        
        if system not in cls._services:
            cls._services[system] = cls._load_service(system)
        
        return cls._services.get(system)
    
    @classmethod
    def _load_service(cls, system: str) -> CatalogService | None:
        """Lazy load a catalog service."""
        if system == "ric":
            from app.services.catalogs.ocre import OCREService
            return OCREService()
        elif system == "crawford":
            from app.services.catalogs.crro import CRROService
            return CRROService()
        elif system == "rpc":
            from app.services.catalogs.rpc import RPCService
            return RPCService()
        # Add more systems as needed
        return None
    
    @classmethod
    def get_supported_systems(cls) -> list[str]:
        """Get list of supported reference systems."""
        return ["ric", "crawford", "rpc"]
    
    @classmethod
    async def lookup(
        cls, 
        system: str, 
        reference: str, 
        context: dict | None = None
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
        service = cls.get_service(system)
        
        if not service:
            return CatalogResult(
                status="error",
                error_message=f"Unsupported reference system: {system}"
            )
        
        try:
            # Build and execute reconciliation query
            query = await service.build_reconcile_query(reference, context)
            result = await service.reconcile(query)
            
            # If successful, fetch full type data
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
    def detect_system(cls, raw_reference: str) -> str | None:
        """
        Detect which reference system a raw reference belongs to.
        
        Tries each service's normalize_reference method.
        Returns the first system that can parse the reference.
        """
        for system in cls.get_supported_systems():
            service = cls.get_service(system)
            if service and service.normalize_reference(raw_reference):
                return system
        return None
    
    @classmethod
    def build_url(cls, system: str, external_id: str) -> str | None:
        """Build catalog URL for a given system and external ID."""
        service = cls.get_service(system)
        if service:
            return service.build_url(external_id)
        return None
