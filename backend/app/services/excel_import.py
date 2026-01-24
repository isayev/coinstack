"""Excel/CSV import service - Clean refactor with type-only references."""
from pathlib import Path
from typing import List, Dict, Any, Optional
import openpyxl
import csv
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Coin, Mint, CoinReference, ReferenceType
from app.models.coin import Category, Metal
import re
import logging
import unicodedata

# Import parsing functions directly (avoid circular imports)
# The parse_collection.py script can be used standalone
# For import service, we use the existing functions below

logger = logging.getLogger(__name__)


def normalize_text(text: Any) -> Optional[str]:
    """Normalize text while preserving meaningful characters (Greek, bullets, etc.).
    
    Normalizations applied:
    - Convert non-breaking spaces (U+00A0, U+202F) to regular spaces
    - Convert en-dash (–), em-dash (—), minus sign (−) to hyphen (-)
    - Normalize special quotes ("", '', «») to ASCII quotes
    - Collapse multiple spaces to single space
    - Strip leading/trailing whitespace
    
    Preserved:
    - Greek letters (used in coin legends)
    - Bullets (•) used as separators in legends
    - Æ ligature (used in denomination names like Æ25)
    - Degree sign (°)
    - Other meaningful Unicode
    """
    if text is None:
        return None
    
    s = str(text)
    
    # Convert various space characters to regular space
    s = s.replace('\u00a0', ' ')  # Non-breaking space
    s = s.replace('\u202f', ' ')  # Narrow no-break space
    s = s.replace('\u2009', ' ')  # Thin space
    s = s.replace('\u200a', ' ')  # Hair space
    
    # Convert special dashes to hyphen-minus
    s = s.replace('\u2013', '-')  # En dash
    s = s.replace('\u2014', '-')  # Em dash
    s = s.replace('\u2212', '-')  # Minus sign
    
    # Normalize quotes
    s = s.replace('\u201c', '"')  # Left double quote
    s = s.replace('\u201d', '"')  # Right double quote
    s = s.replace('\u2018', "'")  # Left single quote
    s = s.replace('\u2019', "'")  # Right single quote
    s = s.replace('\u00ab', '"')  # Left guillemet
    s = s.replace('\u00bb', '"')  # Right guillemet
    
    # Collapse multiple spaces to single
    s = re.sub(r' +', ' ', s)
    
    # Strip leading/trailing whitespace
    s = s.strip()
    
    return s if s else None


class ImportError(Exception):
    """Import error."""
    pass


def detect_file_type(file_path: Path) -> str:
    """Detect if file is CSV or Excel."""
    suffix = file_path.suffix.lower()
    if suffix in [".xlsx", ".xls"]:
        return "excel"
    elif suffix == ".csv":
        return "csv"
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def read_excel_file(file_path: Path) -> List[Dict[str, Any]]:
    """Read Excel file and return list of dictionaries with normalized text."""
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active
    
    # Read headers from first row
    headers = []
    for cell in sheet[1]:
        headers.append(normalize_text(cell.value) or "")
    
    # Read data rows
    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if any(cell is not None for cell in row):  # Skip empty rows
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    # Normalize string values, keep numbers/dates as-is
                    if isinstance(value, str):
                        row_dict[headers[i]] = normalize_text(value)
                    else:
                        row_dict[headers[i]] = value
            rows.append(row_dict)
    
    return rows


def read_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Read CSV file and return list of dictionaries with normalized text."""
    rows = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize all text values
            normalized_row = {
                normalize_text(k) or k: normalize_text(v) 
                for k, v in row.items()
            }
            rows.append(normalized_row)
    return rows


def parse_date(date_value: Any) -> Optional[datetime]:
    """Parse date from various formats."""
    if not date_value:
        return None
    
    if isinstance(date_value, datetime):
        return date_value.date()
    
    if isinstance(date_value, str):
        # Try common date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(date_value.strip(), fmt).date()
            except ValueError:
                continue
    
    return None


def parse_reign_years(reign_str: str) -> tuple[Optional[int], Optional[int]]:
    """Parse reign years from string like '27 BC-AD 14', 'AD 14-37', '96 BC', 'AD 75', or 'AD 140/141'."""
    if not reign_str:
        return None, None
    
    reign_str = str(reign_str).strip().upper()
    
    # Pattern 1: "27 BC-AD 14" or "2 BC-AD 4"
    bc_ad_match = re.search(r"(\d+)\s*BC\s*[-–]\s*AD\s*(\d+)", reign_str, re.IGNORECASE)
    if bc_ad_match:
        start = -int(bc_ad_match.group(1))  # BC is negative
        end = int(bc_ad_match.group(2))      # AD is positive
        return start, end
    
    # Pattern 2: "AD 14-37" or "AD 14 - 37" or "AD 140/141" (range with hyphen, en-dash, or slash)
    ad_range_match = re.search(r"AD\s*(\d+)\s*[-–/]\s*(\d+)", reign_str, re.IGNORECASE)
    if ad_range_match:
        start = int(ad_range_match.group(1))
        end_str = ad_range_match.group(2)
        end = int(end_str)
        
        # Handle abbreviated end years like "159-60" meaning 159-160
        if len(end_str) < len(str(start)):
            # Abbreviated: take prefix from start year
            prefix = str(start)[:-len(end_str)]
            end = int(prefix + end_str)
        
        return start, end
    
    # Pattern 3: "96 BC" or "54 BC" (single BC year)
    single_bc_match = re.search(r"(\d+)\s*BC", reign_str, re.IGNORECASE)
    if single_bc_match:
        year = -int(single_bc_match.group(1))  # BC is negative
        return year, year
    
    # Pattern 4: "AD 75" (single AD year)
    single_ad_match = re.search(r"AD\s*(\d+)", reign_str, re.IGNORECASE)
    if single_ad_match:
        year = int(single_ad_match.group(1))
        return year, year
    
    # Pattern 5: Plain range "14-37" or "140/141" (assume AD)
    plain_range_match = re.search(r"(\d+)\s*[-–/]\s*(\d+)", reign_str)
    if plain_range_match:
        start = int(plain_range_match.group(1))
        end_str = plain_range_match.group(2)
        end = int(end_str)
        
        # Handle abbreviated end years
        if len(end_str) < len(str(start)):
            prefix = str(start)[:-len(end_str)]
            end = int(prefix + end_str)
        
        return start, end
    
    # Pattern 6: Single year without BC/AD (assume AD)
    single_year_match = re.search(r"(\d+)", reign_str)
    if single_year_match:
        year = int(single_year_match.group(1))
        return year, year
    
    return None, None


def parse_references(ref_str: str) -> List[Dict[str, str]]:
    """Parse reference string like 'RIC I 207' or 'Crawford 335/1c'.
    
    Handles multiple references separated by semicolons, commas, periods, or newlines.
    Supports: RIC, RPC, Crawford, RSC, SEAR, BMC, BMCRE, Sydenham, Cohen, Prieur.
    """
    if not ref_str:
        return []
    
    ref_str = str(ref_str).strip()
    references = []
    
    # Split by common separators (semicolon, newline, or period followed by space and capital)
    # The capital letter requirement prevents splitting "Coh. 84" incorrectly
    parts = re.split(r"[;\n]|\.\s+(?=[A-Z])", ref_str)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Further split by comma (but not within patterns)
        # Handle "RIC 129, Sear 8677" -> two refs
        subparts = [p.strip() for p in part.split(",") if p.strip()]
        
        for subpart in subparts:
            if not subpart:
                continue
            
            parsed = False
            
            # RIC modern notation: "RIC II.1 756", "RIC IV.2#252d", "RIC V.II 118"
            # Volume with Arabic numerals and dots/hashes
            ric_modern_match = re.match(
                r"RIC\s+([IVX]+\.[\dIVX]+)\s*#?\s*(\d+[a-z]?)",
                subpart, re.IGNORECASE
            )
            if ric_modern_match:
                volume = ric_modern_match.group(1)
                number = ric_modern_match.group(2)
                references.append({
                    "system": "ric",
                    "volume": volume,
                    "number": number,
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # RIC with mint: "RIC VI Cyzicus 36", "RIC VI Heraclea 73"
            ric_mint_match = re.match(
                r"RIC\s+([IVX]+)\s+([A-Za-z]+)\s+(\d+[a-z]?)",
                subpart, re.IGNORECASE
            )
            if ric_mint_match:
                volume = ric_mint_match.group(1)
                mint = ric_mint_match.group(2)
                number = ric_mint_match.group(3)
                references.append({
                    "system": "ric",
                    "volume": f"{volume} {mint}",
                    "number": number,
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # RIC standard: "RIC I 207", "RIC 127", "RIC I, 207", "RIC 177a", "RIC IViii 177a"
            # Volume can be Roman numerals, optionally with lowercase suffix like "IViii"
            ric_match = re.match(
                r"RIC\s+([IVX]+[a-z]*)?\s*,?\s*(\d+[a-z]?(?:/\d+[a-z]?)?)",
                subpart, re.IGNORECASE
            )
            if ric_match:
                volume = ric_match.group(1) or ""
                number = ric_match.group(2)
                references.append({
                    "system": "ric",
                    "volume": volume,
                    "number": number,
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # RPC pattern: "RPC I 1701a", "RPC 1234", "RPC V.3 1234"
            rpc_match = re.match(
                r"RPC\s+([IVX]+(?:\.\d+)?)\s*,?\s*(\d+[a-z]?)",
                subpart, re.IGNORECASE
            )
            if rpc_match:
                references.append({
                    "system": "rpc",
                    "volume": rpc_match.group(1),
                    "number": rpc_match.group(2),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # RPC without volume: "RPC 1234"
            rpc_simple_match = re.match(r"RPC\s+(\d+[a-z]?)", subpart, re.IGNORECASE)
            if rpc_simple_match:
                references.append({
                    "system": "rpc",
                    "number": rpc_simple_match.group(1),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # Crawford pattern: "Crawford 335/1c"
            crawford_match = re.match(
                r"Crawford\s+(\d+(?:/\d+[a-z]?)?)",
                subpart, re.IGNORECASE
            )
            if crawford_match:
                references.append({
                    "system": "crawford",
                    "number": crawford_match.group(1),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # RSC pattern: "RSC 966"
            rsc_match = re.match(r"RSC\s+(\d+[a-z]?)", subpart, re.IGNORECASE)
            if rsc_match:
                references.append({
                    "system": "rsc",
                    "number": rsc_match.group(1),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # Sear pattern: "Sear 8677", "SEAR II 5722", "Sear5 11344"
            sear_match = re.match(
                r"SEAR\d?\s+([IVX]+\s+)?(\d+)",
                subpart, re.IGNORECASE
            )
            if sear_match:
                volume = (sear_match.group(1) or "").strip()
                references.append({
                    "system": "sear",
                    "volume": volume,
                    "number": sear_match.group(2),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # BMC/BMCRE pattern: "BMC 837", "BMCRE 227"
            bmc_match = re.match(r"(BMC(?:RE)?)\s+(\d+)", subpart, re.IGNORECASE)
            if bmc_match:
                references.append({
                    "system": bmc_match.group(1).lower(),
                    "number": bmc_match.group(2),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # Cohen pattern: "Cohen 161", "Cohen 17", "Coh. 84", "C 161"
            cohen_match = re.match(r"(?:Cohen|Coh\.?|C)\s+(\d+)", subpart, re.IGNORECASE)
            if cohen_match:
                references.append({
                    "system": "cohen",
                    "number": cohen_match.group(1),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # Sydenham pattern: "Sydenham 611"
            sydenham_match = re.match(r"Sydenham\s+(\d+[a-z]?)", subpart, re.IGNORECASE)
            if sydenham_match:
                references.append({
                    "system": "sydenham",
                    "number": sydenham_match.group(1),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # Prieur pattern: "Prieur 1165"
            prieur_match = re.match(r"Prieur\s+(\d+)", subpart, re.IGNORECASE)
            if prieur_match:
                references.append({
                    "system": "prieur",
                    "number": prieur_match.group(1),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # SNG pattern: "SNG Cop 281-282"
            sng_match = re.match(r"SNG\s+(\w+)\s+(\d+(?:-\d+)?)", subpart, re.IGNORECASE)
            if sng_match:
                references.append({
                    "system": "sng",
                    "volume": sng_match.group(1),
                    "number": sng_match.group(2),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # RIC with hyphen: "RIC II.3-1514", "RIC III-12"
            ric_hyphen_match = re.match(
                r"RIC\s+([IVX]+\.?\d*)-(\d+[a-z]?)",
                subpart, re.IGNORECASE
            )
            if ric_hyphen_match:
                references.append({
                    "system": "ric",
                    "volume": ric_hyphen_match.group(1),
                    "number": ric_hyphen_match.group(2),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # RIC with parens: "RIC III (Marcus Aurelius) 430", "RIC IV.III (Trajan Decius) 58b"
            ric_parens_match = re.match(
                r"RIC\s+([IVX]+(?:\.[IVX\d]+)?)\s*\([^)]+\)\s*(\d+[a-z]?)",
                subpart, re.IGNORECASE
            )
            if ric_parens_match:
                references.append({
                    "system": "ric",
                    "volume": ric_parens_match.group(1),
                    "number": ric_parens_match.group(2),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # RIC Part pattern: recombine "RIC IV" + "Part III" + "27b"
            # This handles comma-separated patterns like "RIC IV, Part III, 27b"
            if subpart.upper().startswith("PART "):
                # Skip "Part X" fragments - they should be handled with the previous RIC
                continue
            
            # BMCRE/RSC with hyphen: "BMCRE-842", "RSC-804"
            hyphen_ref_match = re.match(
                r"(BMCRE?|RSC)-(\d+[a-z]?)",
                subpart, re.IGNORECASE
            )
            if hyphen_ref_match:
                references.append({
                    "system": hyphen_ref_match.group(1).lower(),
                    "number": hyphen_ref_match.group(2),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # MIR pattern: "MIR 18"
            mir_match = re.match(r"MIR\s+(\d+)", subpart, re.IGNORECASE)
            if mir_match:
                references.append({
                    "system": "mir",
                    "number": mir_match.group(1),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # SRCV pattern: "SRCV 11967" (Sear Roman Coins and their Values)
            srcv_match = re.match(r"SRCV\s+(\d+)", subpart, re.IGNORECASE)
            if srcv_match:
                references.append({
                    "system": "sear",
                    "number": srcv_match.group(1),
                    "is_primary": len(references) == 0,
                })
                parsed = True
                continue
            
            # Default: treat as other (only if meaningful content)
            if not parsed and len(subpart) > 2:
                references.append({
                    "system": "other",
                    "number": subpart,
                    "is_primary": len(references) == 0,
                })
    
    return references


# Column mapping from Excel to Coin model
COLUMN_MAPPING = {
    "Ruler Issuer": "issuing_authority",
    "Coin type": "denomination",
    "Category": "category",
    "Composition": "metal",  # Will parse "Silver", "Gold", etc.
    "Temp loc": "storage_location",
    "Reference": "references",
    "Amount Paid": "acquisition_price",
    "Weight": "weight_g",
    "Diameter": "diameter_mm",
    "Condition": "grade",  # Primary grade
    "NGC Grade": "ngc_grade",  # More detailed grade
    "Mint": "mint_name",
    "Ruled": "reign",  # Parse reign years
    "Minted": "minted",  # Parse mint years
    "Obverse": "obverse_full",  # Will split into legend/description
    "Reverse": "reverse_full",  # Will split into legend/description
    "Source": "acquisition_source",
    "Link": "acquisition_url",
    "Comment": "personal_notes",
    "NGC comment": "surface_issues",
    "Pedigree": "provenance_notes",
    "Fine style": "style_notes",
    "Script": "script",
    "Laureate": "portrait_subject",
}


def normalize_category(category: str) -> Optional[str]:
    """Normalize category string to enum value."""
    if not category:
        return None
    
    category_lower = str(category).lower()
    if "imperial" in category_lower:
        return "imperial"
    elif "republic" in category_lower:
        return "republic"
    elif "provincial" in category_lower:
        return "provincial"
    elif "byzantine" in category_lower:
        return "byzantine"
    elif "greek" in category_lower:
        return "greek"
    elif "celtic" in category_lower:
        return "celtic"
    elif "judaean" in category_lower or "jewish" in category_lower:
        return "judaean"
    elif "migration" in category_lower:
        return "migration"
    elif "pseudo" in category_lower or "imitation" in category_lower:
        return "pseudo_roman"
    return "other"


def normalize_metal(metal: str) -> Optional[str]:
    """Normalize metal string to enum value."""
    if not metal:
        return None
    
    metal_lower = str(metal).lower()
    if "gold" in metal_lower and "electrum" not in metal_lower:
        return "gold"
    elif "electrum" in metal_lower:
        return "electrum"
    elif "silver" in metal_lower:
        return "silver"
    elif "bronze" in metal_lower:
        return "bronze"
    elif "billon" in metal_lower:
        return "billon"
    elif "potin" in metal_lower:
        return "potin"
    elif "orichalcum" in metal_lower or "brass" in metal_lower:
        return "orichalcum"
    elif "copper" in metal_lower:
        return "copper"
    elif "lead" in metal_lower:
        return "lead"
    elif "ae" in metal_lower:
        return "ae"
    return "uncertain"


def parse_obverse_reverse(full_text: str) -> tuple[Optional[str], Optional[str]]:
    """Parse obverse/reverse text into legend and description.
    
    Looks for pattern: "LEGEND, description" or just "description"
    """
    if not full_text:
        return None, None
    
    full_text = str(full_text).strip()
    
    # Try to split on comma - first part might be legend
    if "," in full_text:
        parts = full_text.split(",", 1)
        legend = parts[0].strip()
        description = parts[1].strip()
        
        # If legend looks like a legend (all caps, abbreviations), use it
        if len(legend) < 50 and legend.isupper():
            return legend, description
        else:
            # Otherwise, it's all description
            return None, full_text
    
    return None, full_text


def parse_mint_years(minted_str: str) -> tuple[Optional[int], Optional[int]]:
    """Parse mint years from string like '2 BC-AD 4' or '96 BC'."""
    if not minted_str:
        return None, None
    
    return parse_reign_years(minted_str)  # Same logic


def parse_ngc_grade(ngc_grade: str) -> dict:
    """Parse NGC grade string like 'Choice AU  Strike: 5/5 Surface: 4/5'."""
    if not ngc_grade:
        return {}
    
    result = {}
    ngc_str = str(ngc_grade).strip()
    
    # Extract grade (first part before "Strike:")
    if "Strike:" in ngc_str:
        grade_part = ngc_str.split("Strike:")[0].strip()
        result["grade"] = grade_part
    else:
        result["grade"] = ngc_str
    
    # Extract strike quality
    strike_match = re.search(r"Strike:\s*(\d)/5", ngc_str)
    if strike_match:
        result["strike_quality"] = int(strike_match.group(1))
    
    # Extract surface quality
    surface_match = re.search(r"Surface:\s*(\d)/5", ngc_str)
    if surface_match:
        result["surface_quality"] = int(surface_match.group(1))
    
    return result


def map_row_to_coin_data(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map Excel/CSV row to CoinCreate schema."""
    coin_data = {}
    
    for excel_col, model_field in COLUMN_MAPPING.items():
        if excel_col in row and row[excel_col] is not None:
            value = row[excel_col]
            
            # Skip empty values
            if value == "" or value is None:
                continue
            
            # Handle type conversions
            if model_field == "acquisition_price":
                try:
                    coin_data[model_field] = float(value) if value else None
                except (ValueError, TypeError):
                    pass
            elif model_field == "weight_g":
                try:
                    coin_data[model_field] = float(value) if value else None
                except (ValueError, TypeError):
                    pass
            elif model_field == "diameter_mm":
                try:
                    coin_data[model_field] = float(value) if value else None
                except (ValueError, TypeError):
                    pass
            elif model_field == "acquisition_date":
                coin_data[model_field] = parse_date(value)
            elif model_field == "references":
                coin_data[model_field] = parse_references(value)
            elif model_field == "category":
                coin_data[model_field] = normalize_category(value)
            elif model_field == "metal":
                coin_data[model_field] = normalize_metal(value)
            elif model_field == "reign":
                start, end = parse_reign_years(value)
                if start is not None:
                    coin_data["reign_start"] = start
                if end is not None:
                    coin_data["reign_end"] = end
            elif model_field == "minted":
                start, end = parse_mint_years(value)
                if start is not None:
                    coin_data["mint_year_start"] = start
                if end is not None:
                    coin_data["mint_year_end"] = end
            elif model_field == "obverse_full":
                legend, description = parse_obverse_reverse(value)
                if legend:
                    coin_data["obverse_legend"] = legend
                if description:
                    coin_data["obverse_description"] = description
            elif model_field == "reverse_full":
                legend, description = parse_obverse_reverse(value)
                if legend:
                    coin_data["reverse_legend"] = legend
                if description:
                    coin_data["reverse_description"] = description
            elif model_field == "ngc_grade":
                ngc_data = parse_ngc_grade(value)
                coin_data.update(ngc_data)
            elif model_field == "surface_issues":
                # Store as list or JSON string
                if value:
                    coin_data[model_field] = [str(value).strip()]
            else:
                coin_data[model_field] = str(value).strip() if value else None
    
    return coin_data


def get_or_create_mint(db: Session, mint_name: str) -> Optional[Mint]:
    """Get or create mint."""
    if not mint_name:
        return None
    
    mint = db.query(Mint).filter(Mint.name == mint_name).first()
    if not mint:
        mint = Mint(name=mint_name)
        db.add(mint)
        db.flush()
    
    return mint


def normalize_reference_string(system: str, volume: str, number: str) -> str:
    """Create normalized reference string for uniqueness check."""
    parts = [system.lower()]
    if volume:
        parts.append(volume.lower())
    if number:
        parts.append(number.lower())
    return ".".join(parts)


def format_local_ref(system: str, volume: str, number: str) -> str:
    """Format a human-readable local reference."""
    system_upper = system.upper()
    if system_upper == "RIC":
        return f"RIC {volume} {number}" if volume else f"RIC {number}"
    elif system_upper == "CRAWFORD":
        return f"Crawford {number}"
    elif system_upper == "RPC":
        return f"RPC {number}"
    elif system_upper == "RSC":
        return f"RSC {number}"
    elif system_upper == "SEAR":
        return f"Sear {number}"
    else:
        return f"{system_upper} {number}"


def get_or_create_reference_type(
    db: Session, 
    system: str, 
    volume: Optional[str], 
    number: str
) -> ReferenceType:
    """Get or create a ReferenceType record."""
    normalized = normalize_reference_string(system, volume or "", number)
    
    # Check if exists
    ref_type = db.query(ReferenceType).filter(
        ReferenceType.local_ref_normalized == normalized
    ).first()
    
    if not ref_type:
        local_ref = format_local_ref(system, volume or "", number)
        ref_type = ReferenceType(
            system=system.lower(),
            local_ref=local_ref,
            local_ref_normalized=normalized,
            volume=volume,
            number=number,
            lookup_status="pending",
        )
        db.add(ref_type)
        db.flush()
    
    return ref_type


class ImportResult:
    """Import result."""
    
    def __init__(self):
        self.imported = 0
        self.updated = 0
        self.skipped = 0
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "imported": self.imported,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
            "warnings": self.warnings,
        }


async def import_collection_file(
    db: Session,
    file_path: Path,
    dry_run: bool = False,
) -> ImportResult:
    """Import collection from CSV or Excel file with robust parsing."""
    result = ImportResult()
    
    try:
        file_type = detect_file_type(file_path)
        
        if file_type == "excel":
            rows = read_excel_file(file_path)
        else:
            rows = read_csv_file(file_path)
        
        logger.info(f"Found {len(rows)} rows in {file_path.name}")
        
        for idx, row in enumerate(rows, start=2):  # Start at 2 (row 1 is header)
            try:
                coin_data = map_row_to_coin_data(row)
                
                # Validate required fields
                if not coin_data.get("issuing_authority") or not coin_data.get("denomination"):
                    result.skipped += 1
                    result.warnings.append(f"Row {idx}: Missing required fields")
                    continue
                
                if not coin_data.get("category"):
                    coin_data["category"] = "imperial"  # Default
                
                if not coin_data.get("metal"):
                    result.skipped += 1
                    result.warnings.append(f"Row {idx}: Missing metal")
                    continue
                
                # Convert to enums
                try:
                    coin_data["category"] = Category(coin_data["category"])
                except ValueError:
                    coin_data["category"] = Category.IMPERIAL
                
                try:
                    coin_data["metal"] = Metal(coin_data["metal"])
                except ValueError:
                    result.skipped += 1
                    result.warnings.append(f"Row {idx}: Invalid metal '{coin_data.get('metal')}'")
                    continue
                
                # Handle mint
                mint = None
                if "mint_name" in coin_data:
                    mint = get_or_create_mint(db, coin_data.pop("mint_name"))
                
                # Handle references
                references_data = coin_data.pop("references", [])
                
                if not dry_run:
                    # Create coin
                    coin = Coin(**coin_data)
                    if mint:
                        coin.mint = mint
                    
                    db.add(coin)
                    db.flush()
                    
                    # Add references (type-only approach)
                    for ref_data in references_data:
                        try:
                            # Get or create the ReferenceType
                            ref_type = get_or_create_reference_type(
                                db,
                                system=ref_data["system"],
                                volume=ref_data.get("volume"),
                                number=ref_data["number"],
                            )
                            
                            # Create CoinReference linking to ReferenceType
                            ref = CoinReference(
                                coin_id=coin.id,
                                reference_type_id=ref_type.id,
                                is_primary=ref_data.get("is_primary", False),
                            )
                            db.add(ref)
                        except Exception as e:
                            logger.warning(f"Error creating reference '{ref_data}': {e}")
                    
                    db.commit()
                    result.imported += 1
                else:
                    result.imported += 1
                    result.warnings.append(f"Row {idx}: Dry run - not imported")
            
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error importing row {idx}: {error_msg}", exc_info=True)
                result.errors.append({
                    "row": idx,
                    "error": error_msg,
                    "data": str(row.get("Ruler Issuer", "Unknown")),
                })
                result.skipped += 1
        
        if not dry_run:
            db.commit()
        
        logger.info(f"Import complete: {result.imported} imported, {result.skipped} skipped")
        
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        result.errors.append({
            "row": 0,
            "error": str(e),
        })
        if not dry_run:
            db.rollback()
    
    return result
