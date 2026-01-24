"""Rule-based reference parser for coin catalog references."""
import re
from typing import Literal
from pydantic import BaseModel


class ParseResult(BaseModel):
    """Result of parsing a reference string."""
    
    # Core fields
    system: str | None = None           # "ric", "crawford", "rpc", etc.
    volume: str | None = None           # Volume number/numeral
    number: str | None = None           # Main reference number
    subtype: str | None = None          # Variant/subtype like "a", "b"
    
    # Parsing metadata
    raw: str                            # Original input string
    normalized: str | None = None       # Normalized form like "ric.1.207"
    confidence: float = 0.0             # 0-1, how confident we are in the parse
    needs_llm: bool = False             # True if LLM disambiguation needed
    
    # Additional parsed components
    edition: str | None = None          # RIC edition number (2, 3)
    main_number: str | None = None      # For Crawford: main Crawford number
    sub_number: str | None = None       # For Crawford: sub-number after /
    
    # Reason for needing LLM (if applicable)
    llm_reason: str | None = None


class ReferenceParser:
    """
    Rule-based parser that handles 80% of references without LLM.
    
    Supports:
    - RIC (Roman Imperial Coinage)
    - Crawford (Roman Republican Coinage)
    - RPC (Roman Provincial Coins)
    - RSC (Roman Silver Coins)
    - BMCRE (British Museum Catalogue of Roman Empire)
    - Sear (Roman Coins and Their Values)
    """
    
    # Patterns organized by system
    PATTERNS = {
        "ric": [
            # RIC I 207, RIC II³ 430, RIC I² 207a
            (r"RIC\s+([IVX]+)([²³]|[23])?\s+(\d+)([a-z])?", "roman_volume"),
            # RIC 1 207, RIC 2.3 430
            (r"RIC\s+(\d+)(?:\.(\d))?\s+(\d+)([a-z])?", "arabic_volume"),
        ],
        "crawford": [
            # Crawford 335/1c, Cr. 335/1, RRC 335/1c
            (r"(?:Crawford|Cr\.?|RRC)\s*(\d+)/(\d+)([a-z])?", "standard"),
            # Just number format: 335/1c
            (r"^(\d+)/(\d+)([a-z])?$", "bare"),
        ],
        "rpc": [
            # RPC I 1234, RPC 1/5678
            (r"RPC\s+([IVX]+)[/\s]+(\d+)", "roman_volume"),
            # RPC 1 5678
            (r"RPC\s+(\d+)[/\s]+(\d+)", "arabic_volume"),
            # RPC 5678 (no volume)
            (r"RPC\s+(\d+)$", "no_volume"),
        ],
        "rsc": [
            # RSC 45, RSC II 123
            (r"RSC\s+(?:([IVX]+)\s+)?(\d+)([a-z])?", "standard"),
        ],
        "bmcre": [
            # BMCRE 123, BMC 456
            (r"(?:BMCRE|BMC)\s+(\d+)", "standard"),
        ],
        "sear": [
            # Sear 1234, S 5678, SCV 123
            (r"(?:Sear|SCV|S)\s+(\d+)", "standard"),
        ],
        "sydenham": [
            # Sydenham 123, Syd. 456
            (r"(?:Sydenham|Syd\.?)\s+(\d+)", "standard"),
        ],
    }
    
    def parse(self, raw: str) -> ParseResult:
        """
        Parse a reference string into structured components.
        
        Returns ParseResult with system, volume, number, etc.
        If parsing fails or is ambiguous, sets needs_llm=True.
        """
        if not raw or not raw.strip():
            return ParseResult(
                raw=raw or "",
                needs_llm=False,
                llm_reason="Empty reference"
            )
        
        raw = raw.strip()
        
        # Try each system's patterns
        for system, patterns in self.PATTERNS.items():
            for pattern, pattern_type in patterns:
                match = re.match(pattern, raw, re.IGNORECASE)
                if match:
                    return self._build_result(system, pattern_type, match, raw)
        
        # No pattern matched - might need LLM
        # Check if it looks like a reference at all
        if self._looks_like_reference(raw):
            return ParseResult(
                raw=raw,
                confidence=0.2,
                needs_llm=True,
                llm_reason="Unrecognized reference format - may need disambiguation"
            )
        
        # Doesn't look like a reference
        return ParseResult(
            raw=raw,
            confidence=0.0,
            needs_llm=False,
            llm_reason="Does not appear to be a catalog reference"
        )
    
    def _build_result(
        self, 
        system: str, 
        pattern_type: str, 
        match: re.Match,
        raw: str
    ) -> ParseResult:
        """Build ParseResult from regex match."""
        
        if system == "ric":
            return self._parse_ric(pattern_type, match, raw)
        elif system == "crawford":
            return self._parse_crawford(pattern_type, match, raw)
        elif system == "rpc":
            return self._parse_rpc(pattern_type, match, raw)
        elif system == "rsc":
            return self._parse_rsc(match, raw)
        elif system in ("bmcre", "sear", "sydenham"):
            return self._parse_simple(system, match, raw)
        
        return ParseResult(raw=raw, needs_llm=True)
    
    def _parse_ric(
        self, 
        pattern_type: str, 
        match: re.Match,
        raw: str
    ) -> ParseResult:
        """Parse RIC reference."""
        
        if pattern_type == "roman_volume":
            roman_vol = match.group(1).upper()
            edition_marker = match.group(2)
            number = match.group(3)
            subtype = match.group(4) if len(match.groups()) > 3 else None
            
            arabic_vol = self._roman_to_arabic(roman_vol)
            edition = None
            if edition_marker:
                edition = "2" if edition_marker in ["²", "2"] else "3"
            
            normalized = f"ric.{arabic_vol}"
            if edition:
                normalized += f"_{edition}"
            normalized += f".{number}"
            if subtype:
                normalized += subtype
            
            return ParseResult(
                system="ric",
                volume=str(arabic_vol),
                number=number,
                subtype=subtype,
                edition=edition,
                raw=raw,
                normalized=normalized.lower(),
                confidence=1.0,
                needs_llm=False
            )
        
        elif pattern_type == "arabic_volume":
            arabic_vol = match.group(1)
            edition = match.group(2)
            number = match.group(3)
            subtype = match.group(4) if len(match.groups()) > 3 else None
            
            normalized = f"ric.{arabic_vol}"
            if edition:
                normalized += f"_{edition}"
            normalized += f".{number}"
            if subtype:
                normalized += subtype
            
            return ParseResult(
                system="ric",
                volume=arabic_vol,
                number=number,
                subtype=subtype,
                edition=edition,
                raw=raw,
                normalized=normalized.lower(),
                confidence=1.0,
                needs_llm=False
            )
        
        return ParseResult(raw=raw, needs_llm=True)
    
    def _parse_crawford(
        self, 
        pattern_type: str, 
        match: re.Match,
        raw: str
    ) -> ParseResult:
        """Parse Crawford reference."""
        
        main_num = match.group(1)
        sub_num = match.group(2)
        variant = match.group(3) if len(match.groups()) > 2 else None
        
        full_number = f"{main_num}/{sub_num}"
        normalized = f"crawford.{main_num}.{sub_num}"
        if variant:
            normalized += variant
        
        # Bare format (335/1c without prefix) has lower confidence
        confidence = 0.9 if pattern_type == "bare" else 1.0
        
        return ParseResult(
            system="crawford",
            number=full_number,
            main_number=main_num,
            sub_number=sub_num,
            subtype=variant,
            raw=raw,
            normalized=normalized.lower(),
            confidence=confidence,
            needs_llm=pattern_type == "bare",  # Bare format might need confirmation
            llm_reason="Bare number format - confirm this is Crawford" if pattern_type == "bare" else None
        )
    
    def _parse_rpc(
        self, 
        pattern_type: str, 
        match: re.Match,
        raw: str
    ) -> ParseResult:
        """Parse RPC reference."""
        
        if pattern_type == "roman_volume":
            roman_vol = match.group(1).upper()
            number = match.group(2)
            arabic_vol = self._roman_to_arabic(roman_vol)
            
            return ParseResult(
                system="rpc",
                volume=str(arabic_vol),
                number=number,
                raw=raw,
                normalized=f"rpc.{arabic_vol}.{number}".lower(),
                confidence=1.0,
                needs_llm=False
            )
        
        elif pattern_type == "arabic_volume":
            arabic_vol = match.group(1)
            number = match.group(2)
            
            return ParseResult(
                system="rpc",
                volume=arabic_vol,
                number=number,
                raw=raw,
                normalized=f"rpc.{arabic_vol}.{number}".lower(),
                confidence=1.0,
                needs_llm=False
            )
        
        elif pattern_type == "no_volume":
            number = match.group(1)
            
            return ParseResult(
                system="rpc",
                volume=None,
                number=number,
                raw=raw,
                normalized=f"rpc.{number}".lower(),
                confidence=0.7,  # Lower confidence without volume
                needs_llm=True,
                llm_reason="RPC reference without volume - may need volume identification"
            )
        
        return ParseResult(raw=raw, needs_llm=True)
    
    def _parse_rsc(self, match: re.Match, raw: str) -> ParseResult:
        """Parse RSC (Roman Silver Coins) reference."""
        volume = match.group(1)
        number = match.group(2)
        subtype = match.group(3) if len(match.groups()) > 2 else None
        
        if volume:
            arabic_vol = self._roman_to_arabic(volume.upper())
            normalized = f"rsc.{arabic_vol}.{number}"
        else:
            normalized = f"rsc.{number}"
        
        if subtype:
            normalized += subtype
        
        return ParseResult(
            system="rsc",
            volume=str(self._roman_to_arabic(volume.upper())) if volume else None,
            number=number,
            subtype=subtype,
            raw=raw,
            normalized=normalized.lower(),
            confidence=1.0 if volume else 0.8,
            needs_llm=not volume,
            llm_reason="RSC reference without volume" if not volume else None
        )
    
    def _parse_simple(
        self, 
        system: str, 
        match: re.Match, 
        raw: str
    ) -> ParseResult:
        """Parse simple single-number references (BMCRE, Sear, Sydenham)."""
        number = match.group(1)
        
        return ParseResult(
            system=system,
            number=number,
            raw=raw,
            normalized=f"{system}.{number}".lower(),
            confidence=1.0,
            needs_llm=False
        )
    
    def _looks_like_reference(self, raw: str) -> bool:
        """Check if string looks like it could be a catalog reference."""
        # Contains numbers and common reference abbreviations
        has_numbers = bool(re.search(r"\d", raw))
        has_ref_words = bool(re.search(
            r"\b(RIC|RPC|Crawford|Cr|RSC|BMC|BMCRE|Sear|SCV|Sydenham|Syd)\b",
            raw, re.IGNORECASE
        ))
        return has_numbers and (has_ref_words or "/" in raw)
    
    def _roman_to_arabic(self, roman: str) -> int:
        """Convert Roman numeral to Arabic number."""
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        result = 0
        prev = 0
        for char in reversed(roman.upper()):
            curr = values.get(char, 0)
            if curr < prev:
                result -= curr
            else:
                result += curr
            prev = curr
        return result
    
    def parse_multiple(self, raw: str) -> list[ParseResult]:
        """
        Parse a string that may contain multiple references.
        
        Handles separators like "; ", ", ", " / ", newlines
        """
        if not raw:
            return []
        
        # Split by common separators
        parts = re.split(r"[;,\n]|\s+/\s+", raw)
        results = []
        
        for part in parts:
            part = part.strip()
            if part:
                result = self.parse(part)
                results.append(result)
        
        return results


# Singleton instance for convenience
parser = ReferenceParser()
