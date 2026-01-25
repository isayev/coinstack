"""Pydantic schemas for catalog API endpoints."""
from typing import Any, Literal
from pydantic import BaseModel
from datetime import datetime


class LookupRequest(BaseModel):
    """Request to lookup a reference."""
    
    # Either provide structured reference
    system: str | None = None
    volume: str | None = None
    number: str | None = None
    
    # Or raw reference string
    raw_reference: str | None = None
    
    # Optional coin context for better matching
    context: dict | None = None


class CandidateResponse(BaseModel):
    """A candidate match from reconciliation."""
    
    external_id: str
    external_url: str | None = None
    confidence: float
    name: str | None = None
    description: str | None = None


class LookupResponse(BaseModel):
    """Response from reference lookup."""
    
    status: Literal["success", "not_found", "ambiguous", "deferred", "error"]
    external_id: str | None = None
    external_url: str | None = None
    confidence: float = 0.0
    candidates: list[CandidateResponse] | None = None
    payload: dict | None = None
    error_message: str | None = None
    
    # Reference type info (if cached)
    reference_type_id: int | None = None
    last_lookup: datetime | None = None
    cache_hit: bool = False


class ConflictResponse(BaseModel):
    """A conflict in enrichment diff."""
    
    field: str
    current: Any
    catalog: Any
    note: str | None = None


class EnrichmentDiffResponse(BaseModel):
    """Enrichment diff response."""
    
    fills: dict[str, Any]
    conflicts: dict[str, ConflictResponse]
    unchanged: list[str]
    fill_count: int
    conflict_count: int
    unchanged_count: int
    has_changes: bool


class EnrichRequest(BaseModel):
    """Request to enrich a coin."""
    
    dry_run: bool = True
    apply_conflicts: list[str] = []  # Field names to force-apply


class EnrichResponse(BaseModel):
    """Response from enrichment."""
    
    success: bool
    coin_id: int
    diff: EnrichmentDiffResponse
    applied_fills: list[str] = []
    applied_conflicts: list[str] = []
    error: str | None = None


class BulkEnrichRequest(BaseModel):
    """Request for bulk enrichment."""
    
    # Filters to select coins
    coin_ids: list[int] | None = None
    missing_fields: list[str] | None = None
    reference_system: str | None = None
    lookup_status: str | None = None  # "not_found" to retry failures
    category: str | None = None
    
    # Options
    dry_run: bool = True
    max_coins: int = 100  # Safety limit


class BulkEnrichResponse(BaseModel):
    """Response from bulk enrichment request."""
    
    job_id: str
    total_coins: int
    status: str = "queued"
    message: str | None = None


class JobStatusResponse(BaseModel):
    """Status of a bulk job."""
    
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: int = 0
    total: int = 0
    
    # Results (when completed)
    updated: int = 0
    conflicts: int = 0
    not_found: int = 0
    errors: int = 0
    
    # Details
    results: list[dict] | None = None
    error_message: str | None = None
    
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ReferenceTypeResponse(BaseModel):
    """Reference type data for API response."""
    
    id: int
    system: str
    local_ref: str
    local_ref_normalized: str | None = None
    external_id: str | None = None
    external_url: str | None = None
    lookup_status: str | None = None
    lookup_confidence: float | None = None
    last_lookup: datetime | None = None
    payload: dict | None = None
    
    class Config:
        from_attributes = True


class CoinReferenceResponse(BaseModel):
    """Coin reference data for API response."""
    
    id: int
    coin_id: int
    is_primary: bool = False
    plate_coin: bool = False
    variant_notes: str | None = None
    raw_reference: str | None = None
    
    # From linked reference type
    reference_type: ReferenceTypeResponse | None = None
    
    # Computed properties
    display_reference: str | None = None
    external_url: str | None = None
    lookup_status: str | None = None
    lookup_confidence: float | None = None
    
    class Config:
        from_attributes = True
