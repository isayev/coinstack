"""Legend expansion API router."""
from fastapi import APIRouter
from app.schemas.coin import LegendExpansionRequest, LegendExpansionResponse
from app.services.legend_dictionary import expand_legend, search_abbreviations, get_abbreviation

router = APIRouter(prefix="/legend", tags=["legend"])


@router.post("/expand", response_model=LegendExpansionResponse)
async def expand_legend_endpoint(request: LegendExpansionRequest):
    """
    Expand a Roman coin legend using the abbreviation dictionary.
    
    Returns the expanded legend with confidence score and unknown terms.
    If use_llm_fallback is true and there are unknown terms, method will be 'partial'.
    """
    result = expand_legend(request.legend, use_llm_fallback=request.use_llm_fallback)
    return LegendExpansionResponse(**result)


@router.get("/search")
async def search_abbreviations_endpoint(q: str):
    """
    Search for abbreviations by partial match.
    
    Returns matching abbreviations and their expansions.
    """
    results = search_abbreviations(q)
    return {
        "query": q,
        "results": [
            {"abbreviation": abbr, "expansion": exp}
            for abbr, exp in results
        ],
        "count": len(results),
    }


@router.get("/lookup/{abbreviation}")
async def lookup_abbreviation(abbreviation: str):
    """
    Look up a single abbreviation.
    
    Returns the expansion if found, or null if not in dictionary.
    """
    expansion = get_abbreviation(abbreviation)
    return {
        "abbreviation": abbreviation.upper(),
        "expansion": expansion,
        "found": expansion is not None,
    }
