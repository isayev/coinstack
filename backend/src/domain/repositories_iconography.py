"""Repository interfaces for compositional iconography module.

Follows Protocol pattern for dependency inversion - application layer depends on these interfaces,
infrastructure layer provides concrete implementations.
"""

from typing import Protocol, Optional, List
from src.domain.coin import (
    IconographyElement,
    IconographyAttribute,
    IconographyComposition,
    CoinIconography
)


class IIconographyElementRepository(Protocol):
    """Repository for iconographic elements (Victory, Mars, Eagle, etc.)."""

    def get_by_id(self, element_id: int) -> Optional[IconographyElement]:
        """Get element by ID."""
        ...

    def get_by_canonical_name(self, name: str) -> Optional[IconographyElement]:
        """Get element by canonical name."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> List[IconographyElement]:
        """List all elements with pagination."""
        ...

    def list_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[IconographyElement]:
        """List elements by category with pagination."""
        ...

    def search(self, query: str, category: Optional[str] = None) -> List[IconographyElement]:
        """Search elements by name or aliases."""
        ...

    def create(self, element: IconographyElement) -> IconographyElement:
        """Create new element."""
        ...

    def update(self, element_id: int, element: IconographyElement) -> Optional[IconographyElement]:
        """Update existing element."""
        ...

    def delete(self, element_id: int) -> bool:
        """Delete element."""
        ...

    def increment_usage(self, element_id: int) -> None:
        """Atomically increment usage count."""
        ...

    def decrement_usage(self, element_id: int) -> None:
        """Atomically decrement usage count."""
        ...


class IIconographyAttributeRepository(Protocol):
    """Repository for iconographic attributes (pose, direction, clothing, etc.)."""

    def get_by_id(self, attribute_id: int) -> Optional[IconographyAttribute]:
        """Get attribute by ID."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> List[IconographyAttribute]:
        """List all attributes with pagination."""
        ...

    def list_by_type(self, attribute_type: str, skip: int = 0, limit: int = 100) -> List[IconographyAttribute]:
        """List attributes by type with pagination."""
        ...

    def search(self, query: str, attribute_type: Optional[str] = None) -> List[IconographyAttribute]:
        """Search attributes by value or display name."""
        ...

    def create(self, attribute: IconographyAttribute) -> IconographyAttribute:
        """Create new attribute."""
        ...

    def update(self, attribute_id: int, attribute: IconographyAttribute) -> Optional[IconographyAttribute]:
        """Update existing attribute."""
        ...

    def delete(self, attribute_id: int) -> bool:
        """Delete attribute."""
        ...


class IIconographyCompositionRepository(Protocol):
    """Repository for iconographic compositions (full scene descriptions)."""

    def get_by_id(self, composition_id: int) -> Optional[IconographyComposition]:
        """Get composition by ID with eager loading of elements and attributes."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> List[IconographyComposition]:
        """List all compositions with pagination."""
        ...

    def list_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[IconographyComposition]:
        """List compositions by category with pagination."""
        ...

    def search(self, query: str, category: Optional[str] = None) -> List[IconographyComposition]:
        """Search compositions by name or canonical description."""
        ...

    def create(self, composition: IconographyComposition) -> IconographyComposition:
        """Create new composition with elements and attributes."""
        ...

    def update(self, composition_id: int, composition: IconographyComposition) -> Optional[IconographyComposition]:
        """Update existing composition."""
        ...

    def delete(self, composition_id: int) -> bool:
        """Delete composition."""
        ...

    def increment_usage(self, composition_id: int) -> None:
        """Atomically increment usage count."""
        ...

    def decrement_usage(self, composition_id: int) -> None:
        """Atomically decrement usage count."""
        ...

    def get_coins_using_composition(self, composition_id: int) -> List[int]:
        """Get list of coin IDs using this composition."""
        ...


class ICoinIconographyRepository(Protocol):
    """Repository for linking coins to iconographic compositions."""

    def get_by_id(self, link_id: int) -> Optional[CoinIconography]:
        """Get link by ID."""
        ...

    def get_by_coin_id(self, coin_id: int) -> List[CoinIconography]:
        """Get all iconography links for a coin."""
        ...

    def get_by_composition_id(self, composition_id: int) -> List[CoinIconography]:
        """Get all coins using a composition."""
        ...

    def create(self, link: CoinIconography) -> CoinIconography:
        """Create new coin-composition link."""
        ...

    def update(self, link_id: int, link: CoinIconography) -> Optional[CoinIconography]:
        """Update existing link (side, position, notes)."""
        ...

    def delete(self, link_id: int) -> bool:
        """Delete link."""
        ...

    def find_duplicate(self, coin_id: int, composition_id: int, coin_side: str) -> Optional[CoinIconography]:
        """Find duplicate link (coin_id, composition_id, coin_side must be unique)."""
        ...
