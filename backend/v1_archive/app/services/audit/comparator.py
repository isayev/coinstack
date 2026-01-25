"""
Numismatic-aware field comparator for Roman coin data.

Handles the quirks of ancient numismatic data including:
- Grade equivalence (Ch VF = Choice VF = VF+ = VF 35)
- Latin legend normalization (AVGVSTVS = AUGUSTUS)
- Reference format variations (RIC II 115 = RIC 2, 115)
- Date range overlap detection
- Die axis clock-to-degrees conversion
"""

import re
from dataclasses import dataclass
from typing import Any
from difflib import SequenceMatcher


@dataclass
class ComparisonResult:
    """Result of comparing two field values."""
    
    matches: bool                    # Whether values are considered equivalent
    similarity: float               # 0-1 similarity score
    difference_type: str            # Type of difference found
    normalized_current: Any         # Normalized form of current value
    normalized_auction: Any         # Normalized form of auction value
    notes: str = ""                 # Human-readable explanation
    
    # Difference types:
    # - "exact": Values are identical
    # - "equivalent": Values are semantically equivalent (e.g., VF = Very Fine)
    # - "within_tolerance": Numeric values within acceptable tolerance
    # - "overlapping": Date ranges overlap
    # - "adjacent": Adjacent grade levels (VF vs EF)
    # - "partial": Partial match (some overlap)
    # - "format_diff": Same value, different format
    # - "mismatch": Values do not match
    # - "missing": One or both values missing


class NumismaticComparator:
    """
    Field comparator with Roman numismatic domain knowledge.
    
    Handles the specific quirks of ancient coin data from auction listings.
    """
    
    # ==========================================================================
    # Grade Equivalence Tables
    # ==========================================================================
    
    GRADE_EQUIVALENTS = {
        # Standard Sheldon scale grades
        "p": ["poor", "p", "po", "pr", "poor 1", "p-1", "p1"],
        "fr": ["fair", "fr", "f-2", "fr-2", "fair 2"],
        "ag": ["about good", "ag", "a/g", "ag-3", "ag 3", "almost good"],
        "g": ["good", "g", "gd", "g-4", "g4", "g-6", "g6"],
        "vg": ["very good", "vg", "v.g.", "v g", "vg-8", "vg8", "vg-10", "vg10"],
        "f": ["fine", "f", "fn", "f-12", "f12", "f-15", "f15"],
        "vf": ["very fine", "vf", "v.f.", "v f", "vf-20", "vf20", "vf-25", "vf25", 
               "vf-30", "vf30", "vf-35", "vf35"],
        "ef": ["extremely fine", "ef", "xf", "e.f.", "x.f.", "ef-40", "ef40", 
               "ef-45", "ef45", "xf-40", "xf40", "xf-45", "xf45"],
        "au": ["about uncirculated", "au", "a.u.", "almost unc", "au-50", "au50", 
               "au-53", "au53", "au-55", "au55", "au-58", "au58"],
        "ms": ["mint state", "ms", "unc", "uncirculated", "fdc", "bu", 
               "ms-60", "ms60", "ms-61", "ms61", "ms-62", "ms62", "ms-63", "ms63",
               "ms-64", "ms64", "ms-65", "ms65", "ms-66", "ms66", "ms-67", "ms67"],
        
        # With modifiers - normalize to base + modifier
        "ch vf": ["choice vf", "ch vf", "vf+", "vf plus", "choice very fine"],
        "ch ef": ["choice ef", "ch xf", "choice xf", "ef+", "xf+", 
                  "choice extremely fine"],
        "ch au": ["choice au", "au+", "choice about uncirculated"],
        "gem": ["gem", "gem bu", "gem unc", "superb"],
    }
    
    # Grade ordering for adjacent grade detection
    GRADE_ORDER = ["p", "fr", "ag", "g", "vg", "f", "vf", "ef", "au", "ms"]
    
    # ==========================================================================
    # Legend Normalization
    # ==========================================================================
    
    # Common Latin abbreviation expansions
    LEGEND_EXPANSIONS = {
        "AVG": "AUGUSTUS",
        "AVGVSTVS": "AUGUSTUS",
        "CAES": "CAESAR",
        "IMP": "IMPERATOR",
        "PM": "PONTIFEX MAXIMUS",
        "P M": "PONTIFEX MAXIMUS",
        "PP": "PATER PATRIAE",
        "P P": "PATER PATRIAE",
        "COS": "CONSUL",
        "TR P": "TRIBUNICIA POTESTATE",
        "TRP": "TRIBUNICIA POTESTATE",
        "TRIB POT": "TRIBUNICIA POTESTATE",
        "SC": "SENATUS CONSULTO",
        "S C": "SENATUS CONSULTO",
        "DN": "DOMINUS NOSTER",
        "D N": "DOMINUS NOSTER",
        "PF": "PIUS FELIX",
        "P F": "PIUS FELIX",
    }
    
    # ==========================================================================
    # Reference Format Patterns
    # ==========================================================================
    
    REFERENCE_PATTERNS = [
        # RIC patterns
        (r"RIC\s*(?:vol\.?\s*)?(?:II|2|ii)?\s*[,.]?\s*(\d+[a-z]?)", r"RIC II \1"),
        (r"RIC\s*(?:vol\.?\s*)?(?:I|1|i)\s*[,.]?\s*(\d+[a-z]?)", r"RIC I \1"),
        (r"RIC\s*(?:vol\.?\s*)?(?:III|3|iii)\s*[,.]?\s*(\d+[a-z]?)", r"RIC III \1"),
        (r"RIC\s*(?:vol\.?\s*)?(?:IV|4|iv)\s*[,.]?\s*(\d+[a-z]?)", r"RIC IV \1"),
        (r"RIC\s*(?:vol\.?\s*)?(?:V|5|v)\s*[,.]?\s*(\d+[a-z]?)", r"RIC V \1"),
        
        # Crawford (Roman Republican)
        (r"Crawford\s*(\d+)/(\d+)([a-z]?)", r"Cr. \1/\2\3"),
        (r"Cr\.?\s*(\d+)/(\d+)([a-z]?)", r"Cr. \1/\2\3"),
        
        # RPC patterns
        (r"RPC\s*(?:vol\.?\s*)?(?:I|1|i)?\s*[,.]?\s*(\d+[a-z]?)", r"RPC I \1"),
        (r"RPC\s*(?:vol\.?\s*)?(?:II|2|ii)\s*[,.]?\s*(\d+[a-z]?)", r"RPC II \1"),
        
        # RSC (Roman Silver Coins)
        (r"RSC\s*(\d+[a-z]?)", r"RSC \1"),
        
        # Sear
        (r"Sear\s*(?:RCV)?\s*(\d+)", r"Sear \1"),
        (r"S\s*(\d{4,})", r"Sear \1"),  # S followed by 4+ digits
        
        # BMC
        (r"BMC\s*(\d+)", r"BMC \1"),
        
        # Cohen
        (r"Cohen\s*(\d+)", r"Cohen \1"),
        (r"C\.?\s*(\d+)(?!\d)", r"Cohen \1"),  # C followed by number, not part of larger
    ]
    
    # ==========================================================================
    # Main Comparison Method
    # ==========================================================================
    
    def compare(self, field: str, current: Any, auction: Any) -> ComparisonResult:
        """
        Compare two values with field-specific logic.
        
        Args:
            field: Field name being compared
            current: Current value in coin record
            auction: Value from auction data
            
        Returns:
            ComparisonResult with match status and details
        """
        # Handle None values
        if current is None and auction is None:
            return ComparisonResult(
                matches=True, similarity=1.0, difference_type="exact",
                normalized_current=None, normalized_auction=None
            )
        
        if current is None or auction is None:
            return ComparisonResult(
                matches=False, similarity=0.0, difference_type="missing",
                normalized_current=current, normalized_auction=auction,
                notes="One value is missing"
            )
        
        # Dispatch to field-specific comparator
        comparators = {
            "weight_g": self._compare_weight,
            "diameter_mm": self._compare_diameter,
            "thickness_mm": self._compare_thickness,
            "grade": self._compare_grade,
            "obverse_legend": self._compare_legend,
            "reverse_legend": self._compare_legend,
            "obverse_legend_expanded": self._compare_legend,
            "reverse_legend_expanded": self._compare_legend,
            "reference": self._compare_reference,
            "mint_year_start": self._compare_date_range,
            "mint_year_end": self._compare_date_range,
            "die_axis": self._compare_die_axis,
            "certification_number": self._compare_exact,
        }
        
        comparator = comparators.get(field, self._compare_text)
        return comparator(current, auction)
    
    # ==========================================================================
    # Weight Comparison
    # ==========================================================================
    
    def _compare_weight(self, current: float, auction: float) -> ComparisonResult:
        """Compare weights with tolerance for die wear and measurement variance."""
        try:
            current_f = float(current)
            auction_f = float(auction)
        except (TypeError, ValueError):
            return self._compare_text(str(current), str(auction))
        
        # 3% tolerance for wear/measurement variance
        tolerance_pct = 0.03
        diff = abs(current_f - auction_f)
        diff_pct = diff / max(current_f, auction_f, 0.01)
        
        if diff_pct <= tolerance_pct:
            return ComparisonResult(
                matches=True,
                similarity=1 - diff_pct,
                difference_type="within_tolerance",
                normalized_current=f"{current_f:.3f}g",
                normalized_auction=f"{auction_f:.3f}g",
                notes=f"Weights within {diff_pct*100:.1f}% tolerance"
            )
        else:
            return ComparisonResult(
                matches=False,
                similarity=max(0, 1 - diff_pct),
                difference_type="mismatch",
                normalized_current=f"{current_f:.3f}g",
                normalized_auction=f"{auction_f:.3f}g",
                notes=f"Weight differs by {diff_pct*100:.1f}% ({diff:.3f}g)"
            )
    
    # ==========================================================================
    # Diameter Comparison
    # ==========================================================================
    
    def _compare_diameter(self, current: float, auction: float) -> ComparisonResult:
        """Compare diameters with 1mm tolerance."""
        try:
            current_f = float(current)
            auction_f = float(auction)
        except (TypeError, ValueError):
            return self._compare_text(str(current), str(auction))
        
        diff = abs(current_f - auction_f)
        
        if diff <= 1.0:
            return ComparisonResult(
                matches=True,
                similarity=1 - diff / 10,
                difference_type="within_tolerance",
                normalized_current=f"{current_f:.1f}mm",
                normalized_auction=f"{auction_f:.1f}mm",
                notes=f"Diameters within {diff:.1f}mm tolerance"
            )
        else:
            return ComparisonResult(
                matches=False,
                similarity=max(0, 1 - diff / 10),
                difference_type="mismatch",
                normalized_current=f"{current_f:.1f}mm",
                normalized_auction=f"{auction_f:.1f}mm",
                notes=f"Diameter differs by {diff:.1f}mm"
            )
    
    def _compare_thickness(self, current: float, auction: float) -> ComparisonResult:
        """Compare thickness with 0.5mm tolerance."""
        try:
            current_f = float(current)
            auction_f = float(auction)
        except (TypeError, ValueError):
            return self._compare_text(str(current), str(auction))
        
        diff = abs(current_f - auction_f)
        
        if diff <= 0.5:
            return ComparisonResult(
                matches=True,
                similarity=1 - diff,
                difference_type="within_tolerance",
                normalized_current=f"{current_f:.2f}mm",
                normalized_auction=f"{auction_f:.2f}mm"
            )
        else:
            return ComparisonResult(
                matches=False,
                similarity=max(0, 1 - diff),
                difference_type="mismatch",
                normalized_current=f"{current_f:.2f}mm",
                normalized_auction=f"{auction_f:.2f}mm",
                notes=f"Thickness differs by {diff:.2f}mm"
            )
    
    # ==========================================================================
    # Grade Comparison
    # ==========================================================================
    
    def _compare_grade(self, current: str, auction: str) -> ComparisonResult:
        """Compare grades with equivalence mapping."""
        norm_current = self._normalize_grade(current)
        norm_auction = self._normalize_grade(auction)
        
        if norm_current == norm_auction:
            if current.lower().strip() == auction.lower().strip():
                return ComparisonResult(
                    matches=True, similarity=1.0, difference_type="exact",
                    normalized_current=norm_current.upper(),
                    normalized_auction=norm_auction.upper()
                )
            else:
                return ComparisonResult(
                    matches=True, similarity=1.0, difference_type="equivalent",
                    normalized_current=norm_current.upper(),
                    normalized_auction=norm_auction.upper(),
                    notes="Grades are equivalent (format difference)"
                )
        
        # Check if same base grade (VF vs VF+)
        base_current = norm_current.split()[0] if norm_current else ""
        base_auction = norm_auction.split()[0] if norm_auction else ""
        
        if base_current == base_auction:
            return ComparisonResult(
                matches=True, similarity=0.9, difference_type="equivalent",
                normalized_current=norm_current.upper(),
                normalized_auction=norm_auction.upper(),
                notes="Same base grade, modifier differs"
            )
        
        # Check adjacent grades (VF vs EF is close)
        try:
            idx_c = self.GRADE_ORDER.index(base_current.lower())
            idx_a = self.GRADE_ORDER.index(base_auction.lower())
            if abs(idx_c - idx_a) == 1:
                return ComparisonResult(
                    matches=False, similarity=0.7, difference_type="adjacent",
                    normalized_current=norm_current.upper(),
                    normalized_auction=norm_auction.upper(),
                    notes="Adjacent grades - minor difference"
                )
        except ValueError:
            pass
        
        return ComparisonResult(
            matches=False, similarity=0.3, difference_type="mismatch",
            normalized_current=norm_current.upper() if norm_current else current,
            normalized_auction=norm_auction.upper() if norm_auction else auction,
            notes="Grades do not match"
        )
    
    def _normalize_grade(self, grade: str) -> str:
        """Normalize grade to standard form."""
        if not grade:
            return ""
        
        grade_lower = grade.lower().strip()
        
        # Remove NGC/PCGS prefixes and numeric suffixes
        grade_lower = re.sub(r'\b(ngc|pcgs)\s*', '', grade_lower)
        grade_lower = re.sub(r'\s*\d{1,2}\s*$', '', grade_lower)  # Remove trailing numbers
        grade_lower = re.sub(r'-\d{1,2}$', '', grade_lower)  # Remove -XX suffix
        grade_lower = grade_lower.strip()
        
        # Find matching standard grade
        for standard, variants in self.GRADE_EQUIVALENTS.items():
            if grade_lower in variants:
                return standard
        
        return grade_lower
    
    # ==========================================================================
    # Legend Comparison
    # ==========================================================================
    
    def _compare_legend(self, current: str, auction: str) -> ComparisonResult:
        """Compare legends with Latin normalization."""
        norm_current = self._normalize_legend(current)
        norm_auction = self._normalize_legend(auction)
        
        if norm_current == norm_auction:
            if current.upper().strip() == auction.upper().strip():
                return ComparisonResult(
                    matches=True, similarity=1.0, difference_type="exact",
                    normalized_current=norm_current, normalized_auction=norm_auction
                )
            else:
                return ComparisonResult(
                    matches=True, similarity=1.0, difference_type="format_diff",
                    normalized_current=norm_current, normalized_auction=norm_auction,
                    notes="Legends match after normalization"
                )
        
        # Fuzzy match
        similarity = SequenceMatcher(None, norm_current, norm_auction).ratio()
        
        if similarity >= 0.9:
            return ComparisonResult(
                matches=True, similarity=similarity, difference_type="equivalent",
                normalized_current=norm_current, normalized_auction=norm_auction,
                notes="Minor spelling/abbreviation difference"
            )
        elif similarity >= 0.7:
            return ComparisonResult(
                matches=False, similarity=similarity, difference_type="partial",
                normalized_current=norm_current, normalized_auction=norm_auction,
                notes="Significant differences in legend"
            )
        else:
            return ComparisonResult(
                matches=False, similarity=similarity, difference_type="mismatch",
                normalized_current=norm_current, normalized_auction=norm_auction,
                notes="Legends do not match"
            )
    
    def _normalize_legend(self, legend: str) -> str:
        """Normalize Roman legend for comparison."""
        if not legend:
            return ""
        
        # Uppercase and clean
        normalized = legend.upper().strip()
        
        # Remove interpuncts and punctuation
        normalized = re.sub(r'[•·.,:;\-\/]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # V→U substitution (AVGVSTVS → AUGUSTUS)
        # This is a simplification - real implementation would be context-aware
        normalized = normalized.replace('V', 'U')
        
        return normalized
    
    # ==========================================================================
    # Reference Comparison
    # ==========================================================================
    
    def _compare_reference(self, current: str, auction: str) -> ComparisonResult:
        """Compare catalog references with format normalization."""
        norm_current = self._normalize_reference(current)
        norm_auction = self._normalize_reference(auction)
        
        if norm_current == norm_auction:
            return ComparisonResult(
                matches=True, similarity=1.0, 
                difference_type="exact" if current == auction else "format_diff",
                normalized_current=norm_current, normalized_auction=norm_auction
            )
        
        # Check if one contains the other (partial match)
        if norm_current in norm_auction or norm_auction in norm_current:
            return ComparisonResult(
                matches=True, similarity=0.9, difference_type="equivalent",
                normalized_current=norm_current, normalized_auction=norm_auction,
                notes="References overlap"
            )
        
        # Check if same system, different number
        current_parts = self._parse_reference_parts(norm_current)
        auction_parts = self._parse_reference_parts(norm_auction)
        
        if current_parts and auction_parts:
            if current_parts.get("system") == auction_parts.get("system"):
                return ComparisonResult(
                    matches=False, similarity=0.3, difference_type="mismatch",
                    normalized_current=norm_current, normalized_auction=norm_auction,
                    notes=f"Same catalog system, different numbers"
                )
        
        return ComparisonResult(
            matches=False, similarity=0.0, difference_type="mismatch",
            normalized_current=norm_current, normalized_auction=norm_auction
        )
    
    def _normalize_reference(self, ref: str) -> str:
        """Normalize catalog reference format."""
        if not ref:
            return ""
        
        normalized = ref.strip()
        
        for pattern, replacement in self.REFERENCE_PATTERNS:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        return normalized.upper()
    
    def _parse_reference_parts(self, ref: str) -> dict | None:
        """Parse reference into system and number parts."""
        if not ref:
            return None
        
        ref_upper = ref.upper()
        
        # Try to identify system
        systems = {
            "RIC": r"RIC\s*([IVX]+|\d+)?\s*(\d+[a-z]?)",
            "CR": r"CR\.?\s*(\d+)/(\d+)",
            "RPC": r"RPC\s*([IVX]+|\d+)?\s*(\d+)",
            "SEAR": r"SEAR\s*(\d+)",
            "RSC": r"RSC\s*(\d+)",
            "BMC": r"BMC\s*(\d+)",
            "COHEN": r"COHEN\s*(\d+)",
        }
        
        for system, pattern in systems.items():
            match = re.search(pattern, ref_upper)
            if match:
                return {"system": system, "number": match.group(0)}
        
        return None
    
    # ==========================================================================
    # Date Range Comparison
    # ==========================================================================
    
    def _compare_date_range(self, current: Any, auction: Any) -> ComparisonResult:
        """Compare dates/date ranges with overlap detection."""
        range_current = self._parse_date_value(current)
        range_auction = self._parse_date_value(auction)
        
        if range_current is None or range_auction is None:
            # Fall back to text comparison
            return self._compare_text(str(current), str(auction))
        
        start_c, end_c = range_current
        start_a, end_a = range_auction
        
        # Exact match
        if start_c == start_a and end_c == end_a:
            return ComparisonResult(
                matches=True, similarity=1.0, difference_type="exact",
                normalized_current=self._format_date_range(start_c, end_c),
                normalized_auction=self._format_date_range(start_a, end_a)
            )
        
        # Check for overlap
        overlaps = start_c <= end_a and start_a <= end_c
        
        if overlaps:
            # Calculate overlap percentage
            overlap_start = max(start_c, start_a)
            overlap_end = min(end_c, end_a)
            overlap_size = overlap_end - overlap_start + 1
            total_size = max(end_c, end_a) - min(start_c, start_a) + 1
            similarity = overlap_size / total_size if total_size > 0 else 1.0
            
            return ComparisonResult(
                matches=True, similarity=similarity, difference_type="overlapping",
                normalized_current=self._format_date_range(start_c, end_c),
                normalized_auction=self._format_date_range(start_a, end_a),
                notes="Date ranges overlap"
            )
        else:
            return ComparisonResult(
                matches=False, similarity=0.0, difference_type="mismatch",
                normalized_current=self._format_date_range(start_c, end_c),
                normalized_auction=self._format_date_range(start_a, end_a),
                notes="Date ranges do not overlap"
            )
    
    def _parse_date_value(self, value: Any) -> tuple[int, int] | None:
        """Parse date value into (start_year, end_year) tuple."""
        if value is None:
            return None
        
        # If already an integer, treat as single year
        if isinstance(value, (int, float)):
            year = int(value)
            return (year, year)
        
        # Parse string
        date_str = str(value).upper().strip()
        date_str = date_str.replace("AD", "CE").replace("BC", "BCE")
        date_str = re.sub(r'[Cc]\.?\s*', '', date_str)  # Remove circa
        
        # Check for BCE indicator
        is_bce = "BCE" in date_str
        date_str = date_str.replace("BCE", "").replace("CE", "").strip()
        
        # Single year
        single = re.match(r'^(\d+)$', date_str)
        if single:
            year = int(single.group(1))
            if is_bce:
                year = -year
            return (year, year)
        
        # Range: "138-161" or "138 - 161"
        range_match = re.match(r'(\d+)\s*[-–]\s*(\d+)', date_str)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if is_bce:
                start, end = -start, -end
            return (min(start, end), max(start, end))
        
        return None
    
    def _format_date_range(self, start: int, end: int) -> str:
        """Format date range for display."""
        if start == end:
            if start < 0:
                return f"{abs(start)} BCE"
            return f"{start} CE"
        
        if start < 0 and end < 0:
            return f"{abs(start)}-{abs(end)} BCE"
        elif start < 0:
            return f"{abs(start)} BCE - {end} CE"
        else:
            return f"{start}-{end} CE"
    
    # ==========================================================================
    # Die Axis Comparison
    # ==========================================================================
    
    def _compare_die_axis(self, current: Any, auction: Any) -> ComparisonResult:
        """Compare die axis values (in degrees or clock hours)."""
        deg_c = self._to_degrees(current)
        deg_a = self._to_degrees(auction)
        
        if deg_c is None or deg_a is None:
            return ComparisonResult(
                matches=False, similarity=0.0, difference_type="missing",
                normalized_current=str(current), normalized_auction=str(auction),
                notes="Could not parse die axis value"
            )
        
        # Allow 15° tolerance (half an hour on clock)
        # Handle wraparound at 360°
        diff = min(abs(deg_c - deg_a), 360 - abs(deg_c - deg_a))
        
        if diff <= 15:
            return ComparisonResult(
                matches=True, similarity=1 - diff / 180,
                difference_type="within_tolerance",
                normalized_current=f"{deg_c}° ({deg_c // 30}h)",
                normalized_auction=f"{deg_a}° ({deg_a // 30}h)",
                notes=f"Die axes within {diff}° tolerance"
            )
        else:
            return ComparisonResult(
                matches=False, similarity=max(0, 1 - diff / 180),
                difference_type="mismatch",
                normalized_current=f"{deg_c}° ({deg_c // 30}h)",
                normalized_auction=f"{deg_a}° ({deg_a // 30}h)",
                notes=f"Die axes differ by {diff}°"
            )
    
    def _to_degrees(self, val: Any) -> int | None:
        """Convert die axis value to degrees (0-360)."""
        if val is None:
            return None
        
        if isinstance(val, (int, float)):
            v = int(val)
            # If <= 12, assume clock hours
            if v <= 12:
                return (v * 30) % 360
            return v % 360
        
        # Parse strings like "6h", "6 o'clock", "180°"
        s = str(val).lower().strip()
        m = re.search(r'(\d+)', s)
        if m:
            v = int(m.group(1))
            if 'h' in s or 'clock' in s or v <= 12:
                return (v * 30) % 360
            return v % 360
        
        return None
    
    # ==========================================================================
    # Generic Comparisons
    # ==========================================================================
    
    def _compare_exact(self, current: Any, auction: Any) -> ComparisonResult:
        """Exact string comparison (for certification numbers, etc.)."""
        str_c = str(current).strip() if current else ""
        str_a = str(auction).strip() if auction else ""
        
        if str_c == str_a:
            return ComparisonResult(
                matches=True, similarity=1.0, difference_type="exact",
                normalized_current=str_c, normalized_auction=str_a
            )
        
        # Case-insensitive
        if str_c.lower() == str_a.lower():
            return ComparisonResult(
                matches=True, similarity=1.0, difference_type="format_diff",
                normalized_current=str_c, normalized_auction=str_a,
                notes="Case difference only"
            )
        
        return ComparisonResult(
            matches=False, similarity=0.0, difference_type="mismatch",
            normalized_current=str_c, normalized_auction=str_a
        )
    
    def _compare_text(self, current: str, auction: str) -> ComparisonResult:
        """Generic text comparison with fuzzy matching."""
        if not current or not auction:
            return ComparisonResult(
                matches=False, similarity=0.0, difference_type="missing",
                normalized_current=current, normalized_auction=auction
            )
        
        norm_c = str(current).lower().strip()
        norm_a = str(auction).lower().strip()
        
        if norm_c == norm_a:
            return ComparisonResult(
                matches=True, similarity=1.0, difference_type="exact",
                normalized_current=current, normalized_auction=auction
            )
        
        similarity = SequenceMatcher(None, norm_c, norm_a).ratio()
        
        if similarity >= 0.9:
            return ComparisonResult(
                matches=True, similarity=similarity, difference_type="equivalent",
                normalized_current=current, normalized_auction=auction
            )
        elif similarity >= 0.6:
            return ComparisonResult(
                matches=False, similarity=similarity, difference_type="partial",
                normalized_current=current, normalized_auction=auction
            )
        else:
            return ComparisonResult(
                matches=False, similarity=similarity, difference_type="mismatch",
                normalized_current=current, normalized_auction=auction
            )
