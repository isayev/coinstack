"""
Grade storage normalizer.

Normalizes grade strings for consistent storage: strip, collapse spaces, uppercase.
Used at every write path (create/update coin, import, apply enrichment).
No synonym mapping; for search canonical form see domain.services.search_service.
"""


def normalize_grade_for_storage(grade: str | None) -> str | None:
    """Normalize grade for consistent storage. Returns None for empty/whitespace-only."""
    if not grade or not grade.strip():
        return None
    return " ".join(grade.strip().split()).upper()
