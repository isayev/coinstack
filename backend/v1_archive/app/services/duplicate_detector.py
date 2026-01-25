"""Duplicate detection service for import operations."""
import logging
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.coin import Coin
from app.models.import_record import ImportRecord
from app.schemas.import_preview import CoinSummary, MatchReason

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Detects potential duplicate coins before import.
    
    Checks for duplicates using:
    1. Exact match on source_id (Heritage lot, eBay item, NGC cert)
    2. Exact match on NGC certification_number
    3. Fuzzy match on physical characteristics + ruler
    """
    
    # Weight tolerance for fuzzy matching (percentage)
    WEIGHT_TOLERANCE = 0.05  # 5%
    
    # Diameter tolerance (mm)
    DIAMETER_TOLERANCE = 1.0  # 1mm
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_duplicate(
        self,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        ngc_cert: Optional[str] = None,
        weight_g: Optional[Decimal] = None,
        diameter_mm: Optional[Decimal] = None,
        issuing_authority: Optional[str] = None,
        denomination: Optional[str] = None,
        max_results: int = 5,
    ) -> list[CoinSummary]:
        """
        Check for duplicate coins.
        
        Args:
            source_type: Import source (heritage, cng, ngc, etc.)
            source_id: Source-specific ID (lot number, cert number)
            ngc_cert: NGC certification number
            weight_g: Coin weight in grams
            diameter_mm: Coin diameter in mm
            issuing_authority: Ruler/issuer name
            denomination: Coin type
            max_results: Maximum similar coins to return
            
        Returns:
            List of similar coins with match reasons
        """
        similar: list[CoinSummary] = []
        seen_ids: set[int] = set()
        
        # 1. Check by source_id in ImportRecord (exact match - highest priority)
        if source_type and source_id:
            existing = self.db.query(ImportRecord).filter(
                ImportRecord.source_type == source_type.lower(),
                ImportRecord.source_id == source_id
            ).first()
            
            if existing:
                coin = self.db.query(Coin).get(existing.coin_id)
                if coin:
                    similar.append(self._coin_to_summary(
                        coin, 
                        MatchReason.EXACT_SOURCE, 
                        confidence=1.0,
                        source_id=source_id,
                        source_type=source_type
                    ))
                    seen_ids.add(coin.id)
        
        # 2. Check by NGC certification number (exact match)
        if ngc_cert:
            cert_clean = ngc_cert.strip()
            existing = self.db.query(Coin).filter(
                Coin.certification_number == cert_clean
            ).first()
            
            if existing and existing.id not in seen_ids:
                # Also check import record for source info
                import_record = self.db.query(ImportRecord).filter(
                    ImportRecord.coin_id == existing.id
                ).first()
                
                similar.append(self._coin_to_summary(
                    existing, 
                    MatchReason.NGC_CERT, 
                    confidence=1.0,
                    source_id=import_record.source_id if import_record else None,
                    source_type=import_record.source_type if import_record else None
                ))
                seen_ids.add(existing.id)
        
        # 3. Fuzzy match on physical characteristics + ruler
        if weight_g and issuing_authority and len(similar) < max_results:
            fuzzy_matches = self._find_physical_matches(
                weight_g=weight_g,
                diameter_mm=diameter_mm,
                issuing_authority=issuing_authority,
                denomination=denomination,
                exclude_ids=seen_ids,
                limit=max_results - len(similar)
            )
            similar.extend(fuzzy_matches)
        
        return similar[:max_results]
    
    def _find_physical_matches(
        self,
        weight_g: Decimal,
        diameter_mm: Optional[Decimal],
        issuing_authority: str,
        denomination: Optional[str],
        exclude_ids: set[int],
        limit: int,
    ) -> list[CoinSummary]:
        """Find coins with similar physical characteristics."""
        results = []
        
        # Calculate weight tolerance range
        weight_tolerance = float(weight_g) * self.WEIGHT_TOLERANCE
        weight_low = float(weight_g) - weight_tolerance
        weight_high = float(weight_g) + weight_tolerance
        
        # Build query
        query = self.db.query(Coin).filter(
            Coin.weight_g.isnot(None),
            Coin.weight_g.between(weight_low, weight_high),
        )
        
        # Issuing authority filter (case-insensitive partial match)
        issuer_clean = issuing_authority.strip().lower()
        query = query.filter(
            func.lower(Coin.issuing_authority).contains(issuer_clean)
        )
        
        # Optional diameter filter
        if diameter_mm:
            diam_low = float(diameter_mm) - self.DIAMETER_TOLERANCE
            diam_high = float(diameter_mm) + self.DIAMETER_TOLERANCE
            query = query.filter(
                or_(
                    Coin.diameter_mm.is_(None),
                    Coin.diameter_mm.between(diam_low, diam_high)
                )
            )
        
        # Optional denomination filter (case-insensitive)
        if denomination:
            denom_clean = denomination.strip().lower()
            query = query.filter(
                func.lower(Coin.denomination).contains(denom_clean)
            )
        
        # Exclude already found coins
        if exclude_ids:
            query = query.filter(Coin.id.notin_(exclude_ids))
        
        # Execute
        candidates = query.limit(limit * 2).all()  # Get extra to calculate confidence
        
        for coin in candidates[:limit]:
            # Calculate confidence based on how close the match is
            confidence = self._calculate_match_confidence(
                coin, weight_g, diameter_mm, issuing_authority, denomination
            )
            
            # Get import record for source info
            import_record = self.db.query(ImportRecord).filter(
                ImportRecord.coin_id == coin.id
            ).first()
            
            results.append(self._coin_to_summary(
                coin,
                MatchReason.PHYSICAL_MATCH,
                confidence=confidence,
                source_id=import_record.source_id if import_record else None,
                source_type=import_record.source_type if import_record else None
            ))
        
        return results
    
    def _calculate_match_confidence(
        self,
        coin: Coin,
        weight_g: Decimal,
        diameter_mm: Optional[Decimal],
        issuing_authority: str,
        denomination: Optional[str],
    ) -> float:
        """Calculate confidence score for a fuzzy match (0-1)."""
        score = 0.0
        factors = 0
        
        # Weight similarity (up to 0.4)
        if coin.weight_g:
            weight_diff = abs(float(coin.weight_g) - float(weight_g))
            weight_max_diff = float(weight_g) * self.WEIGHT_TOLERANCE
            weight_score = max(0, 1 - (weight_diff / weight_max_diff)) * 0.4
            score += weight_score
            factors += 0.4
        
        # Diameter similarity (up to 0.2)
        if diameter_mm and coin.diameter_mm:
            diam_diff = abs(float(coin.diameter_mm) - float(diameter_mm))
            diam_score = max(0, 1 - (diam_diff / self.DIAMETER_TOLERANCE)) * 0.2
            score += diam_score
            factors += 0.2
        
        # Issuing authority match (up to 0.25)
        if coin.issuing_authority:
            issuer_lower = issuing_authority.strip().lower()
            coin_issuer = coin.issuing_authority.lower()
            if issuer_lower == coin_issuer:
                score += 0.25
            elif issuer_lower in coin_issuer or coin_issuer in issuer_lower:
                score += 0.15
            factors += 0.25
        
        # Denomination match (up to 0.15)
        if denomination and coin.denomination:
            denom_lower = denomination.strip().lower()
            coin_denom = coin.denomination.lower()
            if denom_lower == coin_denom:
                score += 0.15
            elif denom_lower in coin_denom or coin_denom in denom_lower:
                score += 0.08
            factors += 0.15
        
        # Normalize to 0-1 range
        return min(1.0, score / factors) if factors > 0 else 0.0
    
    def _coin_to_summary(
        self,
        coin: Coin,
        match_reason: MatchReason,
        confidence: float,
        source_id: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> CoinSummary:
        """Convert a Coin model to CoinSummary for preview."""
        # Get thumbnail from images
        thumbnail = None
        if coin.images:
            primary = next((img for img in coin.images if img.is_primary), None)
            if primary:
                thumbnail = primary.file_path
            elif coin.images:
                thumbnail = coin.images[0].file_path
        
        # Compose title
        title_parts = []
        if coin.issuing_authority:
            title_parts.append(coin.issuing_authority)
        if coin.denomination:
            title_parts.append(coin.denomination)
        title = " - ".join(title_parts) if title_parts else f"Coin #{coin.id}"
        
        return CoinSummary(
            id=coin.id,
            title=title,
            thumbnail=thumbnail,
            source_id=source_id,
            source_type=source_type,
            match_reason=match_reason,
            match_confidence=round(confidence, 2),
            issuing_authority=coin.issuing_authority,
            denomination=coin.denomination,
            metal=coin.metal.value if coin.metal else None,
            weight_g=coin.weight_g,
            grade=coin.grade,
        )
    
    def check_exact_duplicate(
        self,
        source_type: str,
        source_id: str,
    ) -> Optional[int]:
        """
        Quick check for exact duplicate by source.
        
        Returns:
            Coin ID if exact duplicate exists, None otherwise
        """
        existing = self.db.query(ImportRecord).filter(
            ImportRecord.source_type == source_type.lower(),
            ImportRecord.source_id == source_id
        ).first()
        
        return existing.coin_id if existing else None


def get_duplicate_detector(db: Session) -> DuplicateDetector:
    """Dependency injection for DuplicateDetector."""
    return DuplicateDetector(db)
