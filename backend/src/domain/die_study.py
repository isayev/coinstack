"""
Die Study Domain Entities.

This module defines domain entities for tracking die relationships between coins.
Die studies are a cornerstone of numismatic scholarship, helping to:

1. Establish mint sequences and chronology
2. Authenticate coins (die matches are strong evidence)
3. Identify rare die combinations
4. Map die deterioration over time

Key Concepts:
- Obverse die (anvil die): Usually lasted longer, portrait side
- Reverse die (hammer die): Wore faster, design side
- Die link: Two coins sharing the same die (obverse OR reverse)
- Die chain: Sequence of coins connected through die links
- Die group: Set of coins all sharing one particular die
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DieSide(str, Enum):
    """Which side of the coin the die match is on."""
    OBVERSE = "obverse"
    REVERSE = "reverse"


class DieMatchConfidence(str, Enum):
    """Confidence level for die match identification."""
    CERTAIN = "certain"      # No doubt - clear die match
    PROBABLE = "probable"    # High confidence - minor wear differences only
    POSSIBLE = "possible"    # Low confidence - needs more study
    UNCERTAIN = "uncertain"  # Very uncertain - included for tracking


class DieMatchSource(str, Enum):
    """How the die match was identified."""
    MANUAL = "manual"        # User identified match
    LLM = "llm"              # LLM vision suggested match
    REFERENCE = "reference"  # Found in published reference
    IMPORT = "import"        # Imported from external source


@dataclass
class DieLink:
    """
    A die link between two coins.
    
    Represents that two coins were struck from the same die on one side.
    The relationship is bidirectional: if coin_a links to coin_b, then
    coin_b implicitly links to coin_a.
    
    Attributes:
        id: Database ID (None for new links)
        coin_a_id: First coin in the link
        coin_b_id: Second coin in the link
        die_side: Which side shares the die (obverse/reverse)
        confidence: How certain the match is
        source: How the match was identified
        reference: Published reference if applicable
        notes: Additional notes about the match
        identified_at: When the link was created
    """
    id: Optional[int] = None
    coin_a_id: int = 0
    coin_b_id: int = 0
    die_side: DieSide = DieSide.OBVERSE
    confidence: DieMatchConfidence = DieMatchConfidence.POSSIBLE
    source: DieMatchSource = DieMatchSource.MANUAL
    reference: Optional[str] = None  # e.g., "RIC II, plate X.1"
    notes: Optional[str] = None
    identified_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.coin_a_id == self.coin_b_id:
            raise ValueError("Cannot create die link between a coin and itself")
        if self.coin_a_id <= 0 or self.coin_b_id <= 0:
            raise ValueError("Both coin IDs must be positive integers")
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence match."""
        return self.confidence in (DieMatchConfidence.CERTAIN, DieMatchConfidence.PROBABLE)
    
    def involves_coin(self, coin_id: int) -> bool:
        """Check if this link involves a specific coin."""
        return self.coin_a_id == coin_id or self.coin_b_id == coin_id
    
    def get_other_coin(self, coin_id: int) -> int:
        """Get the other coin in the link given one coin ID."""
        if coin_id == self.coin_a_id:
            return self.coin_b_id
        elif coin_id == self.coin_b_id:
            return self.coin_a_id
        raise ValueError(f"Coin {coin_id} not in this die link")


@dataclass
class DieStudyGroup:
    """
    A group of coins that share a single die.
    
    Die groups are collections of coins all linked by the same die.
    Useful for:
    - Tracking all known specimens from a die
    - Estimating die output (number of coins struck)
    - Studying die deterioration sequence
    
    Attributes:
        id: Database ID (None for new groups)
        name: Display name for the group (e.g., "Trajan Obverse Die A")
        die_side: Whether this tracks an obverse or reverse die
        issuer_id: Issuer/ruler associated with this die
        mint_id: Mint that produced this die
        notes: Description and analysis of the die
        members: List of coin IDs in this group (when loaded)
        member_positions: Estimated strike order for each member
    """
    id: Optional[int] = None
    name: str = ""
    die_side: DieSide = DieSide.OBVERSE
    issuer_id: Optional[int] = None  # FK to issuer vocab
    mint_id: Optional[int] = None    # FK to mint vocab
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    # Loaded separately - not persisted directly in group
    members: List[int] = field(default_factory=list)  # Coin IDs
    member_positions: dict = field(default_factory=dict)  # {coin_id: position}
    
    def add_member(self, coin_id: int, position: Optional[int] = None) -> None:
        """Add a coin to the group."""
        if coin_id not in self.members:
            self.members.append(coin_id)
        if position is not None:
            self.member_positions[coin_id] = position
    
    def remove_member(self, coin_id: int) -> bool:
        """Remove a coin from the group. Returns True if removed."""
        if coin_id in self.members:
            self.members.remove(coin_id)
            self.member_positions.pop(coin_id, None)
            return True
        return False
    
    @property
    def member_count(self) -> int:
        """Number of coins in this die group."""
        return len(self.members)


@dataclass
class DieChain:
    """
    A chain of coins connected through die links.
    
    Die chains show the sequence of die usage and can reveal
    mint production patterns. Built by traversing DieLinks.
    
    This is a read-only view object, not persisted directly.
    """
    coins: List[int] = field(default_factory=list)
    links: List[DieLink] = field(default_factory=list)
    die_side: DieSide = DieSide.OBVERSE
    
    @property
    def length(self) -> int:
        """Number of coins in the chain."""
        return len(self.coins)
    
    def contains(self, coin_id: int) -> bool:
        """Check if a coin is in this chain."""
        return coin_id in self.coins


@dataclass
class DieComparisonResult:
    """
    Result of LLM vision comparison of two coin images.
    
    Used by the die study comparison capability.
    """
    coin_a_id: int
    coin_b_id: int
    die_side: DieSide
    is_match: bool
    confidence: float  # 0.0 to 1.0
    reasoning: List[str] = field(default_factory=list)
    diagnostic_points: List[str] = field(default_factory=list)  # Specific matching features
