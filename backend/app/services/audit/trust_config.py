"""
Granular trust configuration for auction data sources.

Trust is defined at the field × source × condition level, allowing
nuanced handling of data from different auction houses based on
their reputation for specific types of information.
"""

from enum import Enum
from dataclasses import dataclass, field


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
    
    Attributes:
        trust_level: Base trust level for this field/source combination
        auto_accept: If True, can be applied without manual review
        tolerance: For numeric fields, acceptable difference (e.g., 0.02 for weight in grams)
        requires_slabbed: If True, only trust this data for slabbed coins
        notes: Human-readable notes about this trust configuration
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
        "heritage": FieldTrust(
            TrustLevel.HIGH, 
            tolerance=0.02,  # 0.02g tolerance
            notes="Heritage scales are professional grade"
        ),
        "cng": FieldTrust(
            TrustLevel.HIGH, 
            tolerance=0.02,
            notes="CNG has excellent measurement standards"
        ),
        "biddr": FieldTrust(
            TrustLevel.HIGH, 
            tolerance=0.05,  # Slightly more tolerance
            notes="Biddr houses generally reliable"
        ),
        "roma": FieldTrust(
            TrustLevel.HIGH, 
            tolerance=0.02,
            notes="Roma Numismatics professional standards"
        ),
        "agora": FieldTrust(
            TrustLevel.HIGH, 
            tolerance=0.03,
            notes="Agora measurements generally accurate"
        ),
        "ebay": FieldTrust(
            TrustLevel.LOW, 
            tolerance=0.1,  # Wide tolerance - seller scales unreliable
            notes="eBay seller scales often inaccurate"
        ),
    },
    
    "diameter_mm": {
        "heritage": FieldTrust(TrustLevel.HIGH, tolerance=0.5),
        "cng": FieldTrust(TrustLevel.HIGH, tolerance=0.5),
        "biddr": FieldTrust(TrustLevel.MEDIUM, tolerance=1.0, notes="Sometimes estimated"),
        "roma": FieldTrust(TrustLevel.HIGH, tolerance=0.5),
        "agora": FieldTrust(TrustLevel.HIGH, tolerance=0.5),
        "ebay": FieldTrust(TrustLevel.LOW, tolerance=2.0, notes="Often inaccurate"),
    },
    
    "die_axis": {
        "heritage": FieldTrust(TrustLevel.HIGH),
        "cng": FieldTrust(
            TrustLevel.AUTHORITATIVE, 
            auto_accept=True,
            notes="CNG is meticulous about die axis"
        ),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "roma": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW, notes="Often missing or incorrect"),
    },
    
    # Grading
    "grade": {
        "heritage": FieldTrust(TrustLevel.HIGH, notes="Heritage graders are experienced"),
        "cng": FieldTrust(TrustLevel.HIGH, notes="CNG grading is conservative and reliable"),
        "ngc": FieldTrust(
            TrustLevel.AUTHORITATIVE, 
            auto_accept=True, 
            requires_slabbed=True,
            notes="Third-party grading service"
        ),
        "pcgs": FieldTrust(
            TrustLevel.AUTHORITATIVE, 
            auto_accept=True, 
            requires_slabbed=True,
            notes="Third-party grading service"
        ),
        "biddr": FieldTrust(TrustLevel.MEDIUM, notes="Varies by sub-house"),
        "roma": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.UNTRUSTED, notes="Sellers wildly overgrade"),
    },
    
    "certification_number": {
        "heritage": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "cng": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "ngc": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "pcgs": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "biddr": FieldTrust(TrustLevel.HIGH),
        "ebay": FieldTrust(TrustLevel.MEDIUM, notes="Verify against grading service"),
    },
    
    # References
    "reference": {
        "cng": FieldTrust(
            TrustLevel.AUTHORITATIVE, 
            auto_accept=True,
            notes="CNG references are gold standard"
        ),
        "heritage": FieldTrust(TrustLevel.HIGH),
        "roma": FieldTrust(TrustLevel.HIGH),
        "biddr": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.HIGH),
        "ebay": FieldTrust(TrustLevel.UNTRUSTED, notes="Often wrong or fabricated"),
    },
    
    # Legends and descriptions
    "obverse_legend": {
        "heritage": FieldTrust(TrustLevel.MEDIUM, notes="Often abbreviated in listings"),
        "cng": FieldTrust(TrustLevel.HIGH, notes="Usually complete and accurate"),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "roma": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW, notes="Often incomplete or wrong"),
    },
    
    "reverse_legend": {
        "heritage": FieldTrust(TrustLevel.MEDIUM, notes="Often abbreviated"),
        "cng": FieldTrust(TrustLevel.HIGH),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "roma": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW),
    },
    
    "obverse_description": {
        "heritage": FieldTrust(TrustLevel.MEDIUM),
        "cng": FieldTrust(TrustLevel.HIGH, notes="CNG descriptions are scholarly"),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "roma": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW),
    },
    
    "reverse_description": {
        "heritage": FieldTrust(TrustLevel.MEDIUM),
        "cng": FieldTrust(TrustLevel.HIGH),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "roma": FieldTrust(TrustLevel.HIGH),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW),
    },
    
    # Mint and dating
    "mint": {
        "cng": FieldTrust(TrustLevel.HIGH, notes="Expert attributions"),
        "heritage": FieldTrust(TrustLevel.HIGH),
        "roma": FieldTrust(TrustLevel.HIGH),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW, notes="Often guessed incorrectly"),
    },
    
    "mint_year_start": {
        "cng": FieldTrust(TrustLevel.HIGH),
        "heritage": FieldTrust(TrustLevel.HIGH),
        "roma": FieldTrust(TrustLevel.HIGH),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW),
    },
    
    "mint_year_end": {
        "cng": FieldTrust(TrustLevel.HIGH),
        "heritage": FieldTrust(TrustLevel.HIGH),
        "roma": FieldTrust(TrustLevel.HIGH),
        "biddr": FieldTrust(TrustLevel.MEDIUM),
        "agora": FieldTrust(TrustLevel.MEDIUM),
        "ebay": FieldTrust(TrustLevel.LOW),
    },
    
    # Images - always valuable regardless of source
    "images": {
        "heritage": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True, notes="Professional photography"),
        "cng": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True, notes="Excellent coin photography"),
        "biddr": FieldTrust(TrustLevel.HIGH, auto_accept=True),
        "roma": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "agora": FieldTrust(TrustLevel.HIGH, auto_accept=True),
        "ebay": FieldTrust(TrustLevel.HIGH, auto_accept=True, notes="Images are images - useful regardless"),
    },
    
    # Pricing - factual data, always trustworthy
    "hammer_price": {
        "heritage": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "cng": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "biddr": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "roma": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "agora": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "ebay": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True, notes="Price is factual"),
    },
    
    "estimate_low": {
        "heritage": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "cng": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "biddr": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "roma": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "agora": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "ebay": FieldTrust(TrustLevel.LOW, notes="eBay doesn't have formal estimates"),
    },
    
    "estimate_high": {
        "heritage": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "cng": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "biddr": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "roma": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "agora": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "ebay": FieldTrust(TrustLevel.LOW, notes="eBay doesn't have formal estimates"),
    },
    
    "auction_date": {
        "heritage": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "cng": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "biddr": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "roma": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "agora": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True),
        "ebay": FieldTrust(TrustLevel.AUTHORITATIVE, auto_accept=True, notes="Date is factual"),
    },
}


# Default trust levels by source when field not in matrix
DEFAULT_TRUST_BY_SOURCE: dict[str, FieldTrust] = {
    "heritage": FieldTrust(TrustLevel.MEDIUM, notes="Default for Heritage"),
    "cng": FieldTrust(TrustLevel.MEDIUM, notes="Default for CNG"),
    "roma": FieldTrust(TrustLevel.MEDIUM, notes="Default for Roma"),
    "biddr": FieldTrust(TrustLevel.MEDIUM, notes="Default for Biddr"),
    "agora": FieldTrust(TrustLevel.MEDIUM, notes="Default for Agora"),
    "ebay": FieldTrust(TrustLevel.LOW, notes="Default for eBay - untrusted"),
    "ngc": FieldTrust(TrustLevel.HIGH, notes="Default for NGC"),
    "pcgs": FieldTrust(TrustLevel.HIGH, notes="Default for PCGS"),
}

# Ultimate fallback
FALLBACK_TRUST = FieldTrust(TrustLevel.LOW, notes="Unknown source - low trust")


def normalize_source(source: str) -> str:
    """
    Normalize source name for lookup.
    
    Handles variations like "Heritage Auctions", "Biddr/Savoca", etc.
    """
    source_lower = source.lower().strip()
    
    # Handle sub-houses (e.g., "Biddr/Savoca" -> "biddr")
    if "/" in source_lower:
        source_lower = source_lower.split("/")[0]
    
    # Common variations
    if "heritage" in source_lower:
        return "heritage"
    if "cng" in source_lower or "classical numismatic" in source_lower:
        return "cng"
    if "biddr" in source_lower:
        return "biddr"
    if "roma" in source_lower:
        return "roma"
    if "agora" in source_lower:
        return "agora"
    if "ebay" in source_lower:
        return "ebay"
    if "ngc" in source_lower:
        return "ngc"
    if "pcgs" in source_lower:
        return "pcgs"
    
    return source_lower


def get_field_trust(field: str, source: str) -> FieldTrust:
    """
    Get trust configuration for a field from a source.
    
    Args:
        field: Field name (e.g., "weight_g", "grade")
        source: Source name (e.g., "Heritage", "CNG", "eBay")
        
    Returns:
        FieldTrust configuration for this field/source combination
    """
    source_normalized = normalize_source(source)
    
    # Check matrix first
    if field in TRUST_MATRIX:
        source_trust = TRUST_MATRIX[field].get(source_normalized)
        if source_trust:
            return source_trust
    
    # Fall back to source defaults
    if source_normalized in DEFAULT_TRUST_BY_SOURCE:
        return DEFAULT_TRUST_BY_SOURCE[source_normalized]
    
    # Ultimate fallback
    return FALLBACK_TRUST


def get_all_trusted_fields(source: str, min_level: TrustLevel = TrustLevel.MEDIUM) -> list[str]:
    """
    Get all fields that meet minimum trust level for a source.
    
    Args:
        source: Source name
        min_level: Minimum trust level required
        
    Returns:
        List of field names meeting the trust threshold
    """
    source_normalized = normalize_source(source)
    trusted_fields = []
    
    trust_order = [
        TrustLevel.AUTHORITATIVE,
        TrustLevel.HIGH,
        TrustLevel.MEDIUM,
        TrustLevel.LOW,
        TrustLevel.UNTRUSTED,
    ]
    min_index = trust_order.index(min_level)
    
    for field, source_map in TRUST_MATRIX.items():
        if source_normalized in source_map:
            field_trust = source_map[source_normalized]
            field_index = trust_order.index(field_trust.trust_level)
            if field_index <= min_index:
                trusted_fields.append(field)
    
    return trusted_fields


# =============================================================================
# Numeric Trust Levels for Auto-Merge System
# =============================================================================

# Special trust levels
USER_TRUST = 30  # Default for user-entered data without verification
USER_VERIFIED_TRUST = 100  # User-verified fields are absolutely protected
UNKNOWN_TRUST = 0  # No source tracking

# Trust level to numeric mapping
TRUST_LEVEL_NUMERIC = {
    TrustLevel.AUTHORITATIVE: 95,
    TrustLevel.HIGH: 80,
    TrustLevel.MEDIUM: 60,
    TrustLevel.LOW: 40,
    TrustLevel.UNTRUSTED: 10,
}

# Numeric trust matrix: source -> field -> trust score
# This is a flattened version for quick numeric lookups
FIELD_TRUST_NUMERIC: dict[str, dict[str, int]] = {
    "heritage": {
        "grade": 90,  # Very good at grading, especially slabbed
        "weight_g": 80,
        "diameter_mm": 80,
        "die_axis": 80,
        "references": 60,  # Sometimes missing volume numbers
        "provenance": 80,
        "obverse_description": 70,
        "reverse_description": 70,
        "obverse_legend": 60,
        "reverse_legend": 60,
        "mint": 80,
        "images": 95,
        "hammer_price": 95,
        "estimate_low": 95,
        "estimate_high": 95,
        "auction_date": 95,
    },
    "cng": {
        "grade": 80,
        "weight_g": 80,
        "diameter_mm": 80,
        "die_axis": 95,  # CNG is meticulous about die axis
        "references": 95,  # Best in class for references
        "provenance": 95,
        "obverse_description": 85,
        "reverse_description": 85,
        "obverse_legend": 85,
        "reverse_legend": 85,
        "mint": 85,
        "images": 95,
        "hammer_price": 95,
        "estimate_low": 95,
        "estimate_high": 95,
        "auction_date": 95,
    },
    "biddr": {
        "grade": 60,
        "weight_g": 70,
        "diameter_mm": 65,
        "die_axis": 60,
        "references": 65,
        "provenance": 60,
        "obverse_description": 60,
        "reverse_description": 60,
        "obverse_legend": 55,
        "reverse_legend": 55,
        "mint": 60,
        "images": 80,
        "hammer_price": 95,
        "estimate_low": 95,
        "estimate_high": 95,
        "auction_date": 95,
    },
    "roma": {
        "grade": 80,
        "weight_g": 80,
        "diameter_mm": 80,
        "die_axis": 80,
        "references": 80,
        "provenance": 80,
        "obverse_description": 80,
        "reverse_description": 80,
        "obverse_legend": 80,
        "reverse_legend": 80,
        "mint": 80,
        "images": 95,
        "hammer_price": 95,
        "estimate_low": 95,
        "estimate_high": 95,
        "auction_date": 95,
    },
    "agora": {
        "grade": 60,
        "weight_g": 70,
        "diameter_mm": 70,
        "die_axis": 60,
        "references": 70,
        "provenance": 60,
        "obverse_description": 60,
        "reverse_description": 60,
        "mint": 65,
        "images": 80,
        "hammer_price": 95,
        "estimate_low": 95,
        "estimate_high": 95,
        "auction_date": 95,
    },
    "ebay": {
        "grade": 40,  # Seller grades are highly suspect
        "weight_g": 60,  # Usually accurate if provided
        "diameter_mm": 55,
        "die_axis": 40,
        "references": 40,  # Often wrong or fabricated
        "provenance": 30,
        "obverse_description": 40,
        "reverse_description": 40,
        "obverse_legend": 35,
        "reverse_legend": 35,
        "mint": 40,
        "images": 70,  # Images are images
        "hammer_price": 95,  # Price is factual
        "estimate_low": 30,  # eBay doesn't have formal estimates
        "estimate_high": 30,
        "auction_date": 95,
    },
    "ngc": {
        "grade": 95,  # Authoritative for grades
        "certification_number": 95,
        "strike_score": 95,
        "surface_score": 95,
    },
    "pcgs": {
        "grade": 95,
        "certification_number": 95,
    },
}

# Default trust by source when field not in matrix
DEFAULT_TRUST_NUMERIC: dict[str, int] = {
    "heritage": 65,
    "cng": 70,
    "biddr": 55,
    "roma": 70,
    "agora": 55,
    "ebay": 35,
    "ngc": 80,
    "pcgs": 80,
}


def get_field_trust_numeric(
    source: str | None, 
    field: str, 
    context: dict | None = None
) -> int:
    """
    Get numeric trust level for a field from a source.
    
    Args:
        source: Source name (e.g., "CNG", "Heritage") or None/empty for user
        field: Field name (e.g., "weight_g", "grade")
        context: Optional context dict with:
            - is_slabbed: bool - if True, Heritage grades get boost
            - auction_age_years: float - older auctions get penalty
            - user_verified: bool - if True, return USER_VERIFIED_TRUST
            
    Returns:
        Numeric trust level (0-100)
    """
    # Handle user-verified fields
    if context and context.get("user_verified"):
        return USER_VERIFIED_TRUST
    
    # Handle no source (user-entered data)
    if not source or source.lower() in ("user", "manual", "import"):
        return USER_TRUST
    
    source_normalized = normalize_source(source)
    
    # Get base trust from numeric matrix
    source_trust = FIELD_TRUST_NUMERIC.get(source_normalized, {})
    base_trust = source_trust.get(field)
    
    if base_trust is None:
        # Fall back to source default
        base_trust = DEFAULT_TRUST_NUMERIC.get(source_normalized, 50)
    
    # Apply context adjustments
    if context:
        # Heritage slabbed coins get AUTHORITATIVE grade trust
        if source_normalized == "heritage" and field == "grade":
            if context.get("is_slabbed"):
                base_trust = 95
        
        # Old auctions (> 2 years) get trust penalty
        auction_age = context.get("auction_age_years", 0)
        if auction_age > 2:
            penalty = min(10, int(auction_age * 2))  # Max 10 point penalty
            base_trust = max(base_trust - penalty, 30)
    
    return base_trust


def compare_trust(
    current_source: str | None,
    current_field: str,
    auction_source: str,
    auction_field: str,
    context: dict | None = None
) -> tuple[int, int, int]:
    """
    Compare trust levels between current value and auction value.
    
    Returns:
        (current_trust, auction_trust, difference)
        Positive difference means auction is more trusted.
    """
    current_trust = get_field_trust_numeric(current_source, current_field, context)
    auction_trust = get_field_trust_numeric(auction_source, auction_field, context)
    
    return current_trust, auction_trust, auction_trust - current_trust
