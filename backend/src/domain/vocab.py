"""
Controlled Vocabulary Domain Layer (V3)

This module defines the domain entities for the unified controlled vocabulary system.
Replaces the previous separate Issuer/Mint entities with a unified VocabTerm approach.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Protocol, Dict, Any


class VocabType(str, Enum):
    """Types of vocabulary terms supported by the system."""
    
    # Core vocabulary (synced from Nomisma SPARQL)
    ISSUER = "issuer"               # Augustus, Trajan, etc.
    MINT = "mint"                   # Roma, Lugdunum, Antioch
    DENOMINATION = "denomination"   # Denarius, Aureus, Sestertius
    
    # Extended vocabulary
    DYNASTY = "dynasty"             # Julio-Claudian, Flavian, Severan
                                    # Metadata: {"period_start": -27, "period_end": 68, "rulers": [...]}
    
    # Canonical series definitions (links to Series entity)
    CANONICAL_SERIES = "canonical_series"  # "Twelve Caesars", "Military Emperors"
                                           # Metadata: {"expected_count": 12, "rulers": [...]}


class IssuerType(str, Enum):
    """Sub-types for ISSUER vocabulary terms (stored in metadata)."""
    # Imperial ranks
    AUGUSTUS = "augustus"      # Senior emperor (post-27 BC)
    CAESAR = "caesar"          # Junior emperor / designated heir
    EMPEROR = "emperor"        # Generic imperial (for searches)
    EMPRESS = "empress"        # Imperial consort with coinage
    REGENT = "regent"          # Acting on behalf of minor (Agrippina, Pulcheria)
    # Contested rulers
    USURPER = "usurper"        # Contested claimants
    # Pre-Imperial / Provincial
    MAGISTRATE = "magistrate"  # Generic Republican official
    MONEYER = "moneyer"        # Tresviri monetales (Republican mint officials)
    CONSUL = "consul"          # Annual magistrate
    PROCONSUL = "proconsul"    # Provincial governor with minting authority
    # Client rulers
    KING = "king"              # Client kings (Herod, etc.)
    TETRARCH = "tetrarch"      # Jewish tetrarchs (Herod's sons)
    ETHNARCH = "ethnarch"      # Lower rank than king (Archelaus)
    # Other
    OTHER = "other"


@dataclass
class VocabTerm:
    """
    Unified vocabulary term entity.
    
    Replaces the previous separate Issuer and Mint entities with a single
    flexible entity that can represent any vocabulary type.
    
    Attributes:
        id: Database ID (None for unsaved terms)
        vocab_type: The type of vocabulary term
        canonical_name: The standardized name
        nomisma_uri: Link to Nomisma.org LOD URI (if available)
        metadata: Type-specific metadata as a dictionary
    
    Metadata examples by type:
        - issuer: {"issuer_type": "emperor", "reign_start": -27, "reign_end": 14}
        - mint: {"modern_name": "Lyon", "ric_abbrev": "LVG", "lat": 45.76, "lon": 4.83}
        - denomination: {"metal": "silver", "typical_weight_g": 3.9}
        - dynasty: {"period_start": -27, "period_end": 68, "rulers": ["Augustus", ...]}
        - canonical_series: {"expected_count": 12, "rulers": [...], "category": "imperial"}
    """
    id: Optional[int]
    vocab_type: VocabType
    canonical_name: str
    nomisma_uri: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the term after initialization."""
        if not self.canonical_name or not self.canonical_name.strip():
            raise ValueError("canonical_name cannot be empty")
    
    @property
    def reign_start(self) -> Optional[int]:
        """Get reign/period start year from metadata (for issuers/dynasties)."""
        return self.metadata.get("reign_start") or self.metadata.get("period_start")
    
    @property
    def reign_end(self) -> Optional[int]:
        """Get reign/period end year from metadata (for issuers/dynasties)."""
        return self.metadata.get("reign_end") or self.metadata.get("period_end")
    
    @property
    def issuer_type(self) -> Optional[str]:
        """Get issuer type from metadata."""
        return self.metadata.get("issuer_type")
    
    @property
    def rulers(self) -> List[str]:
        """Get list of rulers from metadata (for dynasties/series)."""
        return self.metadata.get("rulers", [])
    
    @property
    def expected_count(self) -> Optional[int]:
        """Get expected count from metadata (for canonical series)."""
        return self.metadata.get("expected_count")
    
    def is_active_in_year(self, year: int) -> bool:
        """Check if this term was active in a given year."""
        start = self.reign_start if self.reign_start is not None else float('-inf')
        end = self.reign_end if self.reign_end is not None else float('inf')
        return start <= year <= end
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "vocab_type": self.vocab_type.value,
            "canonical_name": self.canonical_name,
            "nomisma_uri": self.nomisma_uri,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VocabTerm":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            vocab_type=VocabType(data["vocab_type"]),
            canonical_name=data["canonical_name"],
            nomisma_uri=data.get("nomisma_uri"),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class NormalizationResult:
    """
    Result of a vocabulary normalization operation.
    
    Represents the outcome of attempting to match raw user input
    to a canonical vocabulary term.
    
    Attributes:
        success: Whether a match was found
        term: The matched VocabTerm (None if no match)
        method: How the match was found ("exact", "fts", "nomisma", "llm")
        confidence: Confidence score 0.0 - 1.0
        raw_input: The original input that was normalized
        needs_review: Whether this match should be reviewed by user
        alternatives: Other potential matches (for review UI)
    """
    success: bool
    term: Optional[VocabTerm] = None
    method: str = ""           # "exact", "fts", "nomisma", "llm"
    confidence: float = 0.0    # 0.0 - 1.0
    raw_input: str = ""
    needs_review: bool = False
    alternatives: List[VocabTerm] = field(default_factory=list)


class IVocabRepository(Protocol):
    """
    Repository interface for vocabulary operations.
    
    This protocol defines the contract for vocabulary persistence and
    normalization operations. Implementations handle the actual database
    interactions and external API calls.
    """
    
    def search(self, vocab_type: VocabType, query: str, limit: int = 10) -> List[VocabTerm]:
        """
        Search for vocabulary terms using FTS5 full-text search.
        
        Args:
            vocab_type: The type of vocabulary to search
            query: Search query (supports prefix matching)
            limit: Maximum number of results
            
        Returns:
            List of matching VocabTerm instances
        """
        ...
    
    def normalize(
        self, 
        raw: str, 
        vocab_type: VocabType, 
        context: Optional[Dict[str, Any]] = None
    ) -> NormalizationResult:
        """
        Normalize raw text to a canonical vocabulary term.
        
        Uses a chain of matching strategies:
        1. Exact match on canonical_name
        2. FTS5 fuzzy match with confidence scoring
        3. Nomisma reconciliation API (external)
        4. Returns needs_review=True if no confident match
        
        Args:
            raw: Raw input text to normalize
            vocab_type: Expected vocabulary type
            context: Additional context (coin_id, category, etc.)
            
        Returns:
            NormalizationResult with match details
        """
        ...
    
    def sync_nomisma(self, vocab_type: VocabType) -> Dict[str, int]:
        """
        Sync vocabulary from Nomisma SPARQL endpoint.
        
        Args:
            vocab_type: Type of vocabulary to sync (ISSUER, MINT, DENOMINATION)
            
        Returns:
            Stats dict with {"added": N, "unchanged": M}
        """
        ...
    
    def get_by_id(self, term_id: int) -> Optional[VocabTerm]:
        """Get a vocabulary term by ID."""
        ...
    
    def get_by_canonical(
        self, 
        vocab_type: VocabType, 
        name: str
    ) -> Optional[VocabTerm]:
        """Get a vocabulary term by type and canonical name."""
        ...
    
    def save(self, term: VocabTerm) -> VocabTerm:
        """Save or update a vocabulary term."""
        ...
    
    def get_all(
        self, 
        vocab_type: VocabType, 
        limit: int = 1000
    ) -> List[VocabTerm]:
        """Get all vocabulary terms of a given type."""
        ...


# Legacy compatibility aliases (deprecated)
# These are kept for backward compatibility during migration

@dataclass
class Issuer:
    """
    Legacy Issuer entity (deprecated).
    
    Use VocabTerm with vocab_type=ISSUER instead.
    """
    id: int
    canonical_name: str
    nomisma_id: str
    issuer_type: IssuerType
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None

    def __post_init__(self):
        if self.reign_start is not None and self.reign_end is not None:
            if self.reign_start > self.reign_end:
                raise ValueError("Reign start cannot be after reign end")

    def is_active_in_year(self, year: int) -> bool:
        start = self.reign_start if self.reign_start is not None else float('-inf')
        end = self.reign_end if self.reign_end is not None else float('inf')
        return start <= year <= end
    
    def to_vocab_term(self) -> VocabTerm:
        """Convert to unified VocabTerm."""
        return VocabTerm(
            id=self.id,
            vocab_type=VocabType.ISSUER,
            canonical_name=self.canonical_name,
            nomisma_uri=f"http://nomisma.org/id/{self.nomisma_id}" if self.nomisma_id else None,
            metadata={
                "issuer_type": self.issuer_type.value,
                "reign_start": self.reign_start,
                "reign_end": self.reign_end,
            }
        )


@dataclass
class Mint:
    """
    Legacy Mint entity (deprecated).
    
    Use VocabTerm with vocab_type=MINT instead.
    """
    id: int
    canonical_name: str
    nomisma_id: str
    active_from: Optional[int] = None
    active_to: Optional[int] = None

    def __post_init__(self):
        if self.active_from is not None and self.active_to is not None:
            if self.active_from > self.active_to:
                raise ValueError("Active start cannot be after active end")

    def is_active_in_year(self, year: int) -> bool:
        start = self.active_from if self.active_from is not None else float('-inf')
        end = self.active_to if self.active_to is not None else float('inf')
        return start <= year <= end
    
    def to_vocab_term(self) -> VocabTerm:
        """Convert to unified VocabTerm."""
        return VocabTerm(
            id=self.id,
            vocab_type=VocabType.MINT,
            canonical_name=self.canonical_name,
            nomisma_uri=f"http://nomisma.org/id/{self.nomisma_id}" if self.nomisma_id else None,
            metadata={
                "active_from": self.active_from,
                "active_to": self.active_to,
            }
        )
