"""Pydantic schemas for audit endpoints."""

from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, Field


# =============================================================================
# Enums and Types
# =============================================================================

TrustLevelType = Literal["authoritative", "high", "medium", "low", "untrusted"]
DifferenceType = Literal["exact", "equivalent", "within_tolerance", "overlapping", "adjacent", "partial", "format_diff", "mismatch", "missing"]
DiscrepancyStatus = Literal["pending", "accepted", "rejected", "ignored"]
EnrichmentStatus = Literal["pending", "applied", "rejected", "ignored"]
AuditRunStatus = Literal["running", "completed", "failed", "cancelled"]
AuditScope = Literal["single", "selected", "all"]


# =============================================================================
# Discrepancy Schemas
# =============================================================================

class DiscrepancyBase(BaseModel):
    """Base schema for discrepancy records."""
    field_name: str
    current_value: str | None = None
    auction_value: str | None = None
    similarity: float | None = None
    difference_type: DifferenceType | None = None
    comparison_notes: str | None = None
    source_house: str
    trust_level: TrustLevelType
    auto_acceptable: bool = False


class DiscrepancyCreate(DiscrepancyBase):
    """Schema for creating discrepancy records."""
    coin_id: int
    auction_data_id: int | None = None
    audit_run_id: int | None = None


class DiscrepancyOut(DiscrepancyBase):
    """Schema for discrepancy output."""
    id: int
    coin_id: int
    auction_data_id: int | None = None
    audit_run_id: int | None = None
    normalized_current: str | None = None
    normalized_auction: str | None = None
    status: DiscrepancyStatus
    resolved_at: datetime | None = None
    resolution: str | None = None
    resolution_notes: str | None = None
    created_at: datetime
    
    # Extended data from related tables
    source_url: str | None = None
    auction_images: list[str] = []
    coin_primary_image: str | None = None
    
    # Coin details for preview
    coin_ruler: str | None = None
    coin_denomination: str | None = None
    coin_metal: str | None = None
    coin_grade: str | None = None
    coin_category: str | None = None
    coin_mint_year_start: int | None = None
    coin_mint_year_end: int | None = None
    coin_is_circa: bool | None = None
    
    class Config:
        from_attributes = True


class DiscrepancyDetail(DiscrepancyOut):
    """Detailed discrepancy with coin info."""
    coin_name: str | None = None
    auction_house: str | None = None
    auction_date: str | None = None


class DiscrepancyResolveRequest(BaseModel):
    """Request to resolve a discrepancy."""
    resolution: Literal["accepted", "rejected", "ignored"]
    notes: str | None = None


class BulkResolveRequest(BaseModel):
    """Request to bulk resolve discrepancies."""
    discrepancy_ids: list[int]
    resolution: Literal["accepted", "rejected", "ignored"]
    notes: str | None = None


class PaginatedDiscrepancies(BaseModel):
    """Paginated discrepancy response."""
    items: list[DiscrepancyOut]
    total: int
    page: int
    per_page: int
    pages: int


# =============================================================================
# Enrichment Schemas
# =============================================================================

class EnrichmentBase(BaseModel):
    """Base schema for enrichment records."""
    field_name: str
    suggested_value: str
    source_house: str
    trust_level: TrustLevelType
    confidence: float | None = None
    auto_applicable: bool = False


class EnrichmentCreate(EnrichmentBase):
    """Schema for creating enrichment records."""
    coin_id: int
    auction_data_id: int | None = None
    audit_run_id: int | None = None


class EnrichmentOut(EnrichmentBase):
    """Schema for enrichment output."""
    id: int
    coin_id: int
    auction_data_id: int | None = None
    audit_run_id: int | None = None
    status: EnrichmentStatus
    applied: bool
    applied_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    
    # Extended data from related tables
    source_url: str | None = None
    auction_images: list[str] = []
    coin_primary_image: str | None = None
    
    # Coin details for preview
    coin_ruler: str | None = None
    coin_denomination: str | None = None
    coin_metal: str | None = None
    coin_grade: str | None = None
    coin_category: str | None = None
    coin_mint_year_start: int | None = None
    coin_mint_year_end: int | None = None
    coin_is_circa: bool | None = None
    
    class Config:
        from_attributes = True


class EnrichmentDetail(EnrichmentOut):
    """Detailed enrichment with coin info."""
    coin_name: str | None = None
    auction_house: str | None = None


class EnrichmentApplyRequest(BaseModel):
    """Request to apply enrichments."""
    enrichment_ids: list[int]


class EnrichmentRejectRequest(BaseModel):
    """Request to reject enrichments."""
    enrichment_ids: list[int]
    reason: str | None = None


class PaginatedEnrichments(BaseModel):
    """Paginated enrichment response."""
    items: list[EnrichmentOut]
    total: int
    page: int
    per_page: int
    pages: int


# =============================================================================
# Audit Run Schemas
# =============================================================================

class AuditRunCreate(BaseModel):
    """Schema for starting an audit run."""
    scope: AuditScope
    coin_ids: list[int] | None = None


class AuditRunOut(BaseModel):
    """Schema for audit run output."""
    id: int
    scope: AuditScope
    coin_ids: list[int] | None = None
    status: AuditRunStatus
    
    # Progress
    total_coins: int
    coins_audited: int
    coins_with_issues: int
    
    # Results
    discrepancies_found: int
    enrichments_found: int
    images_downloaded: int
    auto_accepted: int
    auto_applied: int
    
    # Timing
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    
    class Config:
        from_attributes = True


class AuditRunProgress(BaseModel):
    """Progress update for an audit run."""
    id: int
    status: AuditRunStatus
    progress_percent: float
    coins_audited: int
    total_coins: int
    discrepancies_found: int
    enrichments_found: int


# =============================================================================
# Audit Summary Schemas
# =============================================================================

class AuditSummary(BaseModel):
    """Summary statistics for audit dashboard."""
    pending_discrepancies: int
    pending_enrichments: int
    discrepancies_by_trust: dict[str, int]
    discrepancies_by_field: dict[str, int]
    discrepancies_by_source: dict[str, int]
    recent_runs: list[dict]


class CoinAuditSummary(BaseModel):
    """Audit summary for a single coin."""
    coin_id: int
    auctions_checked: int
    discrepancies: int
    enrichments: int
    message: str | None = None


# =============================================================================
# Image Download Schemas
# =============================================================================

class ImageDownloadRequest(BaseModel):
    """Request to download auction images."""
    auction_data_id: int | None = None  # If None, download from all auctions


class ImageDownloadResult(BaseModel):
    """Result of image download operation."""
    coin_id: int
    auctions_processed: int
    images_downloaded: int
    duplicates_skipped: int
    errors: int


# =============================================================================
# Filter Schemas
# =============================================================================

class DiscrepancyFilters(BaseModel):
    """Filters for discrepancy queries."""
    status: DiscrepancyStatus | None = None
    field_name: str | None = None
    source_house: str | None = None
    trust_level: TrustLevelType | None = None
    coin_id: int | None = None
    audit_run_id: int | None = None
    min_similarity: float | None = None
    max_similarity: float | None = None


class EnrichmentFilters(BaseModel):
    """Filters for enrichment queries."""
    status: EnrichmentStatus | None = None
    field_name: str | None = None
    source_house: str | None = None
    trust_level: TrustLevelType | None = None
    coin_id: int | None = None
    audit_run_id: int | None = None
    auto_applicable: bool | None = None
