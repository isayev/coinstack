"""Base catalog service interface and result schema."""
from abc import ABC, abstractmethod
from typing import Literal, Any, List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone


class CatalogCandidate(BaseModel):
    """A candidate match from catalog reconciliation."""
    external_id: str
    external_url: Optional[str] = None
    score: float  # 0-100 from API
    confidence: float  # Normalized 0-1
    name: Optional[str] = None
    description: Optional[str] = None
    match_type: Optional[str] = None  # "exact", "partial", "fuzzy"


class CatalogResult(BaseModel):
    """Result from catalog lookup."""
    
    # Match status
    status: Literal["success", "not_found", "ambiguous", "deferred", "error"]
    
    # Best match (if status is "success")
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    confidence: float = 0.0  # 0-1 from reconciliation
    
    # For ambiguous results - multiple candidates
    candidates: Optional[List[CatalogCandidate]] = None
    
    # Parsed type data (from JSON-LD)
    payload: Optional[Dict[str, Any]] = None
    
    # Raw response for debugging
    raw: Optional[Dict[str, Any]] = None
    
    # Error information
    error_message: Optional[str] = None
    
    # Metadata
    source_version: Optional[str] = None
    lookup_timestamp: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CatalogPayload(BaseModel):
    """Standardized payload extracted from catalog JSON-LD."""
    
    # Authority / Ruler
    authority: Optional[str] = None
    authority_uri: Optional[str] = None
    
    # Denomination
    denomination: Optional[str] = None
    denomination_uri: Optional[str] = None
    
    # Mint
    mint: Optional[str] = None
    mint_uri: Optional[str] = None
    
    # Dating
    date_from: Optional[int] = None
    date_to: Optional[int] = None
    date_string: Optional[str] = None
    
    # Design - Obverse
    obverse_description: Optional[str] = None
    obverse_legend: Optional[str] = None
    obverse_portrait: Optional[str] = None
    
    # Design - Reverse
    reverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_type: Optional[str] = None
    
    # Physical
    material: Optional[str] = None
    material_uri: Optional[str] = None
    
    # Catalog-specific
    type_series: Optional[str] = None
    subtypes: Optional[List[str]] = None
    related_types: Optional[List[str]] = None
    
    # Bibliography
    bibliography: Optional[List[Dict]] = None


class CatalogService(ABC):
    """
    Abstract base class for catalog services.
    
    Each catalog (OCRE, CRRO, RPC) implements this interface.
    """
    
    # Configuration
    CACHE_TTL_DAYS: int = 180  # 6 months default
    BASE_URL: str = ""
    SYSTEM: str = ""  # "ric", "crawford", "rpc"
    
    @abstractmethod
    def normalize_reference(self, raw: str) -> Optional[str]:
        """
        Convert raw reference string to normalized form.
        
        Examples:
            "RIC I 207" -> "ric.1.207"
            "Crawford 335/1c" -> "crawford.335.1c"
        
        Returns None if the reference doesn't match this system.
        """
        pass
    
    @abstractmethod
    def parse_reference(self, raw: str) -> Optional[Dict]:
        """
        Parse reference string into structured components.
        
        Returns dict with keys like:
            - system: "ric"
            - volume: "1"
            - number: "207"
            - subtype: "a" (optional)
        
        Returns None if parsing fails.
        """
        pass
    
    @abstractmethod
    async def build_reconcile_query(
        self, 
        ref: str, 
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Build OpenRefine reconciliation query.
        
        Args:
            ref: Reference string or normalized form
            context: Optional coin context (ruler, mint, denomination)
        
        Returns dict suitable for POST to reconciliation API.
        """
        pass
    
    @abstractmethod
    async def reconcile(self, query: Dict) -> CatalogResult:
        """
        Hit reconciliation API and return result.
        
        This should handle:
        - HTTP errors
        - Rate limiting
        - Multiple candidates (ambiguous)
        - No matches (not_found)
        """
        pass
    
    @abstractmethod
    async def fetch_type_data(self, external_id: str) -> Optional[Dict]:
        """
        Fetch full JSON-LD for a matched type.
        
        Args:
            external_id: The OCRE/CRRO ID like "ric.1(2).aug.207"
        
        Returns raw JSON-LD dict or None if fetch fails.
        """
        pass
    
    @abstractmethod
    def parse_payload(self, jsonld: Dict) -> CatalogPayload:
        """
        Extract structured fields from JSON-LD into CatalogPayload.
        
        This normalizes the catalog-specific JSON-LD structure
        into our standard CatalogPayload format.
        """
        pass
    
    @abstractmethod
    def build_url(self, external_id: str) -> str:
        """
        Generate human-readable catalog URL.
        
        Args:
            external_id: The catalog ID
        
        Returns full URL like "http://numismatics.org/ocre/id/ric.1.207"
        """
        pass
    
    def is_cache_fresh(self, last_lookup: Optional[datetime]) -> bool:
        """Check if cached data is still fresh."""
        if not last_lookup:
            return False
        if last_lookup.tzinfo is None:
             last_lookup = last_lookup.replace(tzinfo=timezone.utc)
        ttl = timedelta(days=self.CACHE_TTL_DAYS)
        return datetime.now(timezone.utc) - last_lookup < ttl
    
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
    
    def _arabic_to_roman(self, num: int) -> str:
        """Convert Arabic number to Roman numeral."""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        result = ''
        for i, v in enumerate(val):
            while num >= v:
                result += syms[i]
                num -= v
        return result
