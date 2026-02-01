"""Repository interfaces for die study module.

Follows Protocol pattern for dependency inversion - application layer depends on these interfaces,
infrastructure layer provides concrete implementations.
"""

from typing import Protocol, Optional
from src.domain.coin import Die, DieLink, DiePairing, DieVariety


class IDieRepository(Protocol):
    """Repository for die catalog."""

    def get_by_id(self, die_id: int) -> Optional[Die]:
        """Get die by ID."""
        ...

    def get_by_identifier(self, identifier: str) -> Optional[Die]:
        """Get die by canonical identifier."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Die]:
        """List all dies with pagination."""
        ...

    def search(self, query: str, die_side: str | None = None) -> list[Die]:
        """Search dies by identifier or notes."""
        ...

    def create(self, die: Die) -> Die:
        """Create new die entry."""
        ...

    def update(self, die_id: int, die: Die) -> Optional[Die]:
        """Update existing die entry."""
        ...

    def delete(self, die_id: int) -> bool:
        """Delete die entry."""
        ...


class IDieLinkRepository(Protocol):
    """Repository for die links between coins."""

    def get_by_id(self, link_id: int) -> Optional[DieLink]:
        """Get die link by ID."""
        ...

    def get_by_coin_id(self, coin_id: int) -> list[DieLink]:
        """Get all die links for a coin."""
        ...

    def get_by_die_id(self, die_id: int) -> list[DieLink]:
        """Get all die links for a specific die."""
        ...

    def get_linked_coins(self, coin_id: int, die_id: int) -> list[int]:
        """Get all coin IDs directly linked to this coin via shared die."""
        ...

    def get_die_network(self, coin_id: int, die_id: int, max_depth: int = 3) -> list[int]:
        """Get all coins transitively linked via shared die (BFS up to max_depth)."""
        ...

    def create(self, link: DieLink) -> DieLink:
        """Create new die link (enforces coin_a_id < coin_b_id ordering)."""
        ...

    def update(self, link_id: int, link: DieLink) -> Optional[DieLink]:
        """Update existing die link."""
        ...

    def delete(self, link_id: int) -> bool:
        """Delete die link."""
        ...

    def find_duplicate(self, die_id: int, coin_a_id: int, coin_b_id: int) -> Optional[DieLink]:
        """Check if die link already exists between two coins."""
        ...


class IDiePairingRepository(Protocol):
    """Repository for die pairings (obverse-reverse combinations)."""

    def get_by_id(self, pairing_id: int) -> Optional[DiePairing]:
        """Get die pairing by ID."""
        ...

    def get_by_dies(self, obverse_die_id: int, reverse_die_id: int) -> Optional[DiePairing]:
        """Get die pairing by obverse and reverse die IDs."""
        ...

    def list_by_obverse(self, obverse_die_id: int) -> list[DiePairing]:
        """List all pairings for an obverse die."""
        ...

    def list_by_reverse(self, reverse_die_id: int) -> list[DiePairing]:
        """List all pairings for a reverse die."""
        ...

    def create(self, pairing: DiePairing) -> DiePairing:
        """Create new die pairing."""
        ...

    def update(self, pairing_id: int, pairing: DiePairing) -> Optional[DiePairing]:
        """Update existing die pairing."""
        ...

    def delete(self, pairing_id: int) -> bool:
        """Delete die pairing."""
        ...


class IDieVarietyRepository(Protocol):
    """Repository for die variety classifications."""

    def get_by_id(self, variety_id: int) -> Optional[DieVariety]:
        """Get die variety by ID."""
        ...

    def get_by_coin_id(self, coin_id: int) -> list[DieVariety]:
        """Get all die varieties for a coin."""
        ...

    def get_by_die_id(self, die_id: int) -> list[DieVariety]:
        """Get all varieties using a specific die."""
        ...

    def list_by_variety_code(self, code: str) -> list[DieVariety]:
        """List all varieties with matching code."""
        ...

    def create(self, variety: DieVariety) -> DieVariety:
        """Create new die variety."""
        ...

    def update(self, variety_id: int, variety: DieVariety) -> Optional[DieVariety]:
        """Update existing die variety."""
        ...

    def delete(self, variety_id: int) -> bool:
        """Delete die variety."""
        ...
