from typing import Protocol, Optional, List, Dict, Any, Union
from datetime import date
from src.domain.coin import (
    Coin, ProvenanceEntry, ProvenanceEventType, GradingHistoryEntry,
    RarityAssessment, ReferenceConcordance, ExternalCatalogLink,
    LLMEnrichment, PromptTemplate, LLMFeedback, LLMUsageDaily,
    MarketPrice, MarketDataPoint, CoinValuation, WishlistItem,
    PriceAlert, WishlistMatch, Collection, CollectionCoin, CollectionStatistics,
    CensusSnapshot,
)
from src.domain.auction import AuctionLot
from src.domain.vocab import Issuer, Mint, VocabTerm, VocabType, NormalizationResult
from src.domain.vocab import IVocabRepository  # Re-export the unified interface
from src.domain.series import Series, SeriesSlot
from src.domain.llm import FuzzyMatch

# Note: IVocabRepository is defined in src.domain.vocab and re-exported here for convenience.
# The modern interface uses VocabTerm instead of legacy Issuer/Mint types.
# See ILegacyVocabRepository below for backward compatibility during migration.

class ICoinRepository(Protocol):
    def save(self, coin: Coin) -> Coin:
        """Saves a coin and returns the updated entity (with ID)."""
        ...

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        """Retrieves a coin by ID."""
        ...

    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        sort_by: Optional[str] = None, 
        sort_dir: str = "asc",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Coin]:
        """
        Retrieves a list of coins with pagination, sorting, and filtering.
        
        Supported filters:
        - category: str - exact match
        - metal: str - exact match
        - denomination: str - exact match
        - grading_state: str - exact match
        - grade_service: str - exact match
        - issuer: str - partial match (LIKE %value%)
        - year_start: int - coins with year_start >= value
        - year_end: int - coins with year_start <= value
        - weight_min: float - coins with weight >= value
        - weight_max: float - coins with weight <= value
        """
        ...
        
    def delete(self, coin_id: int) -> bool:
        """Deletes a coin by ID."""
        ...

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Returns the total number of coins, optionally filtered."""
        ...
    
    def get_by_reference(
        self,
        catalog: str,
        number: str,
        volume: Optional[str] = None
    ) -> List[Coin]:
        """
        Find coins by catalog reference.
        
        Args:
            catalog: Catalog system (RIC, Crawford, Sear, etc.)
            number: Reference number
            volume: Optional volume (e.g., II, V.1)
        
        Returns:
            List of coins matching the reference
        """
        ...


class IAuctionDataRepository(Protocol):
    """Repository interface for auction data persistence."""

    def upsert(self, lot: AuctionLot, coin_id: Optional[int] = None) -> int:
        """Insert or update auction lot data. Returns auction_data_id."""
        ...

    def get_by_coin_id(self, coin_id: int) -> Optional[AuctionLot]:
        """Get auction data linked to a coin."""
        ...

    def get_by_url(self, url: str) -> Optional[AuctionLot]:
        """Get auction data by unique URL."""
        ...

    def get_comparables(
        self,
        issuer: Optional[str] = None,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        limit: int = 10
    ) -> List[AuctionLot]:
        """Get comparable auction lots for price analysis."""
        ...


class ISeriesRepository(Protocol):
    """Repository interface for series/collection management."""

    def create(self, series: Series) -> Series:
        """Create a new series."""
        ...

    def get_by_id(self, series_id: int) -> Optional[Series]:
        """Retrieve a series by ID."""
        ...

    def get_by_slug(self, slug: str) -> Optional[Series]:
        """Retrieve a series by unique slug."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Series]:
        """List all series with pagination."""
        ...

    def update(self, series: Series) -> Series:
        """Update an existing series."""
        ...

    def delete(self, series_id: int) -> bool:
        """Delete a series by ID."""
        ...


class ILegacyVocabRepository(Protocol):
    """
    Legacy repository interface for vocabulary (issuers, mints).
    
    DEPRECATED: Use IVocabRepository from src.domain.vocab instead.
    This interface uses legacy Issuer/Mint types. New code should use
    the unified VocabTerm approach with IVocabRepository.
    """

    def get_issuer_by_id(self, issuer_id: int) -> Optional[Issuer]:
        """Get issuer by ID."""
        ...

    def get_issuer_by_name(self, canonical_name: str) -> Optional[Issuer]:
        """Get issuer by canonical name."""
        ...

    def create_issuer(self, issuer: Issuer) -> Issuer:
        """Create a new issuer."""
        ...

    def list_issuers(
        self,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Issuer]:
        """List issuers with optional search and pagination."""
        ...

    def get_mint_by_id(self, mint_id: int) -> Optional[Mint]:
        """Get mint by ID."""
        ...

    def get_mint_by_name(self, canonical_name: str) -> Optional[Mint]:
        """Get mint by canonical name."""
        ...

    def create_mint(self, mint: Mint) -> Mint:
        """Create a new mint."""
        ...

    def list_mints(
        self,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Mint]:
        """List mints with optional search and pagination."""
        ...
    
    # -------------------------------------------------------------------------
    # LLM Integration Methods (for fallback when LLM unavailable)
    # -------------------------------------------------------------------------
    
    def get_by_canonical(
        self,
        vocab_type: str,
        canonical_name: str
    ) -> Optional[Union[Issuer, Mint]]:
        """
        Get vocab term by canonical name and type.
        
        Args:
            vocab_type: "issuer" or "mint"
            canonical_name: Exact canonical name to match
        
        Returns:
            Issuer or Mint if found, None otherwise
        """
        ...
    
    def fuzzy_search(
        self,
        query: str,
        vocab_type: str,
        limit: int = 5,
        min_score: float = 0.5
    ) -> List[FuzzyMatch]:
        """
        Fuzzy search for vocabulary terms.

        Used as fallback when LLM is unavailable. Uses string similarity
        to find potential matches.

        Args:
            query: Search query string
            vocab_type: "issuer" or "mint"
            limit: Maximum number of results
            min_score: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of FuzzyMatch results sorted by score descending
        """
        ...


class IProvenanceRepository(Protocol):
    """
    Repository interface for provenance (pedigree) record management.

    Provenance tracks the ownership history of a coin, from earliest known
    appearance through to current ownership (ACQUISITION event type).
    """

    def get_by_coin_id(self, coin_id: int) -> List[ProvenanceEntry]:
        """
        Get all provenance entries for a coin, ordered by sort_order.

        Returns complete pedigree timeline from earliest to most recent.
        """
        ...

    def get_by_id(self, provenance_id: int) -> Optional[ProvenanceEntry]:
        """Get a specific provenance entry by ID."""
        ...

    def create(self, coin_id: int, entry: ProvenanceEntry) -> ProvenanceEntry:
        """
        Create a new provenance entry for a coin.

        Returns entry with ID assigned.
        """
        ...

    def create_bulk(self, coin_id: int, entries: List[ProvenanceEntry]) -> List[ProvenanceEntry]:
        """Create multiple provenance entries efficiently."""
        ...

    def update(self, provenance_id: int, entry: ProvenanceEntry) -> Optional[ProvenanceEntry]:
        """Update an existing provenance entry."""
        ...

    def delete(self, provenance_id: int) -> bool:
        """Delete a provenance entry by ID."""
        ...

    def find_by_source(
        self,
        event_type: ProvenanceEventType,
        source_name: str,
        event_date: Optional[date] = None
    ) -> List[ProvenanceEntry]:
        """Find provenance entries by source details (for deduplication)."""
        ...

    def get_acquisition_by_coin(self, coin_id: int) -> Optional[ProvenanceEntry]:
        """Get the acquisition (current ownership) entry for a coin, if exists."""
        ...

    def get_earliest_by_coin(self, coin_id: int) -> Optional[ProvenanceEntry]:
        """Get the earliest known provenance entry for a coin."""
        ...


class IGradingHistoryRepository(Protocol):
    """
    Repository interface for grading history (TPG lifecycle) management.

    Tracks the complete grading history of a coin from raw through
    slabbing, crossovers, regrades, and crack-outs.
    """

    def get_by_coin_id(self, coin_id: int) -> List[GradingHistoryEntry]:
        """
        Get all grading history entries for a coin, ordered by sequence_order.

        Returns complete timeline from initial grading to current state.
        """
        ...

    def get_by_id(self, entry_id: int) -> Optional[GradingHistoryEntry]:
        """Get a specific grading history entry by ID."""
        ...

    def create(self, coin_id: int, entry: GradingHistoryEntry) -> GradingHistoryEntry:
        """
        Create a new grading history entry for a coin.

        Returns entry with ID assigned.
        """
        ...

    def update(self, entry_id: int, entry: GradingHistoryEntry) -> Optional[GradingHistoryEntry]:
        """Update an existing grading history entry."""
        ...

    def delete(self, entry_id: int) -> bool:
        """Delete a grading history entry by ID."""
        ...

    def set_current(self, coin_id: int, entry_id: int) -> bool:
        """
        Mark a grading history entry as the current grading state.

        Clears is_current flag on all other entries for this coin.
        Returns True if successful, False if entry not found.
        """
        ...

    def get_current(self, coin_id: int) -> Optional[GradingHistoryEntry]:
        """Get the current (active) grading state for a coin."""
        ...


class IRarityAssessmentRepository(Protocol):
    """
    Repository interface for multi-source rarity assessment management.

    Supports tracking rarity from multiple sources (catalogs, census data,
    market analysis) with grade-conditional support.
    """

    def get_by_coin_id(self, coin_id: int) -> List[RarityAssessment]:
        """
        Get all rarity assessments for a coin.

        Returns assessments ordered by is_primary desc, then by source_date desc.
        """
        ...

    def get_by_id(self, assessment_id: int) -> Optional[RarityAssessment]:
        """Get a specific rarity assessment by ID."""
        ...

    def create(self, coin_id: int, assessment: RarityAssessment) -> RarityAssessment:
        """
        Create a new rarity assessment for a coin.

        Returns assessment with ID assigned.
        """
        ...

    def update(self, assessment_id: int, assessment: RarityAssessment) -> Optional[RarityAssessment]:
        """Update an existing rarity assessment."""
        ...

    def delete(self, assessment_id: int) -> bool:
        """Delete a rarity assessment by ID."""
        ...

    def set_primary(self, coin_id: int, assessment_id: int) -> bool:
        """
        Mark a rarity assessment as the primary assessment.

        Clears is_primary flag on all other assessments for this coin.
        Returns True if successful, False if assessment not found.
        """
        ...

    def get_primary(self, coin_id: int) -> Optional[RarityAssessment]:
        """Get the primary rarity assessment for a coin."""
        ...


class IConcordanceRepository(Protocol):
    """
    Repository interface for reference concordance management.

    Concordance links equivalent references across different catalog systems.
    Example: RIC 207 = RSC 112 = BMC 298 = Cohen 169
    """

    def get_by_group_id(self, group_id: str) -> List[ReferenceConcordance]:
        """Get all concordance entries in a group."""
        ...

    def get_by_reference_type_id(self, reference_type_id: int) -> List[ReferenceConcordance]:
        """Get concordance entries for a specific reference type."""
        ...

    def create(self, concordance: ReferenceConcordance) -> ReferenceConcordance:
        """Create a new concordance entry. Returns entry with ID assigned."""
        ...

    def create_group(
        self,
        reference_type_ids: List[int],
        source: str = "user",
        confidence: float = 1.0,
        notes: Optional[str] = None
    ) -> str:
        """
        Create a concordance group linking multiple reference types.

        Returns the generated concordance_group_id (UUID).
        """
        ...

    def delete(self, concordance_id: int) -> bool:
        """Delete a concordance entry by ID."""
        ...

    def delete_group(self, group_id: str) -> int:
        """Delete all concordance entries in a group. Returns count deleted."""
        ...

    def find_equivalent_references(self, reference_type_id: int) -> List[int]:
        """
        Find all reference_type_ids equivalent to the given reference.

        Follows concordance links to find all equivalent references.
        """
        ...


class IExternalCatalogLinkRepository(Protocol):
    """
    Repository interface for external catalog link management.

    Links reference types to online databases like OCRE, Nomisma, CRRO, RPC Online.
    """

    def get_by_reference_type_id(self, reference_type_id: int) -> List[ExternalCatalogLink]:
        """Get all external links for a reference type."""
        ...

    def get_by_source(
        self,
        reference_type_id: int,
        catalog_source: str
    ) -> Optional[ExternalCatalogLink]:
        """Get a specific external link by reference type and source."""
        ...

    def create(self, link: ExternalCatalogLink) -> ExternalCatalogLink:
        """Create a new external catalog link. Returns link with ID assigned."""
        ...

    def upsert(self, link: ExternalCatalogLink) -> ExternalCatalogLink:
        """Create or update an external catalog link."""
        ...

    def update(self, link_id: int, link: ExternalCatalogLink) -> Optional[ExternalCatalogLink]:
        """Update an existing external catalog link."""
        ...

    def delete(self, link_id: int) -> bool:
        """Delete an external catalog link by ID."""
        ...

    def find_by_external_id(
        self,
        catalog_source: str,
        external_id: str
    ) -> Optional[ExternalCatalogLink]:
        """Find an external link by source and external ID."""
        ...

    def list_pending_sync(self, limit: int = 100) -> List[ExternalCatalogLink]:
        """Get external links pending synchronization."""
        ...

    def mark_synced(
        self,
        link_id: int,
        external_data: Optional[str] = None
    ) -> bool:
        """Mark an external link as synced with optional data."""
        ...


# --- Phase 4: LLM Architecture Repositories ---

class ILLMEnrichmentRepository(Protocol):
    """
    Repository interface for LLM enrichment management.

    Centralized storage for all LLM-generated content with versioning,
    review workflow, and cost tracking.
    """

    def get_by_id(self, enrichment_id: int) -> Optional[LLMEnrichment]:
        """Get a specific enrichment by ID."""
        ...

    def get_by_coin_id(
        self,
        coin_id: int,
        capability: Optional[str] = None,
        review_status: Optional[str] = None
    ) -> List[LLMEnrichment]:
        """
        Get enrichments for a coin, optionally filtered by capability and status.

        Returns enrichments ordered by created_at desc.
        """
        ...

    def get_current(self, coin_id: int, capability: str) -> Optional[LLMEnrichment]:
        """
        Get the current (active) enrichment for a coin/capability.

        Returns the most recent approved enrichment, or pending if none approved.
        """
        ...

    def get_by_input_hash(
        self,
        capability: str,
        input_hash: str
    ) -> Optional[LLMEnrichment]:
        """
        Get enrichment by input hash for cache lookup.

        Used to check if we already have a result for this exact input.
        """
        ...

    def create(self, enrichment: LLMEnrichment) -> LLMEnrichment:
        """Create a new enrichment. Returns enrichment with ID assigned."""
        ...

    def update(
        self,
        enrichment_id: int,
        enrichment: LLMEnrichment
    ) -> Optional[LLMEnrichment]:
        """Update an existing enrichment."""
        ...

    def update_review_status(
        self,
        enrichment_id: int,
        review_status: str,
        reviewed_by: Optional[str] = None,
        review_notes: Optional[str] = None
    ) -> bool:
        """Update the review status of an enrichment."""
        ...

    def supersede(
        self,
        old_enrichment_id: int,
        new_enrichment_id: int
    ) -> bool:
        """Mark an enrichment as superseded by a newer one."""
        ...

    def delete(self, enrichment_id: int) -> bool:
        """Delete an enrichment by ID."""
        ...

    def list_pending_review(
        self,
        capability: Optional[str] = None,
        limit: int = 100
    ) -> List[LLMEnrichment]:
        """Get enrichments pending review."""
        ...

    def list_by_capability(
        self,
        capability: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LLMEnrichment]:
        """List all enrichments for a capability with pagination."""
        ...


class IPromptTemplateRepository(Protocol):
    """
    Repository interface for prompt template management.

    Enables versioning and A/B testing of prompts.
    """

    def get_by_id(self, template_id: int) -> Optional[PromptTemplate]:
        """Get a specific template by ID."""
        ...

    def get_active(
        self,
        capability: str,
        variant_name: str = "default"
    ) -> Optional[PromptTemplate]:
        """Get the active template for a capability and variant."""
        ...

    def get_latest_version(self, capability: str) -> Optional[PromptTemplate]:
        """Get the highest version template for a capability."""
        ...

    def list_by_capability(
        self,
        capability: str,
        include_deprecated: bool = False
    ) -> List[PromptTemplate]:
        """List all templates for a capability."""
        ...

    def list_active_variants(self, capability: str) -> List[PromptTemplate]:
        """List all active variants for A/B testing."""
        ...

    def create(self, template: PromptTemplate) -> PromptTemplate:
        """Create a new template. Returns template with ID assigned."""
        ...

    def update(
        self,
        template_id: int,
        template: PromptTemplate
    ) -> Optional[PromptTemplate]:
        """Update an existing template."""
        ...

    def deprecate(self, template_id: int) -> bool:
        """Mark a template as deprecated."""
        ...

    def delete(self, template_id: int) -> bool:
        """Delete a template by ID."""
        ...


class ILLMFeedbackRepository(Protocol):
    """
    Repository interface for LLM feedback management.

    Tracks user corrections and quality feedback.
    """

    def get_by_id(self, feedback_id: int) -> Optional[LLMFeedback]:
        """Get a specific feedback entry by ID."""
        ...

    def get_by_enrichment_id(self, enrichment_id: int) -> List[LLMFeedback]:
        """Get all feedback for an enrichment."""
        ...

    def create(self, feedback: LLMFeedback) -> LLMFeedback:
        """Create a new feedback entry. Returns feedback with ID assigned."""
        ...

    def delete(self, feedback_id: int) -> bool:
        """Delete a feedback entry by ID."""
        ...

    def list_by_type(
        self,
        feedback_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LLMFeedback]:
        """List feedback entries by type."""
        ...

    def list_by_capability(
        self,
        capability: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LLMFeedback]:
        """List feedback for enrichments of a specific capability."""
        ...

    def count_by_type(self, feedback_type: str) -> int:
        """Count feedback entries by type."""
        ...


class ILLMUsageRepository(Protocol):
    """
    Repository interface for LLM usage metrics.

    Aggregated daily metrics for cost monitoring and analytics.
    """

    def get_daily(
        self,
        date: str,
        capability: str,
        model_id: str
    ) -> Optional[LLMUsageDaily]:
        """Get usage metrics for a specific day/capability/model."""
        ...

    def upsert(self, usage: LLMUsageDaily) -> LLMUsageDaily:
        """Create or update daily usage metrics."""
        ...

    def increment(
        self,
        date: str,
        capability: str,
        model_id: str,
        request_count: int = 1,
        cache_hits: int = 0,
        error_count: int = 0,
        cost_usd: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> LLMUsageDaily:
        """Atomically increment usage counters."""
        ...

    def list_by_date_range(
        self,
        start_date: str,
        end_date: str,
        capability: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> List[LLMUsageDaily]:
        """List usage metrics for a date range."""
        ...

    def get_total_cost(
        self,
        start_date: str,
        end_date: str,
        capability: Optional[str] = None
    ) -> float:
        """Get total cost for a date range."""
        ...

    def get_capability_summary(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get usage summary grouped by capability.

        Returns dict with totals for each capability.
        """
        ...


# --- Phase 5: Market Tracking & Wishlists Repositories ---

class IMarketPriceRepository(Protocol):
    """
    Repository interface for market price aggregate management.

    Tracks type-level pricing across multiple sales/observations.
    """

    def get_by_id(self, price_id: int) -> Optional[MarketPrice]:
        """Get a market price by ID."""
        ...

    def get_by_attribution_key(self, attribution_key: str) -> Optional[MarketPrice]:
        """Get market price by attribution key."""
        ...

    def list_all(
        self,
        issuer: Optional[str] = None,
        denomination: Optional[str] = None,
        metal: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketPrice]:
        """List market prices with optional filters."""
        ...

    def count(
        self,
        issuer: Optional[str] = None,
        denomination: Optional[str] = None,
        metal: Optional[str] = None,
    ) -> int:
        """Count market prices matching filters."""
        ...

    def create(self, market_price: MarketPrice) -> MarketPrice:
        """Create a new market price. Returns price with ID assigned."""
        ...

    def update(self, price_id: int, market_price: MarketPrice) -> Optional[MarketPrice]:
        """Update an existing market price."""
        ...

    def delete(self, price_id: int) -> bool:
        """Delete a market price by ID."""
        ...


class IMarketDataPointRepository(Protocol):
    """
    Repository interface for market data point management.

    Individual price observations feeding market aggregates.
    """

    def get_by_id(self, data_point_id: int) -> Optional[MarketDataPoint]:
        """Get a data point by ID."""
        ...

    def get_by_market_price_id(
        self,
        market_price_id: int,
        source_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketDataPoint]:
        """Get all data points for a market price."""
        ...

    def get_recent(self, market_price_id: int, days: int = 365) -> List[MarketDataPoint]:
        """Get recent data points within a date range."""
        ...

    def create(self, market_price_id: int, data_point: MarketDataPoint) -> MarketDataPoint:
        """Create a new data point. Returns point with ID assigned."""
        ...

    def update(self, data_point_id: int, data_point: MarketDataPoint) -> Optional[MarketDataPoint]:
        """Update an existing data point."""
        ...

    def delete(self, data_point_id: int) -> bool:
        """Delete a data point by ID."""
        ...

    def count_by_market_price_id(self, market_price_id: int) -> int:
        """Count data points for a market price."""
        ...


class ICoinValuationRepository(Protocol):
    """
    Repository interface for coin valuation management.

    Per-coin valuation snapshots with trend tracking.
    """

    def get_by_id(self, valuation_id: int) -> Optional[CoinValuation]:
        """Get a valuation by ID."""
        ...

    def get_by_coin_id(
        self,
        coin_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CoinValuation]:
        """Get all valuations for a coin."""
        ...

    def get_latest(self, coin_id: int) -> Optional[CoinValuation]:
        """Get the most recent valuation for a coin."""
        ...

    def get_latest_batch(self, coin_ids: List[int]) -> Dict[int, CoinValuation]:
        """
        Get the most recent valuations for multiple coins in a single query.

        Args:
            coin_ids: List of coin IDs to get valuations for

        Returns:
            Dict mapping coin_id to its latest CoinValuation (missing coins not included)
        """
        ...

    def create(self, coin_id: int, valuation: CoinValuation) -> CoinValuation:
        """Create a new valuation. Returns valuation with ID assigned."""
        ...

    def update(self, valuation_id: int, valuation: CoinValuation) -> Optional[CoinValuation]:
        """Update an existing valuation."""
        ...

    def delete(self, valuation_id: int) -> bool:
        """Delete a valuation by ID."""
        ...

    def count_by_coin_id(self, coin_id: int) -> int:
        """Count valuations for a specific coin."""
        ...

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Calculate portfolio-wide valuation summary."""
        ...


class IWishlistItemRepository(Protocol):
    """
    Repository interface for wishlist item management.

    Acquisition targets with matching criteria.
    """

    def get_by_id(self, item_id: int) -> Optional[WishlistItem]:
        """Get a wishlist item by ID."""
        ...

    def list_all(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WishlistItem]:
        """List wishlist items with optional filters."""
        ...

    def count(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        category: Optional[str] = None,
    ) -> int:
        """Count wishlist items matching filters."""
        ...

    def create(self, item: WishlistItem) -> WishlistItem:
        """Create a new wishlist item. Returns item with ID assigned."""
        ...

    def update(self, item_id: int, item: WishlistItem) -> Optional[WishlistItem]:
        """Update an existing wishlist item."""
        ...

    def delete(self, item_id: int) -> bool:
        """Delete a wishlist item by ID."""
        ...

    def mark_acquired(
        self,
        item_id: int,
        coin_id: int,
        acquired_price: Optional[Any] = None,
    ) -> Optional[WishlistItem]:
        """Mark a wishlist item as acquired."""
        ...


class IPriceAlertRepository(Protocol):
    """
    Repository interface for price alert management.

    User-configured alerts for price thresholds and availability.
    """

    def get_by_id(self, alert_id: int) -> Optional[PriceAlert]:
        """Get an alert by ID."""
        ...

    def get_active(self, skip: int = 0, limit: int = 100) -> List[PriceAlert]:
        """Get all active alerts."""
        ...

    def get_by_coin_id(self, coin_id: int) -> List[PriceAlert]:
        """Get all alerts for a specific coin."""
        ...

    def get_by_wishlist_item_id(self, wishlist_item_id: int) -> List[PriceAlert]:
        """Get all alerts for a wishlist item."""
        ...

    def list_all(
        self,
        status: Optional[str] = None,
        trigger_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PriceAlert]:
        """List alerts with optional filters."""
        ...

    def count(self, status: Optional[str] = None) -> int:
        """Count alerts matching filters."""
        ...

    def create(self, alert: PriceAlert) -> PriceAlert:
        """Create a new alert. Returns alert with ID assigned."""
        ...

    def update(self, alert_id: int, alert: PriceAlert) -> Optional[PriceAlert]:
        """Update an existing alert."""
        ...

    def delete(self, alert_id: int) -> bool:
        """Delete an alert by ID."""
        ...

    def trigger(self, alert_id: int) -> Optional[PriceAlert]:
        """Mark an alert as triggered."""
        ...


class IWishlistMatchRepository(Protocol):
    """
    Repository interface for wishlist match management.

    Matched auction lots for wishlist items.
    """

    def get_by_id(self, match_id: int) -> Optional[WishlistMatch]:
        """Get a match by ID."""
        ...

    def get_by_wishlist_item_id(
        self,
        wishlist_item_id: int,
        include_dismissed: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WishlistMatch]:
        """Get all matches for a wishlist item."""
        ...

    def get_saved(
        self,
        wishlist_item_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WishlistMatch]:
        """Get saved matches, optionally filtered by wishlist item."""
        ...

    def count_by_wishlist_item_id(
        self,
        wishlist_item_id: int,
        include_dismissed: bool = False,
    ) -> int:
        """Count matches for a wishlist item."""
        ...

    def create(self, wishlist_item_id: int, match: WishlistMatch) -> WishlistMatch:
        """Create a new match. Returns match with ID assigned."""
        ...

    def update(self, match_id: int, match: WishlistMatch) -> Optional[WishlistMatch]:
        """Update an existing match."""
        ...

    def dismiss(self, match_id: int) -> Optional[WishlistMatch]:
        """Dismiss a match."""
        ...

    def save(self, match_id: int) -> Optional[WishlistMatch]:
        """Save/bookmark a match."""
        ...

    def delete(self, match_id: int) -> bool:
        """Delete a match by ID."""
        ...


# --- Census Snapshots Repository ---

class ICensusSnapshotRepository(Protocol):
    """
    Repository interface for census snapshot management.

    Tracks NGC/PCGS population census data over time for TPG-graded coins.
    """

    def get_by_id(self, snapshot_id: int) -> Optional["CensusSnapshot"]:
        """Get a specific census snapshot by ID."""
        ...

    def get_by_coin_id(
        self,
        coin_id: int,
        service: Optional[str] = None,
    ) -> List["CensusSnapshot"]:
        """
        Get all census snapshots for a coin, optionally filtered by service.

        Returns snapshots ordered by date desc (newest first).
        """
        ...

    def get_latest(
        self,
        coin_id: int,
        service: Optional[str] = None,
    ) -> Optional["CensusSnapshot"]:
        """
        Get the most recent census snapshot for a coin.

        Optionally filter by service (ngc, pcgs).
        """
        ...

    def create(self, coin_id: int, snapshot: "CensusSnapshot") -> "CensusSnapshot":
        """Create a new census snapshot. Returns snapshot with ID assigned."""
        ...

    def update(
        self,
        snapshot_id: int,
        snapshot: "CensusSnapshot"
    ) -> Optional["CensusSnapshot"]:
        """Update an existing census snapshot."""
        ...

    def delete(self, snapshot_id: int) -> bool:
        """Delete a census snapshot by ID."""
        ...

    def list_by_service(
        self,
        service: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List["CensusSnapshot"]:
        """List all snapshots for a service with pagination."""
        ...

    def list_by_date_range(
        self,
        coin_id: int,
        start_date: date,
        end_date: date,
    ) -> List["CensusSnapshot"]:
        """Get snapshots within a date range for trend analysis."""
        ...


# --- Phase 6: Collections Repository ---

class ICollectionRepository(Protocol):
    """
    Repository interface for collection management.

    Supports custom collections (manual coin selection) and smart collections
    (dynamic membership based on criteria). Hierarchy limited to 3 levels.
    """

    def get_by_id(self, collection_id: int) -> Optional[Collection]:
        """Get a collection by ID with eager loading of relationships."""
        ...

    def get_by_slug(self, slug: str) -> Optional[Collection]:
        """Get a collection by unique slug."""
        ...

    def list_all(
        self,
        parent_id: Optional[int] = None,
        collection_type: Optional[str] = None,
        purpose: Optional[str] = None,
        include_hidden: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Collection]:
        """
        List collections with optional filters.

        If parent_id is None, returns top-level collections.
        If parent_id is set, returns children of that collection.
        """
        ...

    def list_tree(self) -> List[Collection]:
        """
        Get complete collection hierarchy as a tree structure.

        Returns all collections ordered for tree display.
        """
        ...

    def count(
        self,
        parent_id: Optional[int] = None,
        collection_type: Optional[str] = None,
        include_hidden: bool = False,
    ) -> int:
        """Count collections matching filters."""
        ...

    def create(self, collection: Collection) -> Collection:
        """Create a new collection. Returns collection with ID assigned."""
        ...

    def update(self, collection_id: int, collection: Collection) -> Optional[Collection]:
        """Update an existing collection."""
        ...

    def delete(self, collection_id: int, promote_children: bool = True) -> bool:
        """
        Delete a collection by ID.

        If promote_children is True, child collections are moved to
        the deleted collection's parent. Otherwise they become top-level.
        """
        ...

    # --- Coin membership operations ---

    def add_coin(
        self,
        collection_id: int,
        coin_id: int,
        notes: Optional[str] = None,
        position: Optional[int] = None,
    ) -> bool:
        """Add a coin to a collection."""
        ...

    def add_coins_bulk(
        self,
        collection_id: int,
        coin_ids: List[int],
    ) -> int:
        """Add multiple coins to a collection. Returns count added."""
        ...

    def remove_coin(self, collection_id: int, coin_id: int) -> bool:
        """Remove a coin from a collection."""
        ...

    def get_coins_in_collection(
        self,
        collection_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CollectionCoin]:
        """Get coins in a collection with membership details."""
        ...

    def get_collections_for_coin(self, coin_id: int) -> List[Collection]:
        """Get all collections containing a specific coin."""
        ...

    def update_coin_membership(
        self,
        collection_id: int,
        coin_id: int,
        notes: Optional[str] = None,
        is_featured: Optional[bool] = None,
        is_placeholder: Optional[bool] = None,
        position: Optional[int] = None,
        fulfills_type: Optional[str] = None,
        exclude_from_stats: Optional[bool] = None,
    ) -> bool:
        """Update a coin's membership details in a collection."""
        ...

    def reorder_coins(self, collection_id: int, coin_order: List[int]) -> bool:
        """Reorder coins within a collection."""
        ...

    def count_coins_in_collection(self, collection_id: int) -> int:
        """Count coins in a collection."""
        ...

    def get_membership(self, collection_id: int, coin_id: int) -> Optional[CollectionCoin]:
        """Get a single coin membership by collection and coin ID."""
        ...

    # --- Statistics ---

    def get_statistics(self, collection_id: int) -> CollectionStatistics:
        """Calculate collection statistics."""
        ...

    def update_cached_stats(self, collection_id: int) -> bool:
        """Refresh cached statistics for a collection."""
        ...
