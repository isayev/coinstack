"""
SNG (Sylloge Nummorum Graecorum) reference parser.

Format: SNG [collection] number, e.g. SNG Cop 123, SNG ANS 336, SNG Fitzwilliam 789.
Uses ParsedRef.collection for the collection abbreviation.
"""
import re
from typing import Optional

from .base import ParsedRef, normalize_whitespace


# SNG + collection abbreviation (letters, possibly with dots) + number + optional variant
# Common: SNG Cop, SNG ANS, SNG Paris, SNG Fitzwilliam, SNG Leu, SNG Lockett, SNG München
_PATTERN = re.compile(
    r"SNG\s+([A-Za-z][A-Za-z.]*?)\s+(\d+)([a-z])?",
    re.IGNORECASE,
)


def _normalize_collection(collection: str) -> str:
    """Normalize collection abbreviation (e.g. 'cop' -> 'Cop', 'ANS' -> 'ANS')."""
    if not collection or not collection.strip():
        return collection or ""
    s = collection.strip()
    if s.upper() == s and len(s) <= 5:
        return s.upper()  # ANS, Cop-style keep conventional case
    return s[0].upper() + s[1:].lower() if len(s) > 1 else s.upper()


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse SNG reference. Returns ParsedRef with collection and number, or None."""
    if not raw or not raw.strip():
        return None
    text = normalize_whitespace(raw)
    m = _PATTERN.match(text)
    if not m:
        return None
    collection_raw = m.group(1)
    number = m.group(2)
    variant = m.group(3)
    collection = _normalize_collection(collection_raw) if collection_raw else None
    num_str = f"{number}{variant}" if variant else number
    coll_norm = collection_raw.lower().replace(".", "").strip()
    norm = f"sng.{coll_norm}.{number}"
    if variant:
        norm += variant
    return ParsedRef(
        system="sng",
        number=num_str,
        variant=variant,
        collection=collection,
        normalized=norm.lower(),
    )
