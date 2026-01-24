"""
Conflict Classification for Auto-Merge System.

Classifies conflicts between existing coin data and auction data to determine
whether they can be safely auto-merged or require manual review.
"""
from enum import Enum
from typing import Any, Optional
import re


class ConflictType(str, Enum):
    """
    Classification of conflicts between current and auction values.
    
    SAFE types can be auto-merged even at equal trust levels.
    REVIEW types require manual decision.
    """
    # SAFE - Can auto-merge even at equal trust
    MEASUREMENT_TOLERANCE = "measurement_tolerance"  # Within 2% (19.0mm vs 19.1mm)
    GRADE_MINOR = "grade_minor"  # Refinement ("VF" vs "Choice VF")
    REF_ADDITIONAL = "ref_additional"  # Adding new reference
    TEXT_EXPANSION = "text_expansion"  # More detail added
    VALUE_IDENTICAL = "value_identical"  # Same value, different source
    
    # REVIEW REQUIRED - Needs user decision
    MEASUREMENT_SIGNIFICANT = "measurement_significant"  # >2% difference
    GRADE_MAJOR = "grade_major"  # Different grade level ("VF" vs "AU")
    REF_DIFFERENT = "ref_different"  # Different attribution
    TEXT_DIFFERENT = "text_different"  # Contradictory information
    VALUE_CONFLICT = "value_conflict"  # General conflict


# Conflict types that are safe to auto-merge
SAFE_CONFLICT_TYPES = {
    ConflictType.MEASUREMENT_TOLERANCE,
    ConflictType.GRADE_MINOR,
    ConflictType.REF_ADDITIONAL,
    ConflictType.TEXT_EXPANSION,
    ConflictType.VALUE_IDENTICAL,
}


# Grade hierarchy for comparison
GRADE_HIERARCHY = {
    # Base grades in ascending order
    "poor": 1, "p": 1,
    "fair": 2,
    "about good": 3, "ag": 3,
    "good": 4, "g": 4,
    "very good": 5, "vg": 5,
    "fine": 6, "f": 6,
    "very fine": 7, "vf": 7,
    "extremely fine": 8, "ef": 8, "xf": 8,
    "about uncirculated": 9, "au": 9,
    "mint state": 10, "ms": 10, "uncirculated": 10, "unc": 10,
    "fdc": 11,  # Fleur de coin
}

# Grade modifiers that refine but don't change the base grade
GRADE_MODIFIERS = {
    "near", "choice", "good", "superb", "gem", "exceptional",
    "almost", "about", "nearly"
}


def normalize_grade(grade: str) -> tuple[str, int, set[str]]:
    """
    Normalize a grade string to (base_grade, level, modifiers).
    
    Examples:
        "Choice VF" -> ("vf", 7, {"choice"})
        "Good VF" -> ("vf", 7, {"good"})
        "EF" -> ("ef", 8, set())
        "NGC MS 64" -> ("ms", 10, set())
    """
    if not grade:
        return ("", 0, set())
    
    grade_lower = grade.lower().strip()
    
    # Remove NGC/PCGS prefixes and numeric grades
    grade_lower = re.sub(r'^(ngc|pcgs)\s+', '', grade_lower)
    grade_lower = re.sub(r'\s+\d+(/\d+)?$', '', grade_lower)  # Remove "64" or "4/5"
    grade_lower = re.sub(r'\s+\d+$', '', grade_lower)
    
    # Extract modifiers
    modifiers = set()
    words = grade_lower.split()
    base_words = []
    
    for word in words:
        if word in GRADE_MODIFIERS:
            modifiers.add(word)
        else:
            base_words.append(word)
    
    base_grade = " ".join(base_words)
    level = GRADE_HIERARCHY.get(base_grade, 0)
    
    # Try abbreviations if full name didn't match
    if level == 0 and base_grade:
        # Try common abbreviations
        for full, abbrev_level in GRADE_HIERARCHY.items():
            if base_grade == full or base_grade.replace(" ", "") == full.replace(" ", ""):
                level = abbrev_level
                break
    
    return (base_grade, level, modifiers)


def classify_grade_conflict(old_grade: str, new_grade: str) -> ConflictType:
    """
    Classify a grade conflict.
    
    Minor: Same base grade, different modifiers (VF vs Choice VF)
    Major: Different base grades (VF vs AU)
    """
    if not old_grade or not new_grade:
        return ConflictType.VALUE_CONFLICT
    
    old_base, old_level, old_mods = normalize_grade(old_grade)
    new_base, new_level, new_mods = normalize_grade(new_grade)
    
    # Same normalized grade
    if old_level == new_level:
        if old_mods != new_mods:
            # Same grade, different modifiers (VF vs Choice VF)
            return ConflictType.GRADE_MINOR
        else:
            # Identical
            return ConflictType.VALUE_IDENTICAL
    
    # One grade level difference might be minor
    if abs(old_level - new_level) == 1:
        # Check if it's just a refinement (e.g., "Fine" vs "Good VF")
        # This is borderline - we'll call it major to be safe
        return ConflictType.GRADE_MAJOR
    
    # Significant grade difference
    return ConflictType.GRADE_MAJOR


def classify_reference_conflict(
    old_refs: Any, 
    new_refs: Any
) -> ConflictType:
    """
    Classify a reference conflict.
    
    Additional: New refs include all old refs plus more
    Different: New refs contradict or exclude old refs
    """
    # Normalize to lists
    if isinstance(old_refs, str):
        old_list = [r.strip() for r in old_refs.split(',')]
    elif isinstance(old_refs, list):
        old_list = old_refs
    else:
        old_list = []
    
    if isinstance(new_refs, str):
        new_list = [r.strip() for r in new_refs.split(',')]
    elif isinstance(new_refs, list):
        new_list = new_refs
    else:
        new_list = []
    
    # Normalize reference strings for comparison
    def normalize_ref(ref: str) -> str:
        return re.sub(r'\s+', ' ', ref.lower().strip())
    
    old_normalized = {normalize_ref(r) for r in old_list if r}
    new_normalized = {normalize_ref(r) for r in new_list if r}
    
    if not old_normalized:
        return ConflictType.REF_ADDITIONAL
    
    if not new_normalized:
        return ConflictType.VALUE_CONFLICT
    
    # Check if new includes all old
    if old_normalized.issubset(new_normalized):
        if len(new_normalized) > len(old_normalized):
            return ConflictType.REF_ADDITIONAL
        else:
            return ConflictType.VALUE_IDENTICAL
    
    # Check overlap
    overlap = old_normalized & new_normalized
    if overlap:
        # Some refs match, some don't - likely different attributions
        return ConflictType.REF_DIFFERENT
    
    # No overlap - completely different
    return ConflictType.REF_DIFFERENT


def classify_measurement_conflict(
    old_value: Optional[float],
    new_value: Optional[float],
    tolerance_pct: float = 2.0
) -> ConflictType:
    """
    Classify a measurement conflict (weight, diameter).
    
    Tolerance: Within tolerance_pct% (default 2%)
    Significant: Beyond tolerance
    """
    if old_value is None or new_value is None:
        return ConflictType.VALUE_CONFLICT
    
    try:
        old_float = float(old_value)
        new_float = float(new_value)
    except (ValueError, TypeError):
        return ConflictType.VALUE_CONFLICT
    
    if old_float == 0:
        return ConflictType.VALUE_CONFLICT
    
    diff_pct = abs(old_float - new_float) / old_float * 100
    
    if diff_pct <= tolerance_pct:
        if diff_pct < 0.01:  # Essentially identical
            return ConflictType.VALUE_IDENTICAL
        return ConflictType.MEASUREMENT_TOLERANCE
    
    return ConflictType.MEASUREMENT_SIGNIFICANT


def classify_text_conflict(old_text: str, new_text: str) -> ConflictType:
    """
    Classify a text field conflict (descriptions, legends).
    
    Expansion: New text contains old text plus more
    Different: Texts are contradictory
    """
    if not old_text or not new_text:
        return ConflictType.VALUE_CONFLICT
    
    old_normalized = old_text.lower().strip()
    new_normalized = new_text.lower().strip()
    
    if old_normalized == new_normalized:
        return ConflictType.VALUE_IDENTICAL
    
    # Check if new is expansion of old
    if old_normalized in new_normalized:
        return ConflictType.TEXT_EXPANSION
    
    # Check word overlap
    old_words = set(old_normalized.split())
    new_words = set(new_normalized.split())
    
    overlap = old_words & new_words
    if len(overlap) / max(len(old_words), 1) > 0.7:
        # High overlap - likely expansion or minor difference
        if len(new_words) > len(old_words):
            return ConflictType.TEXT_EXPANSION
    
    return ConflictType.TEXT_DIFFERENT


def classify_conflict(
    field: str, 
    old_value: Any, 
    new_value: Any
) -> ConflictType:
    """
    Main entry point: classify a conflict for any field.
    
    Args:
        field: Field name (weight_g, grade, etc.)
        old_value: Current value in coin
        new_value: Value from auction data
        
    Returns:
        ConflictType indicating severity and auto-merge eligibility
    """
    # Handle None/empty
    if old_value is None or old_value == "" or old_value == []:
        return ConflictType.VALUE_IDENTICAL  # Not really a conflict
    
    if new_value is None or new_value == "" or new_value == []:
        return ConflictType.VALUE_CONFLICT
    
    # Route to specific classifier
    if field in ("weight_g", "diameter_mm"):
        return classify_measurement_conflict(old_value, new_value)
    
    if field in ("grade",):
        return classify_grade_conflict(str(old_value), str(new_value))
    
    if field in ("references", "catalog_references", "primary_reference"):
        return classify_reference_conflict(old_value, new_value)
    
    if field in ("obverse_description", "reverse_description", 
                 "obverse_legend", "reverse_legend", "description"):
        return classify_text_conflict(str(old_value), str(new_value))
    
    # Default: compare as strings
    if str(old_value).lower().strip() == str(new_value).lower().strip():
        return ConflictType.VALUE_IDENTICAL
    
    return ConflictType.VALUE_CONFLICT


def is_safe_conflict(conflict_type: ConflictType) -> bool:
    """Check if a conflict type is safe for auto-merge."""
    return conflict_type in SAFE_CONFLICT_TYPES
