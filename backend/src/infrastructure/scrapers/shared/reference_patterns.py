"""
Shared Reference Pattern Extraction

Consolidated regex patterns for extracting catalog references from auction descriptions.
Supports: RIC, Crawford, RSC, RPC, Sear, BMC, Cohen, Sydenham, SNG, MIR, Calicó, etc.

Usage:
    from src.infrastructure.scrapers.shared.reference_patterns import extract_references
    
    text = "RIC II.1 756; Crawford 44/5; RSC 162"
    refs = extract_references(text)
    # Returns list of CatalogReference objects
"""

import re
from typing import List, Optional, Tuple, Pattern
from src.infrastructure.scrapers.shared.models import CatalogReference


# =============================================================================
# REFERENCE PATTERN DEFINITIONS
# =============================================================================

# Each tuple: (compiled_pattern, catalog_name, has_volume)
# Named groups: vol (volume), num (number), suffix (optional qualifier)

REFERENCE_PATTERNS: List[Tuple[Pattern, str, bool]] = [
    # -------------------------------------------------------------------------
    # RIC (Roman Imperial Coinage) - most common
    # Formats: "RIC II.1 756", "RIC V.I 160", "RIC III 676 (Aurelius)"
    # -------------------------------------------------------------------------
    (
        re.compile(
            r'RIC\s+(?P<vol>[IVX]+(?:\.\d)?(?:/[12])?)\s+(?P<num>\d+[a-z]?)'
            r'(?:\s*\((?P<suffix>[^)]+)\))?',
            re.I
        ),
        'RIC',
        True
    ),
    
    # -------------------------------------------------------------------------
    # Crawford (Roman Republican Coinage)
    # Formats: "Crawford 44/5", "Cr. 335/1c", "Crawford 463/3"
    # -------------------------------------------------------------------------
    (
        re.compile(
            r'(?:Crawford|Cr\.?)\s*(?P<num>\d+/\d+[a-z]?)',
            re.I
        ),
        'Crawford',
        False
    ),
    
    # -------------------------------------------------------------------------
    # RSC (Roman Silver Coins / Seaby)
    # Formats: "RSC 162", "RSC 123a"
    # -------------------------------------------------------------------------
    (
        re.compile(r'RSC\s+(?P<num>\d+[a-z]?)', re.I),
        'RSC',
        False
    ),
    
    # -------------------------------------------------------------------------
    # RPC (Roman Provincial Coinage)
    # Formats: "RPC I 1234", "RPC IV.3 5678"
    # -------------------------------------------------------------------------
    (
        re.compile(
            r'RPC\s+(?P<vol>[IVX]+(?:\.\d)?)\s+(?P<num>\d+)',
            re.I
        ),
        'RPC',
        True
    ),
    
    # -------------------------------------------------------------------------
    # Sear (Roman Coins and Their Values)
    # Formats: "Sear 1234", "S 1234"
    # -------------------------------------------------------------------------
    (
        re.compile(r'(?:Sear|S\.?)\s+(?P<num>\d+)', re.I),
        'Sear',
        False
    ),
    
    # -------------------------------------------------------------------------
    # BMC (British Museum Catalogue)
    # Formats: "BMC 123", "BMC RE 456"
    # -------------------------------------------------------------------------
    (
        re.compile(
            r'BMC\s+(?:(?P<vol>[A-Z]+)\s+)?(?P<num>\d+)',
            re.I
        ),
        'BMC',
        True
    ),
    
    # -------------------------------------------------------------------------
    # Cohen
    # Formats: "Cohen 123", "C. 456"
    # -------------------------------------------------------------------------
    (
        re.compile(r'(?:Cohen|C\.)\s+(?P<num>\d+)', re.I),
        'Cohen',
        False
    ),
    
    # -------------------------------------------------------------------------
    # Sydenham (Coinage of the Roman Republic)
    # Formats: "Sydenham 549", "Syd. 549"
    # -------------------------------------------------------------------------
    (
        re.compile(r'(?:Sydenham|Syd\.?)\s+(?P<num>\d+[a-z]?)', re.I),
        'Sydenham',
        False
    ),
    
    # -------------------------------------------------------------------------
    # SNG (Sylloge Nummorum Graecorum)
    # Formats: "SNG Copenhagen 123", "SNG ANS 456"
    # -------------------------------------------------------------------------
    (
        re.compile(
            r'SNG\s+(?P<vol>[\w]+)\s+(?P<num>\d+)',
            re.I
        ),
        'SNG',
        True
    ),
    
    # -------------------------------------------------------------------------
    # MIR (Moneta Imperii Romani)
    # Formats: "MIR 18, 10-4a", "MIR 14 1234"
    # -------------------------------------------------------------------------
    (
        re.compile(
            r'MIR\s+(?P<vol>\d+),?\s*(?P<num>[\d\-]+[a-z]?)',
            re.I
        ),
        'MIR',
        True
    ),
    
    # -------------------------------------------------------------------------
    # Calicó (Spanish Coinage)
    # Formats: "Calicó 1234", "Calicó 567a"
    # -------------------------------------------------------------------------
    (
        re.compile(r'Calicó\s+(?P<num>\d+[a-z]?)', re.I),
        'Calicó',
        False
    ),
    
    # -------------------------------------------------------------------------
    # BMCRR (British Museum Catalogue Roman Republic)
    # Formats: "BMCRR 123"
    # -------------------------------------------------------------------------
    (
        re.compile(r'BMCRR\s+(?P<num>\d+)', re.I),
        'BMCRR',
        False
    ),
    
    # -------------------------------------------------------------------------
    # CRR (Coinage of the Roman Republic)
    # Formats: "CRR 123"
    # -------------------------------------------------------------------------
    (
        re.compile(r'CRR\s+(?P<num>\d+)', re.I),
        'CRR',
        False
    ),
    
    # -------------------------------------------------------------------------
    # DOC (Dumbarton Oaks Catalogue - Byzantine)
    # Formats: "DOC I 123", "DOC 456"
    # -------------------------------------------------------------------------
    (
        re.compile(
            r'DOC\s+(?:(?P<vol>[IVX]+)\s+)?(?P<num>\d+)',
            re.I
        ),
        'DOC',
        True
    ),
    
    # -------------------------------------------------------------------------
    # Sear Byzantine (Byzantine Coins and Their Values)
    # Formats: "SB 1234", "Sear Byz 1234"
    # -------------------------------------------------------------------------
    (
        re.compile(r'(?:SB|Sear\s+Byz(?:antine)?)\s+(?P<num>\d+)', re.I),
        'SB',
        False
    ),
    
    # -------------------------------------------------------------------------
    # Babelon (Roman Republican Coinage)
    # Formats: "Bab. 123", "Babelon 456"
    # -------------------------------------------------------------------------
    (
        re.compile(r'(?:Babelon|Bab\.?)\s+(?P<num>\d+)', re.I),
        'Babelon',
        False
    ),
]


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_references(
    text: str,
    needs_verification: bool = False
) -> List[CatalogReference]:
    """
    Extract catalog references from text.
    
    Args:
        text: Description text containing references
        needs_verification: Mark all references as needing verification (for eBay)
    
    Returns:
        List of CatalogReference objects, deduplicated by normalized form
    
    Example:
        >>> refs = extract_references("RIC II.1 756; Crawford 44/5")
        >>> [r.normalized for r in refs]
        ['RIC II.1 756', 'Crawford 44/5']
    """
    if not text:
        return []
    
    found_refs: List[CatalogReference] = []
    seen_normalized: set = set()
    
    for pattern, catalog_name, has_volume in REFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groupdict()
            
            volume = groups.get('vol') or groups.get('collection')
            number = groups.get('num', '')
            suffix = groups.get('suffix')
            raw_text = match.group(0).strip()
            
            # Create reference
            ref = CatalogReference(
                catalog=catalog_name,
                volume=volume,
                number=number,
                suffix=suffix,
                raw_text=raw_text,
                needs_verification=needs_verification
            )
            
            # Deduplicate by normalized form
            if ref.normalized not in seen_normalized:
                seen_normalized.add(ref.normalized)
                found_refs.append(ref)
    
    return found_refs


def extract_primary_reference(text: str) -> Optional[CatalogReference]:
    """
    Extract the primary (first) catalog reference from text.
    
    Useful when you only need the main reference.
    
    Args:
        text: Description text
    
    Returns:
        First CatalogReference found, or None
    """
    refs = extract_references(text)
    return refs[0] if refs else None


def normalize_reference(raw_ref: str) -> Optional[str]:
    """
    Normalize a raw reference string.
    
    Args:
        raw_ref: Raw reference like "RIC II 756" or "Cr. 44/5"
    
    Returns:
        Normalized form like "RIC II 756" or "Crawford 44/5", or None if not parseable
    """
    refs = extract_references(raw_ref)
    return refs[0].normalized if refs else None


def is_valid_reference(text: str) -> bool:
    """
    Check if text contains at least one valid catalog reference.
    
    Args:
        text: Text to check
    
    Returns:
        True if at least one reference pattern matches
    """
    return len(extract_references(text)) > 0


# =============================================================================
# REFERENCE VALIDATION
# =============================================================================

# Known volume ranges for validation
CATALOG_VOLUMES = {
    'RIC': ['I', 'II', 'II.1', 'II.2', 'III', 'IV', 'IV.1', 'IV.2', 'IV.3', 'V', 'V.1', 'V.2', 'VI', 'VII', 'VIII', 'IX', 'X'],
    'RPC': ['I', 'II', 'III', 'IV', 'IV.1', 'IV.2', 'IV.3', 'IV.4', 'V', 'VI', 'VII', 'VIII', 'IX'],
    'DOC': ['I', 'II', 'III', 'IV', 'V'],
}


def validate_reference_volume(ref: CatalogReference) -> bool:
    """
    Validate that a reference volume is within known ranges.
    
    Args:
        ref: CatalogReference to validate
    
    Returns:
        True if volume is valid or catalog doesn't have known volumes
    """
    if not ref.volume:
        return True
    
    known_volumes = CATALOG_VOLUMES.get(ref.catalog)
    if not known_volumes:
        return True  # No validation data
    
    return ref.volume.upper() in [v.upper() for v in known_volumes]
