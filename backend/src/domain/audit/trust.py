"""
Granular trust configuration for auction data sources.

Trust is defined at the field × source × condition level, allowing
nuanced handling of data from different auction houses based on
their reputation for specific types of information.
"""

from enum import Enum
from dataclasses import dataclass


class TrustLevel(str, Enum):
    """Trust level for a field from a specific source."""
    
    AUTHORITATIVE = "authoritative"  # 95%+ confidence, can auto-accept
    HIGH = "high"                    # 80%+ confidence, suggest with mild review
    MEDIUM = "medium"                # 60%+ confidence, suggest but require review
    LOW = "low"                      # 40%+ confidence, flag only, don't suggest updates
    UNTRUSTED = "untrusted"          # <40% confidence, ignore for enrichment purposes
    
    @property
    def confidence_threshold(self) -> float:
        """Get confidence threshold for this trust level."""
        return {
            TrustLevel.AUTHORITATIVE: 0.95,
            TrustLevel.HIGH: 0.80,
            TrustLevel.MEDIUM: 0.60,
            TrustLevel.LOW: 0.40,
            TrustLevel.UNTRUSTED: 0.0,
        }[self]
    
    @property
    def can_suggest(self) -> bool:
        """Whether this trust level allows suggesting enrichments."""
        return self in (TrustLevel.AUTHORITATIVE, TrustLevel.HIGH, TrustLevel.MEDIUM)
    
    @property
    def requires_review(self) -> bool:
        """Whether values at this trust level require manual review."""
        return self not in (TrustLevel.AUTHORITATIVE,)


@dataclass
class FieldTrust:
    """
    Trust configuration for a specific field from a specific source.
    """
    trust_level: TrustLevel
    auto_accept: bool = False
    tolerance: float | None = None
    requires_slabbed: bool = False
    notes: str = ""
    
    @property
    def confidence(self) -> float:
        """Get confidence score for this trust configuration."""
        return self.trust_level.confidence_threshold


# =============================================================================
# Trust Matrix: field × source
# =============================================================================

TRUST_MATRIX: dict[str, dict[str, FieldTrust]] = {
    # Physical measurements
    "weight_g": {
        "heritage": FieldTrust(TrustLevel.HIGH, tolerance=0.02),
        "cng": FieldTrust(TrustLevel.HIGH, tolerance=0.02),
        "biddr": FieldTrust(TrustLevel.HIGH, tolerance=0.05),
        "roma": FieldTrust(TrustLevel.HIGH, tolerance=0.02),
        "agora": FieldTrust(TrustLevel.HIGH, tolerance=0.03),
        "ebay": FieldTrust(TrustLevel.LOW, tolerance=0.1),
    },
    "diameter_mm": {
        "heritage": FieldTrust(TrustLevel.HIGH, tolerance=0.5),
        "cng": FieldTrust(TrustLevel.HIGH, tolerance=0.5),
        "biddr": FieldTrust(TrustLevel.MEDIUM, tolerance=1.0),
        "roma": FieldTrust(TrustLevel.HIGH, tolerance=0.5),
        "agora": FieldTrust(TrustLevel.HIGH, tolerance=0.5),
        "ebay": FieldTrust(TrustLevel.LOW, tolerance=2.0),
    },
    "die_axis": {
        "heritage": FieldTrust(TrustLevel.HIGH),
        "cng": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "roma": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW),
    },
    "grade": {
        "heritage": FieldTrust(TrustLevel.HIGH),
        "cng": FieldTrust(TrustLevel.HIGH),
        "ngc": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True, requires_slabbed=True),
        "pcgs": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True, requires_slabbed=True),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "roma": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.UNTRUSTED),
    },
    "hammer_price": {
        "heritage": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "cng": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "biddr": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "roma": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "agora": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "ebay": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
    },
}

# Defaults
DEFAULT_TRUST_BY_SOURCE: dict[str, FieldTrust] = {
    "heritage": FieldTrust(TrustLevel.MEDIUM),
    "cng": FieldTrust(TrustLevel.MEDIUM),
    "roma": FieldTrust(TrustLevel.MEDIUM),
    "biddr": FieldTrust(TrustLevel.MEDIUM),
    "agora": FieldTrust(TrustLevel.MEDIUM),
    "ebay": FieldTrust(TrustLevel.LOW),
    "ngc": FieldTrust(TrustLevel.HIGH),
    "pcgs": FieldTrust(TrustLevel.HIGH),
}

FALLBACK_TRUST = FieldTrust(TrustLevel.LOW)

def normalize_source(source: str) -> str:
    """Normalize source name for lookup."""
    if not source: return "unknown"
    s = source.lower().strip()
    if "/" in s: s = s.split("/")[0]
    if "heritage" in s: return "heritage"
    if "cng" in s or "classical" in s: return "cng"
    if "biddr" in s: return "biddr"
    if "roma" in s: return "roma"
    if "agora" in s: return "agora"
    if "ebay" in s: return "ebay"
    if "ngc" in s: return "ngc"
    if "pcgs" in s: return "pcgs"
    return s

def get_field_trust(field: str, source: str) -> FieldTrust:
    """Get trust configuration for a field from a source."""
    s = normalize_source(source)
    if field in TRUST_MATRIX:
        return TRUST_MATRIX[field].get(s, DEFAULT_TRUST_BY_SOURCE.get(s, FALLBACK_TRUST))
    return DEFAULT_TRUST_BY_SOURCE.get(s, FALLBACK_TRUST)
