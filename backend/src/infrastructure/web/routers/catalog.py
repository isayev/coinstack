"""Catalog Router - dedicated non-LLM catalog endpoints."""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from src.infrastructure.services.catalogs.registry import CatalogRegistry
from src.infrastructure.services.catalogs.base import CatalogResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/catalog", tags=["Catalog"])

class CatalogLookupRequest(BaseModel):
    reference: Optional[str] = None
    external_id: Optional[str] = None
    system: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

@router.post(
    "/lookup", 
    response_model=CatalogResult,
    summary="Lookup reference in official catalogs",
    description="Perform a real-time lookup. Can search by reference string (reconcile) or by external_id (fetch)."
)
async def lookup_catalog(request: CatalogLookupRequest):
    """
    Lookup a catalog reference or fetch by ID.
    """
    try:
        # Case 1: Fetch by Specific ID (hydration)
        if request.external_id:
            system = request.system
            
            # If system not provided, try to guess from ID
            if not system:
                if "ric" in request.external_id.lower(): system = "ric"
                elif "rrc" in request.external_id.lower(): system = "crawford"
                elif "rpc" in request.external_id.lower(): system = "rpc"
                else: system = "ric" # Default fallback
            
            logger.info(f"Catalog fetch: {request.external_id} (System: {system})")
            return await CatalogRegistry.get_by_id(system, request.external_id)

        # Case 2: Search by Reference String
        if not request.reference:
            raise HTTPException(status_code=400, detail="Either 'reference' or 'external_id' must be provided")

        # Detect system if not provided
        system = request.system
        if not system or system == "auto":
             system = CatalogRegistry.detect_system(request.reference)
        
        if not system:
             # Basic fallback if unknown: try RIC then RPC
             if "RPC" in request.reference.upper():
                 system = "rpc"
             else:
                 system = "ric"

        logger.info(f"Catalog lookup: {request.reference} (System: {system})")
        
        result = await CatalogRegistry.lookup(
            system=system,
            reference=request.reference,
            context=request.context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Catalog lookup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
