"""
Reign Validation Strategy

Validates that a coin's mint date falls within the issuing authority's reign period.
This catches historical inconsistencies like:
- A coin dated 75 AD attributed to Augustus (died 14 AD)
- A coin dated 200 BC attributed to Trajan (reigned 98-117 AD)

Posthumous issues are flagged with lower confidence as they may be legitimate.
"""

from typing import List, Dict, Tuple, Optional
from src.domain.coin import Coin
from src.domain.audit import IAuditStrategy, ExternalAuctionData, Discrepancy


# Import rulers data - fallback to empty dict if not available
try:
    from backend.v1_archive.app.data.rulers import RULERS
except ImportError:
    try:
        from v1_archive.app.data.rulers import RULERS
    except ImportError:
        # Inline minimal ruler data as fallback
        RULERS: Dict[str, Tuple[int, int]] = {}


class ReignValidationStrategy(IAuditStrategy):
    """
    Validates mint dates against issuer's reign period.
    
    This strategy checks whether the coin's attributed mint date
    falls within the historical reign of the issuing authority.
    
    Discrepancy types:
    - BEFORE_REIGN: Coin dated before issuer's reign started
    - AFTER_REIGN: Coin dated after issuer's reign ended (may be posthumous)
    """
    
    def __init__(self, rulers_data: Optional[Dict[str, Tuple[int, int]]] = None):
        """
        Initialize with rulers data.
        
        Args:
            rulers_data: Dict mapping ruler names to (reign_start, reign_end) tuples.
                        Years are integers (negative for BC).
                        If None, uses the RULERS constant from v1_archive.
        """
        self.rulers = rulers_data if rulers_data is not None else RULERS
    
    def audit(self, coin: Coin, auction_data: ExternalAuctionData) -> List[Discrepancy]:
        """
        Validate coin's mint date against issuer's reign.
        
        Args:
            coin: The coin being audited
            auction_data: External auction data (not used by this strategy,
                         but required by IAuditStrategy protocol)
        
        Returns:
            List of Discrepancy objects for date/reign mismatches
        """
        discrepancies = []
        
        issuer = coin.attribution.issuer
        if not issuer:
            return discrepancies
        
        # Look up reign dates
        reign_dates = self._get_reign_dates(issuer)
        if not reign_dates:
            return discrepancies
        
        reign_start, reign_end = reign_dates
        
        # Check start year
        if coin.attribution.year_start is not None:
            year = coin.attribution.year_start
            
            if year < reign_start:
                # Coin dated before reign - definite error
                discrepancies.append(Discrepancy(
                    field="year_start",
                    current_value=self._format_year(year),
                    auction_value=f"Reign begins {self._format_year(reign_start)}",
                    confidence=0.95,  # High confidence - historical fact
                    source="Historical Reference"
                ))
            
            elif year > reign_end:
                # Coin dated after reign - could be posthumous
                # Lower confidence as posthumous issues are valid
                discrepancies.append(Discrepancy(
                    field="year_start",
                    current_value=self._format_year(year),
                    auction_value=f"Reign ends {self._format_year(reign_end)} (posthumous?)",
                    confidence=0.6,  # Lower confidence - posthumous possible
                    source="Historical Reference"
                ))
        
        # Check end year if different from start
        if (coin.attribution.year_end is not None and 
            coin.attribution.year_end != coin.attribution.year_start):
            year = coin.attribution.year_end
            
            if year < reign_start:
                discrepancies.append(Discrepancy(
                    field="year_end",
                    current_value=self._format_year(year),
                    auction_value=f"Reign begins {self._format_year(reign_start)}",
                    confidence=0.95,
                    source="Historical Reference"
                ))
        
        return discrepancies
    
    def _get_reign_dates(self, issuer: str) -> Optional[Tuple[int, int]]:
        """
        Look up reign dates for an issuer.
        
        Tries exact match first, then case-insensitive, then partial match.
        
        Args:
            issuer: Name of the issuing authority
            
        Returns:
            (reign_start, reign_end) tuple or None if not found
        """
        # Exact match
        if issuer in self.rulers:
            return self.rulers[issuer]
        
        # Case-insensitive match
        issuer_lower = issuer.lower()
        for name, dates in self.rulers.items():
            if name.lower() == issuer_lower:
                return dates
        
        # Partial match (issuer contains or is contained in ruler name)
        for name, dates in self.rulers.items():
            if name.lower() in issuer_lower or issuer_lower in name.lower():
                return dates
        
        return None
    
    def _format_year(self, year: int) -> str:
        """Format year with BC/AD suffix."""
        if year < 0:
            return f"{abs(year)} BC"
        else:
            return f"AD {year}"
    
    def validate_single(self, issuer: str, year: int) -> Optional[str]:
        """
        Convenience method to validate a single issuer/year combination.
        
        Args:
            issuer: Name of the issuing authority
            year: Mint year (negative for BC)
            
        Returns:
            Error message string if invalid, None if valid
        """
        reign_dates = self._get_reign_dates(issuer)
        if not reign_dates:
            return None  # Can't validate - no data
        
        reign_start, reign_end = reign_dates
        
        if year < reign_start:
            return f"Year {self._format_year(year)} is before {issuer}'s reign ({self._format_year(reign_start)})"
        
        if year > reign_end:
            return f"Year {self._format_year(year)} is after {issuer}'s reign ended ({self._format_year(reign_end)}) - possibly posthumous"
        
        return None  # Valid


# Factory function for easy instantiation
def create_reign_strategy() -> ReignValidationStrategy:
    """Create a ReignValidationStrategy with default rulers data."""
    return ReignValidationStrategy(RULERS if RULERS else None)
