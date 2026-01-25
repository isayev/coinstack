"""
Roman legend abbreviation dictionary for fast expansion.

Handles 80%+ of Roman coin legend expansions without LLM calls.
Uses dictionary lookup first, falls back to LLM for unusual cases.
"""
from typing import Optional
import re


# ============================================================================
# LEGEND ABBREVIATIONS - Comprehensive Roman numismatic dictionary
# ============================================================================

LEGEND_ABBREVIATIONS = {
    # ----- IMPERIAL TITLES -----
    "IMP": "Imperator",
    "IMPP": "Imperatores",  # Two emperors
    "CAES": "Caesar",
    "CAESAR": "Caesar",
    "AVG": "Augustus",
    "AVGG": "Augusti",  # Two Augusti
    "AVGGG": "Augustorum",  # Three Augusti
    "AVGVSTVS": "Augustus",
    "AVGVSTA": "Augusta",
    
    # ----- RELIGIOUS OFFICES -----
    "PM": "Pontifex Maximus",
    "P M": "Pontifex Maximus",
    "PONT": "Pontifex",
    "PONT MAX": "Pontifex Maximus",
    "PONTIF": "Pontifex",
    "PONTIF MAX": "Pontifex Maximus",
    
    # ----- TRIBUNICIAN POWER -----
    "TR P": "Tribunicia Potestate",
    "TRP": "Tribunicia Potestate",
    "TRIB": "Tribunicia",
    "TRIB P": "Tribunicia Potestate",
    "TRIB POT": "Tribunicia Potestate",
    "POT": "Potestate",
    
    # ----- CONSULSHIP -----
    "COS": "Consul",
    "COSS": "Consules",
    "DES": "Designatus",
    "DESIG": "Designatus",
    
    # ----- HONORARY TITLES -----
    "PP": "Pater Patriae",
    "P P": "Pater Patriae",
    "PATER PATRIAE": "Pater Patriae",
    
    # ----- DIVINE/DEIFIED -----
    "DIV": "Divus",
    "DIVI": "Divi",
    "DIVVS": "Divus",
    "DIVA": "Diva",
    "DIVI F": "Divi Filius",
    "DIVIF": "Divi Filius",
    "DIVI N": "Divi Nepos",
    
    # ----- SENATE -----
    "SC": "Senatus Consulto",
    "S C": "Senatus Consulto",
    "SENATVS": "Senatus",
    "CONSVLTO": "Consulto",
    
    # ----- MILITARY TITLES -----
    "GERM": "Germanicus",
    "GERMAN": "Germanicus",
    "DAC": "Dacicus",
    "DACIC": "Dacicus",
    "PART": "Parthicus",
    "PARTH": "Parthicus",
    "ARAB": "Arabicus",
    "ADIAB": "Adiabenicus",
    "BRIT": "Britannicus",
    "BRITAN": "Britannicus",
    "SARM": "Sarmaticus",
    "GOT": "Gothicus",
    "GOTH": "Gothicus",
    "MAX": "Maximus",
    "MAXIMVS": "Maximus",
    
    # ----- IMPERIAL ACCLAMATIONS -----
    "IMP II": "Imperator II",
    "IMP III": "Imperator III",
    "IMP IIII": "Imperator IIII",
    "IMP V": "Imperator V",
    
    # ----- PERSONIFICATIONS -----
    "AEQVITAS": "Aequitas (Equity)",
    "AETERNITAS": "Aeternitas (Eternity)",
    "ANNONA": "Annona (Grain Supply)",
    "BONVS EVENTVS": "Bonus Eventus (Good Fortune)",
    "CLEMENTIA": "Clementia (Clemency)",
    "CONCORDIA": "Concordia (Harmony)",
    "FELICITAS": "Felicitas (Happiness)",
    "FIDES": "Fides (Faith/Loyalty)",
    "FORTVNA": "Fortuna (Fortune)",
    "FORTVNAE": "Fortunae",
    "GENIVS": "Genius (Guardian Spirit)",
    "HILARITAS": "Hilaritas (Joy)",
    "IVSTITIA": "Iustitia (Justice)",
    "LAETITIA": "Laetitia (Joy)",
    "LIBERALITAS": "Liberalitas (Generosity)",
    "LIBERTAS": "Libertas (Liberty)",
    "MONETA": "Moneta (Mint)",
    "NOBILITAS": "Nobilitas (Nobility)",
    "PAX": "Pax (Peace)",
    "PIETAS": "Pietas (Piety)",
    "PROVIDENTIA": "Providentia (Providence)",
    "PVBLICAE": "Publicae (Public)",
    "PVDICITIA": "Pudicitia (Modesty)",
    "ROMA": "Roma (Goddess Rome)",
    "SALVS": "Salus (Health/Safety)",
    "SECVRITAS": "Securitas (Security)",
    "SPES": "Spes (Hope)",
    "VBERITAS": "Uberitas (Fertility)",
    "VICTORIA": "Victoria (Victory)",
    "VIRTVS": "Virtus (Valor/Virtue)",
    
    # ----- REVERSE TYPE MODIFIERS -----
    "AVG": "Augusti",
    "AVGG": "Augustorum",
    "FEL": "Felix",
    "TEMP": "Temporum",
    "PERPETVA": "Perpetua",
    "SAEC": "Saeculi",
    "SAECVLI": "Saeculi",
    "ORBIS": "Orbis",
    "PVB": "Publica",
    "PVBLIC": "Publica",
    "RESTITVTOR": "Restitutor (Restorer)",
    "CONSERVATOR": "Conservator (Preserver)",
    "PROPAGATOR": "Propagator (Extender)",
    "RECTOR": "Rector (Ruler)",
    "INVICTVS": "Invictus (Unconquered)",
    "INDVLGENTIA": "Indulgentia (Indulgence)",
    
    # ----- MILITARY STANDARDS -----
    "LEG": "Legio",
    "COH": "Cohors",
    "PR": "Praetoria",
    "PRAET": "Praetoriana",
    "FID": "Fidelis",
    "P F": "Pia Fidelis",
    "PF": "Pia Fidelis",
    "VIC": "Victrix",
    
    # ----- MINTS -----
    "ROM": "Roma",
    "LVG": "Lugdunum",
    "TR": "Treveri",
    "TICIN": "Ticinum",
    "ANT": "Antiochia",
    "ALEX": "Alexandria",
    "AQ": "Aquileia",
    "AQVIL": "Aquileia",
    "SIS": "Siscia",
    "SIRM": "Sirmium",
    "CONS": "Constantinopolis",
    "CONST": "Constantinopolis",
    "NIK": "Nicomedia",
    "NIC": "Nicomedia",
    "CYZ": "Cyzicus",
    "HER": "Heraclea",
    "SMANT": "Sacra Moneta Antiochiae",
    
    # ----- COMMON WORDS -----
    "EXERCITVS": "Exercitus (Army)",
    "CAESAR": "Caesar",
    "NOB": "Nobilissimus",
    "NOBIL": "Nobilissimus",
    "PRINC": "Princeps",
    "IVVENT": "Iuventutis",
    "IVVENTVTIS": "Iuventutis (Youth)",
    "PER": "Perpetuus",
    "PERP": "Perpetuus",
    
    # ----- NUMBERS (for tribunician power, consulships) -----
    "I": "1",
    "II": "2",
    "III": "3",
    "IIII": "4",
    "IV": "4",
    "V": "5",
    "VI": "6",
    "VII": "7",
    "VIII": "8",
    "VIIII": "9",
    "IX": "9",
    "X": "10",
    "XI": "11",
    "XII": "12",
    "XIII": "13",
    "XIV": "14",
    "XV": "15",
    "XVI": "16",
    "XVII": "17",
    "XVIII": "18",
    "XIX": "19",
    "XX": "20",
    "XXI": "21",
    "XXII": "22",
    
    # ----- REPUBLIC-SPECIFIC -----
    "EX": "Ex",
    "SC": "Senatus Consulto",
    "ARG PVB": "Argento Publico",
    "Q": "Quaestor",
    "AED": "Aedilis",
    "CVR": "Curator",
    "PR": "Praetor",
    "MONEYER": "Moneyer",
    "III VIR": "Triumvir",
    "A A A FF": "Auro Argento Aere Flando Feriundo",
    
    # ----- PROVINCIAL/GREEK -----
    "KOINON": "Koinon (League)",
    "NEOKOROS": "Neokoros (Temple Warden)",
    "METR": "Metropolis",
    "COL": "Colonia",
}


# ============================================================================
# EXPANSION FUNCTIONS
# ============================================================================

def normalize_legend(legend: str) -> str:
    """Normalize a legend string for processing."""
    if not legend:
        return ""
    
    # Uppercase
    normalized = legend.upper()
    
    # Handle common ligatures and special characters
    normalized = normalized.replace("Æ", "AE")
    normalized = normalized.replace("Œ", "OE")
    normalized = normalized.replace("·", " ")
    normalized = normalized.replace("•", " ")
    normalized = normalized.replace(".", " ")
    normalized = normalized.replace("-", " ")
    
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def split_legend(legend: str) -> list[str]:
    """Split a legend into parts for expansion."""
    normalized = normalize_legend(legend)
    
    if not normalized:
        return []
    
    # Split on spaces
    parts = normalized.split()
    
    return parts


def expand_legend(
    legend: str, 
    use_llm_fallback: bool = True
) -> dict:
    """
    Expand a Roman coin legend.
    
    Args:
        legend: The legend string to expand (e.g., "IMP CAES TRAIANO AVG")
        use_llm_fallback: Whether to mark unknown terms for LLM expansion
    
    Returns:
        {
            "original": str,
            "expanded": str,
            "method": "dictionary" | "llm" | "partial",
            "confidence": float,  # 0.0-1.0
            "unknown_terms": list[str],
            "expansion_map": dict[str, str]  # original -> expanded for each part
        }
    """
    if not legend:
        return {
            "original": "",
            "expanded": "",
            "method": "dictionary",
            "confidence": 1.0,
            "unknown_terms": [],
            "expansion_map": {}
        }
    
    parts = split_legend(legend)
    expanded_parts = []
    unknown = []
    expansion_map = {}
    
    for part in parts:
        # Try direct lookup
        if part in LEGEND_ABBREVIATIONS:
            expansion = LEGEND_ABBREVIATIONS[part]
            expanded_parts.append(expansion)
            expansion_map[part] = expansion
        
        # Try with trailing numerals (e.g., "TRP XIIII")
        elif len(part) > 1 and part[-1].isdigit():
            # Split letters from numerals
            match = re.match(r'^([A-Z]+)(\d+)$', part)
            if match:
                letters, nums = match.groups()
                if letters in LEGEND_ABBREVIATIONS:
                    expansion = f"{LEGEND_ABBREVIATIONS[letters]} {nums}"
                    expanded_parts.append(expansion)
                    expansion_map[part] = expansion
                else:
                    expanded_parts.append(part)
                    unknown.append(part)
            else:
                expanded_parts.append(part)
                if len(part) > 2:
                    unknown.append(part)
        
        # Check if it's a Roman numeral (keep as-is)
        elif is_roman_numeral(part):
            expanded_parts.append(part)
            expansion_map[part] = part
        
        # Unknown - keep original
        else:
            expanded_parts.append(part)
            if len(part) > 2:  # Skip single letters and short fragments
                unknown.append(part)
    
    expanded = " ".join(expanded_parts)
    
    # Calculate confidence
    total_parts = len(parts)
    known_parts = total_parts - len(unknown)
    confidence = known_parts / total_parts if total_parts > 0 else 1.0
    
    # Determine method
    if not unknown:
        method = "dictionary"
    elif use_llm_fallback:
        method = "partial"
    else:
        method = "dictionary"
    
    return {
        "original": legend,
        "expanded": expanded,
        "method": method,
        "confidence": round(confidence, 2),
        "unknown_terms": unknown,
        "expansion_map": expansion_map
    }


def is_roman_numeral(s: str) -> bool:
    """Check if a string is a Roman numeral."""
    if not s:
        return False
    
    # Only I, V, X, L, C, D, M
    return bool(re.match(r'^[IVXLCDM]+$', s))


def get_abbreviation(abbr: str) -> Optional[str]:
    """Get the expansion for a single abbreviation."""
    return LEGEND_ABBREVIATIONS.get(abbr.upper())


def search_abbreviations(query: str) -> list[tuple[str, str]]:
    """Search abbreviations by partial match."""
    query_upper = query.upper()
    results = []
    
    for abbr, expansion in LEGEND_ABBREVIATIONS.items():
        if query_upper in abbr or query_upper in expansion.upper():
            results.append((abbr, expansion))
    
    return sorted(results, key=lambda x: x[0])
