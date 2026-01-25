"""
Numismatic terminology synonyms for natural language search.

Maps common collector terminology to database values for intelligent search:
- Dynasty names → ruler lists
- Plural forms → singular denominations
- Colloquial terms → metal/grade values
- Period names → date ranges
"""
from typing import Union


# ============================================================================
# DYNASTY / PERIOD → RULERS
# ============================================================================

DYNASTY_RULERS = {
    # Julio-Claudian (27 BC - AD 68)
    "julio-claudian": ["Augustus", "Tiberius", "Caligula", "Claudius", "Nero"],
    "julio-claudians": ["Augustus", "Tiberius", "Caligula", "Claudius", "Nero"],
    
    # Year of Four Emperors (AD 69)
    "year of four emperors": ["Galba", "Otho", "Vitellius", "Vespasian"],
    "civil war": ["Galba", "Otho", "Vitellius"],
    
    # Flavian (AD 69-96)
    "flavian": ["Vespasian", "Titus", "Domitian"],
    "flavians": ["Vespasian", "Titus", "Domitian"],
    
    # Nerva-Antonine (AD 96-192)
    "nerva-antonine": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius", "Lucius Verus", "Commodus"],
    "antonine": ["Antoninus Pius", "Marcus Aurelius", "Lucius Verus", "Commodus"],
    "antonines": ["Antoninus Pius", "Marcus Aurelius", "Lucius Verus", "Commodus"],
    "adoptive emperors": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius"],
    "five good emperors": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius"],
    
    # Severan (AD 193-235)
    "severan": ["Septimius Severus", "Caracalla", "Geta", "Macrinus", "Elagabalus", "Severus Alexander"],
    "severans": ["Septimius Severus", "Caracalla", "Geta", "Macrinus", "Elagabalus", "Severus Alexander"],
    
    # Crisis of the Third Century (AD 235-284)
    "military emperors": ["Maximinus I", "Gordian I", "Gordian II", "Gordian III", "Philip I", "Decius", "Trebonianus Gallus", "Valerian", "Gallienus"],
    "barracks emperors": ["Maximinus I", "Gordian III", "Philip I", "Decius", "Gallienus"],
    "gallic empire": ["Postumus", "Victorinus", "Tetricus I", "Tetricus II"],
    
    # Tetrarchy (AD 284-324)
    "tetrarchy": ["Diocletian", "Maximian", "Constantius I", "Galerius"],
    "tetrarchs": ["Diocletian", "Maximian", "Constantius I", "Galerius"],
    
    # Constantinian (AD 306-363)
    "constantinian": ["Constantine I", "Constantine II", "Constans", "Constantius II", "Julian"],
    "constantinople": ["Constantine I", "Constantine II", "Constans", "Constantius II"],
    
    # Valentinianic (AD 364-392)
    "valentinianic": ["Valentinian I", "Valens", "Gratian", "Valentinian II"],
    
    # Theodosian (AD 379-455)
    "theodosian": ["Theodosius I", "Arcadius", "Honorius", "Theodosius II"],
    
    # Republic periods
    "late republic": ["Sulla", "Pompey", "Caesar", "Brutus", "Cassius", "Mark Antony", "Octavian"],
    "triumvirate": ["Caesar", "Mark Antony", "Octavian", "Lepidus"],
    "second triumvirate": ["Mark Antony", "Octavian", "Lepidus"],
}


# ============================================================================
# DENOMINATION PLURALS → SINGULAR
# ============================================================================

PLURALS = {
    # Gold
    "aurei": "aureus",
    "solidi": "solidus",
    "tremisses": "tremissis",
    "semisses": "semissis",
    
    # Silver
    "denarii": "denarius",
    "quinarii": "quinarius",
    "antoniniani": "antoninianus",
    "argentei": "argenteus",
    "siliquae": "siliqua",
    "miliarenses": "miliarensis",
    
    # Bronze/Copper
    "sestertii": "sestertius",
    "dupondii": "dupondius",
    "asses": "as",
    "semisses": "semis",
    "quadrantes": "quadrans",
    "folles": "follis",
    "nummi": "nummus",
    "centenionales": "centenionalis",
    
    # Greek
    "drachmae": "drachm",
    "drachms": "drachm",
    "didrachms": "didrachm",
    "tetradrachms": "tetradrachm",
    "staters": "stater",
    "obols": "obol",
    "hemidrachms": "hemidrachm",
}


# ============================================================================
# METAL SYNONYMS
# ============================================================================

METAL_SYNONYMS = {
    # Gold
    "gold": "gold",
    "av": "gold",
    "au": "gold",
    
    # Electrum
    "electrum": "electrum",
    "el": "electrum",
    "white gold": "electrum",
    
    # Silver
    "silver": "silver",
    "ar": "silver",
    "ag": "silver",
    
    # Billon
    "billon": "billon",
    "billion": "billon",  # Common misspelling
    "silvered": "billon",
    
    # Bronze/Copper
    "bronze": "bronze",
    "ae": "ae",
    "copper": "copper",
    "cu": "copper",
    "brass": "orichalcum",
    "orichalcum": "orichalcum",
    "yellow bronze": "orichalcum",
    
    # Potin
    "potin": "potin",
    "tin bronze": "potin",
    
    # Lead
    "lead": "lead",
    "pb": "lead",
}


# ============================================================================
# GRADE SYNONYMS (NGC/PCGS compatible)
# ============================================================================

GRADE_SYNONYMS = {
    # Mint State
    "mint state": "MS",
    "ms": "MS",
    "uncirculated": "MS",
    "unc": "MS",
    "brilliant uncirculated": "MS",
    "bu": "MS",
    "fdc": "MS",  # Fleur de Coin
    
    # About Uncirculated
    "about uncirculated": "AU",
    "almost uncirculated": "AU",
    "au": "AU",
    "choice au": "Choice AU",
    
    # Extremely Fine
    "extremely fine": "EF",
    "extra fine": "EF",
    "ef": "EF",
    "xf": "EF",
    "choice ef": "Choice EF",
    "choice xf": "Choice EF",
    
    # Very Fine
    "very fine": "VF",
    "vf": "VF",
    "choice vf": "Choice VF",
    
    # Fine
    "fine": "F",
    "f": "F",
    "choice f": "Choice F",
    
    # Very Good
    "very good": "VG",
    "vg": "VG",
    
    # Good
    "good": "G",
    "g": "G",
    
    # About Good
    "about good": "AG",
    "almost good": "AG",
    "ag": "AG",
    
    # Fair/Poor
    "fair": "Fair",
    "poor": "Poor",
    "pr": "Poor",
}


# ============================================================================
# CATEGORY SYNONYMS
# ============================================================================

CATEGORY_SYNONYMS = {
    "roman imperial": "imperial",
    "roman empire": "imperial",
    "empire": "imperial",
    "imperial": "imperial",
    
    "roman republic": "republic",
    "republican": "republic",
    "republic": "republic",
    
    "roman provincial": "provincial",
    "provincial": "provincial",
    "greek imperial": "provincial",
    
    "byzantine": "byzantine",
    "eastern roman": "byzantine",
    
    "greek": "greek",
    "hellenic": "greek",
    "hellenistic": "greek",
    
    "celtic": "celtic",
    "gaulish": "celtic",
    "british celtic": "celtic",
    
    "jewish": "judaean",
    "judaean": "judaean",
    "judaea": "judaean",
    
    "migration period": "migration",
    "barbarian": "migration",
    "ostrogothic": "migration",
    "vandal": "migration",
}


# ============================================================================
# PERIOD → DATE RANGES (for filtering)
# ============================================================================

PERIOD_DATES = {
    "roman republic": (-509, -27),
    "late republic": (-133, -27),
    "roman empire": (-27, 476),
    "principate": (-27, 284),
    "dominate": (284, 476),
    "early empire": (-27, 96),
    "high empire": (96, 192),
    "third century crisis": (235, 284),
    "late empire": (284, 476),
    "byzantine": (476, 1453),
    "early byzantine": (476, 717),
}


# ============================================================================
# EXPANSION FUNCTION
# ============================================================================

def expand_search_term(term: str) -> dict:
    """
    Expand a search term into structured filters.
    
    Args:
        term: User search term (e.g., "flavian denarii", "silver EF")
    
    Returns:
        {
            "original": str,
            "rulers": list[str] | None,
            "denomination": str | None,
            "metal": str | None,
            "grade": str | None,
            "category": str | None,
            "date_range": tuple[int, int] | None,
            "matched_terms": list[str]
        }
    """
    term_lower = term.lower().strip()
    words = term_lower.split()
    
    result = {
        "original": term,
        "rulers": None,
        "denomination": None,
        "metal": None,
        "grade": None,
        "category": None,
        "date_range": None,
        "matched_terms": []
    }
    
    # Check each word and multi-word phrases
    for i, word in enumerate(words):
        # Check dynasty/period (single word)
        if word in DYNASTY_RULERS:
            result["rulers"] = DYNASTY_RULERS[word]
            result["matched_terms"].append(word)
        
        # Check plural denomination
        if word in PLURALS:
            result["denomination"] = PLURALS[word]
            result["matched_terms"].append(word)
        
        # Check metal synonym
        if word in METAL_SYNONYMS:
            result["metal"] = METAL_SYNONYMS[word]
            result["matched_terms"].append(word)
        
        # Check grade synonym
        if word in GRADE_SYNONYMS:
            result["grade"] = GRADE_SYNONYMS[word]
            result["matched_terms"].append(word)
        
        # Check category synonym
        if word in CATEGORY_SYNONYMS:
            result["category"] = CATEGORY_SYNONYMS[word]
            result["matched_terms"].append(word)
        
        # Check period dates
        if word in PERIOD_DATES:
            result["date_range"] = PERIOD_DATES[word]
            result["matched_terms"].append(word)
    
    # Check multi-word phrases (up to 4 words)
    for phrase_len in range(2, min(5, len(words) + 1)):
        for i in range(len(words) - phrase_len + 1):
            phrase = " ".join(words[i:i + phrase_len])
            
            if phrase in DYNASTY_RULERS:
                result["rulers"] = DYNASTY_RULERS[phrase]
                result["matched_terms"].append(phrase)
            
            if phrase in PERIOD_DATES:
                result["date_range"] = PERIOD_DATES[phrase]
                result["matched_terms"].append(phrase)
            
            if phrase in CATEGORY_SYNONYMS:
                result["category"] = CATEGORY_SYNONYMS[phrase]
                result["matched_terms"].append(phrase)
            
            if phrase in GRADE_SYNONYMS:
                result["grade"] = GRADE_SYNONYMS[phrase]
                result["matched_terms"].append(phrase)
    
    return result


def get_rulers_for_dynasty(dynasty: str) -> list[str]:
    """Get list of rulers for a dynasty/period name."""
    return DYNASTY_RULERS.get(dynasty.lower(), [])


def normalize_denomination(denom: str) -> str:
    """Normalize a denomination (handles plurals)."""
    denom_lower = denom.lower().strip()
    return PLURALS.get(denom_lower, denom)


def normalize_metal(metal: str) -> str:
    """Normalize a metal name."""
    metal_lower = metal.lower().strip()
    return METAL_SYNONYMS.get(metal_lower, metal)


def normalize_grade(grade: str) -> str:
    """Normalize a grade string."""
    grade_lower = grade.lower().strip()
    return GRADE_SYNONYMS.get(grade_lower, grade)
