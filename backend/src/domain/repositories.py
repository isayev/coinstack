from typing import Protocol, Optional, List, Dict, Any, Union
from datetime import date
from src.domain.coin import Coin, ProvenanceEntry, ProvenanceEventType
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
