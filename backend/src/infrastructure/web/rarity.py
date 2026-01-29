"""
Normalize rarity for API and storage.

Frontend and design system expect lowercase canonical values: c, s, r1, r2, r3, u.
LLM and legacy data may return RIC-style uppercase (C, S, R1–R5, RR, RRR, UNIQUE).
"""

from typing import Optional

# RIC-style uppercase -> frontend canonical lowercase (c, s, r1, r2, r3, u)
_RARITY_MAP = {
    "C": "c",
    "S": "s",
    "R1": "r1",
    "R2": "r2",
    "R3": "r3",
    "R4": "r3",   # map to r3 (extremely rare)
    "R5": "u",    # unique
    "RR": "r2",   # very rare
    "RRR": "r3",  # extremely rare
    "UNIQUE": "u",
}

# Description-like text (lowercase) -> canonical; used when only description is set
_DESC_MAP = {
    "common": "c",
    "scarce": "s",
    "rare": "r1",
    "very rare": "r2",
    "extremely rare": "r3",
    "unique": "u",
}


def normalize_rarity_for_api(value: Optional[str]) -> Optional[str]:
    """
    Normalize rarity to frontend canonical lowercase (c, s, r1, r2, r3, u).

    Used when building API responses and when applying LLM-suggested rarity
    so that stored/returned values always match the frontend Zod enum.
    """
    if not value or not value.strip():
        return value
    s = value.strip()
    key = s.upper()
    if key in _RARITY_MAP:
        return _RARITY_MAP[key]
    # Try description-style (e.g. "Very Rare" from LLM); check longer phrases first
    low = s.lower()
    for desc in sorted(_DESC_MAP.keys(), key=len, reverse=True):
        if desc in low or low == desc:
            return _DESC_MAP[desc]
    return s.lower()
