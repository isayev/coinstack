"""Catalog parse and systems API (parser expansion)."""
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from src.infrastructure.services.catalogs.parser import parse_catalog_reference_full
from src.infrastructure.services.catalogs.catalog_systems import SYSTEM_TO_DISPLAY
from src.infrastructure.web.routers.v2 import CatalogReferenceResponse

router = APIRouter(prefix="/api/v2/catalog", tags=["Catalog V2"])


class ParseCatalogRequest(BaseModel):
    raw: str


class ParseCatalogResponse(BaseModel):
    ref: Optional[CatalogReferenceResponse] = None
    confidence: float = 0.0
    warnings: List[str] = []
    alternatives: List[CatalogReferenceResponse] = []


@router.post(
    "/parse",
    response_model=ParseCatalogResponse,
    summary="Parse catalog reference string",
    description="Parse a raw reference string; returns ref, confidence, warnings. Use for import preview or reference field without persisting.",
)
def parse_catalog(request: ParseCatalogRequest) -> ParseCatalogResponse:
    raw = (request.raw or "").strip()
    if not raw:
        return ParseCatalogResponse(ref=None, confidence=0.0, warnings=["Empty input"])
    result = parse_catalog_reference_full(raw)
    ref_response = None
    if result.system and result.system in SYSTEM_TO_DISPLAY:
        catalog = SYSTEM_TO_DISPLAY[result.system]
        number = result.number or ""
        if result.subtype:
            number = f"{number}{result.subtype}"
        ref_response = CatalogReferenceResponse(
            catalog=catalog,
            number=number.strip() or "",
            volume=result.volume,
            raw_text=raw,
        )
    return ParseCatalogResponse(
        ref=ref_response,
        confidence=result.confidence,
        warnings=result.warnings or [],
        alternatives=[],
    )


@router.get(
    "/systems",
    summary="List catalog systems",
    description="Returns system key -> display name for all supported catalogs.",
)
def get_catalog_systems() -> dict:
    return dict(SYSTEM_TO_DISPLAY)
