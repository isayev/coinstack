"""
Shared Physical Data Parser

Consolidated parsing logic for extracting physical measurements from auction descriptions.
Handles weight (g/gm/grams), diameter (mm), and die axis (h) across various formats.

Usage:
    from src.infrastructure.scrapers.shared.physical_parser import parse_physical
    
    text = "19mm, 3.45g, 6h"
    physical = parse_physical(text)
    # Returns PhysicalData(diameter_mm=19.0, weight_g=3.45, die_axis_hours=6)
"""

import re
from typing import Optional, Tuple
from src.infrastructure.scrapers.shared.models import PhysicalData


# =============================================================================
# REGEX PATTERNS
# =============================================================================

# Weight patterns - handles various formats
WEIGHT_PATTERNS = [
    # Standard: "3.45g", "3.45 g", "3.45gm", "3.45 gm", "3.45 grams"
    re.compile(r'(?P<weight>\d+(?:[.,]\d+)?)\s*(?:g(?:m|rams?)?)\b', re.I),
    # Parenthetical: "(3.45 g)"
    re.compile(r'\((?P<weight>\d+(?:[.,]\d+)?)\s*(?:g(?:m|rams?)?)\)', re.I),
    # With label: "Weight: 3.45g"
    re.compile(r'weight[:\s]+(?P<weight>\d+(?:[.,]\d+)?)\s*(?:g(?:m|rams?)?)?', re.I),
    # German format: "3,45 g"
    re.compile(r'(?P<weight>\d+,\d+)\s*g\b', re.I),
]

# Diameter patterns
DIAMETER_PATTERNS = [
    # Standard: "19mm", "19 mm", "19-20mm"
    re.compile(r'(?P<diam>\d+(?:[.,]\d+)?)\s*(?:-\s*\d+(?:[.,]\d+)?)?\s*mm\b', re.I),
    # Parenthetical: "(19mm)"
    re.compile(r'\((?P<diam>\d+(?:[.,]\d+)?)\s*mm\)', re.I),
    # With label: "Diameter: 19mm"
    re.compile(r'diam(?:eter)?[:\s]+(?P<diam>\d+(?:[.,]\d+)?)\s*(?:mm)?', re.I),
    # Range format: "19-20 mm" - take first value
    re.compile(r'(?P<diam>\d+(?:[.,]\d+)?)\s*-\s*\d+(?:[.,]\d+)?\s*mm\b', re.I),
]

# Die axis patterns - handles clock position notation
DIE_AXIS_PATTERNS = [
    # Standard: "6h", "6 h", "12h"
    re.compile(r'\b(?P<axis>1[0-2]|[1-9])\s*h\b', re.I),
    # Written: "6 o'clock"
    re.compile(r"\b(?P<axis>1[0-2]|[1-9])\s*o['\u2019]?\s*clock\b", re.I),
    # With label: "Die axis: 6h"
    re.compile(r'die\s*axis[:\s]+(?P<axis>1[0-2]|[1-9])\s*h?\b', re.I),
    # Parenthetical: "(6h)"
    re.compile(r'\((?P<axis>1[0-2]|[1-9])\s*h\)', re.I),
]

# Thickness patterns (less common)
THICKNESS_PATTERNS = [
    re.compile(r'(?P<thick>\d+(?:[.,]\d+)?)\s*mm\s*thick', re.I),
    re.compile(r'thickness[:\s]+(?P<thick>\d+(?:[.,]\d+)?)\s*mm', re.I),
]

# Combined pattern for title parsing (Heritage-style)
# Matches: "19mm (3.45 gm, 6h)"
COMBINED_PHYSICAL_PATTERN = re.compile(
    r'(?P<diam>\d+(?:[.,]\d+)?)\s*mm'
    r'\s*\(\s*'
    r'(?P<weight>\d+(?:[.,]\d+)?)\s*(?:g(?:m|rams?)?)?'
    r'(?:,?\s*(?P<axis>1[0-2]|[1-9])\s*h)?'
    r'\s*\)',
    re.I
)


# =============================================================================
# PARSING FUNCTIONS
# =============================================================================

def parse_physical(text: str) -> PhysicalData:
    """
    Parse physical measurements from text.
    
    Extracts weight, diameter, and die axis from various formats:
    - Heritage: "19mm (3.45 gm, 6h)"
    - CNG: "19mm, 3.45g, 6h"
    - Biddr: "19 mm; 3,45 g; 6h"
    - eBay: Various user formats
    
    Args:
        text: Description text containing measurements
    
    Returns:
        PhysicalData with extracted values (None for missing)
    
    Example:
        >>> data = parse_physical("19mm (3.45 gm, 6h)")
        >>> data.diameter_mm
        19.0
        >>> data.weight_g
        3.45
        >>> data.die_axis_hours
        6
    """
    if not text:
        return PhysicalData()
    
    # Try combined pattern first (Heritage-style title)
    combined_match = COMBINED_PHYSICAL_PATTERN.search(text)
    if combined_match:
        return PhysicalData(
            diameter_mm=_parse_number(combined_match.group('diam')),
            weight_g=_parse_number(combined_match.group('weight')),
            die_axis_hours=_parse_die_axis(combined_match.group('axis'))
        )
    
    # Parse individual components
    return PhysicalData(
        diameter_mm=_extract_diameter(text),
        weight_g=_extract_weight(text),
        die_axis_hours=_extract_die_axis(text),
        thickness_mm=_extract_thickness(text)
    )


def _parse_number(value: Optional[str]) -> Optional[float]:
    """Parse a number string, handling both US and European formats."""
    if not value:
        return None
    try:
        # Handle European format (comma as decimal)
        normalized = value.replace(',', '.')
        return float(normalized)
    except (ValueError, AttributeError):
        return None


def _parse_die_axis(value: Optional[str]) -> Optional[int]:
    """Parse die axis value."""
    if not value:
        return None
    try:
        axis = int(value)
        if 0 <= axis <= 12:
            return axis
        return None
    except (ValueError, AttributeError):
        return None


def _extract_weight(text: str) -> Optional[float]:
    """Extract weight in grams from text."""
    for pattern in WEIGHT_PATTERNS:
        match = pattern.search(text)
        if match:
            return _parse_number(match.group('weight'))
    return None


def _extract_diameter(text: str) -> Optional[float]:
    """Extract diameter in mm from text."""
    for pattern in DIAMETER_PATTERNS:
        match = pattern.search(text)
        if match:
            return _parse_number(match.group('diam'))
    return None


def _extract_die_axis(text: str) -> Optional[int]:
    """Extract die axis in clock hours from text."""
    for pattern in DIE_AXIS_PATTERNS:
        match = pattern.search(text)
        if match:
            return _parse_die_axis(match.group('axis'))
    return None


def _extract_thickness(text: str) -> Optional[float]:
    """Extract thickness in mm from text."""
    for pattern in THICKNESS_PATTERNS:
        match = pattern.search(text)
        if match:
            return _parse_number(match.group('thick'))
    return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def parse_weight_with_unit(text: str) -> Tuple[Optional[float], str]:
    """
    Parse weight and return both value and detected unit.
    
    Args:
        text: Text containing weight
    
    Returns:
        Tuple of (weight_in_grams, original_unit)
    
    Example:
        >>> parse_weight_with_unit("3.45 gm")
        (3.45, 'gm')
    """
    for pattern in WEIGHT_PATTERNS:
        match = pattern.search(text)
        if match:
            weight = _parse_number(match.group('weight'))
            # Extract unit from match
            full_match = match.group(0)
            if 'grams' in full_match.lower():
                unit = 'grams'
            elif 'gm' in full_match.lower():
                unit = 'gm'
            else:
                unit = 'g'
            return weight, unit
    return None, ''


def convert_ounces_to_grams(oz: float) -> float:
    """Convert troy ounces to grams (for eBay US listings)."""
    return oz * 31.1035


def convert_inches_to_mm(inches: float) -> float:
    """Convert inches to millimeters (for eBay US listings)."""
    return inches * 25.4


def validate_physical_data(data: PhysicalData) -> bool:
    """
    Validate physical data is within reasonable ranges for ancient coins.
    
    Args:
        data: PhysicalData to validate
    
    Returns:
        True if all values are within reasonable ranges
    """
    # Weight: 0.1g to 500g (covers tiny bronze to large gold medallions)
    if data.weight_g is not None:
        if data.weight_g < 0.1 or data.weight_g > 500:
            return False
    
    # Diameter: 5mm to 100mm (covers tiny fractions to large medallions)
    if data.diameter_mm is not None:
        if data.diameter_mm < 5 or data.diameter_mm > 100:
            return False
    
    # Die axis: 0-12 (clock positions)
    if data.die_axis_hours is not None:
        if data.die_axis_hours < 0 or data.die_axis_hours > 12:
            return False
    
    return True
