"""
WishlistMatchingService - Score and match auction lots against wishlist criteria.

Analyzes auction lots to find potential matches for wishlist items,
calculating confidence scores and budget comparisons.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
from typing import Optional, List

from src.domain.coin import WishlistItem, WishlistMatch
from src.domain.auction import AuctionLot
from src.domain.repositories import IWishlistItemRepository, IWishlistMatchRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MatchScore:
    """Scoring result for a wishlist/lot match."""
    score: Decimal  # 0-100
    confidence: str  # exact, high, medium, possible
    reasons: tuple  # Tuple of reasons for immutability
    is_below_budget: bool
    is_below_market: bool

    @property
    def reason_list(self) -> List[str]:
        """Convert reasons tuple to list for serialization."""
        return list(self.reasons)


class WishlistMatchingService:
    """
    Service for matching auction lots to wishlist criteria.

    Uses a multi-factor scoring algorithm considering:
    - Issuer match (40 points)
    - Catalog reference match (25 points)
    - Denomination match (15 points)
    - Date range match (10 points)
    - Grade compatibility (10 points)

    Budget comparison determines value score.
    """

    # Scoring weights
    WEIGHT_ISSUER = 40
    WEIGHT_CATALOG_REF = 25
    WEIGHT_DENOMINATION = 15
    WEIGHT_DATE_RANGE = 10
    WEIGHT_GRADE = 10

    # Confidence thresholds
    CONFIDENCE_EXACT = 90
    CONFIDENCE_HIGH = 70
    CONFIDENCE_MEDIUM = 50

    def __init__(
        self,
        wishlist_repo: IWishlistItemRepository,
        match_repo: IWishlistMatchRepository,
    ):
        self._wishlist_repo = wishlist_repo
        self._match_repo = match_repo

    def score_lot(self, item: WishlistItem, lot: AuctionLot) -> MatchScore:
        """
        Calculate match score between wishlist item and auction lot.

        Args:
            item: The wishlist item with desired criteria
            lot: The auction lot to evaluate

        Returns:
            MatchScore with score, confidence, and comparison flags
        """
        score = Decimal("0")
        reasons: List[str] = []

        # Issuer matching
        issuer_score = self._match_issuer(item, lot)
        score += issuer_score
        if issuer_score > 0:
            reasons.append(f"Issuer match: {lot.issuer}")

        # Catalog reference matching
        ref_score = self._match_catalog_ref(item, lot)
        score += ref_score
        if ref_score > 0:
            reasons.append("Catalog reference match")

        # Denomination matching (searches description since AuctionLot has no denomination field)
        denom_score = self._match_denomination(item, lot)
        score += denom_score
        if denom_score > 0:
            reasons.append(f"Denomination match: {item.denomination}")

        # Date range matching
        date_score = self._match_date_range(item, lot)
        score += date_score
        if date_score > 0:
            reasons.append(f"Date range compatible")

        # Grade matching
        grade_score = self._match_grade(item, lot)
        score += grade_score
        if grade_score > 0:
            reasons.append(f"Grade meets minimum: {lot.grade}")

        # Determine confidence level
        if score >= self.CONFIDENCE_EXACT:
            confidence = "exact"
        elif score >= self.CONFIDENCE_HIGH:
            confidence = "high"
        elif score >= self.CONFIDENCE_MEDIUM:
            confidence = "medium"
        else:
            confidence = "possible"

        # Budget comparison - use hammer_price (realized) or estimate as fallback
        lot_price = lot.hammer_price or lot.estimate_low or Decimal("0")
        is_below_budget = (
            item.max_price is not None and lot_price <= item.max_price
        )
        is_below_target = (
            item.target_price is not None and lot_price <= item.target_price
        )

        return MatchScore(
            score=score,
            confidence=confidence,
            reasons=tuple(reasons),
            is_below_budget=is_below_budget,
            is_below_market=is_below_target,
        )

    def find_matches(
        self,
        lots: List[AuctionLot],
        min_score: Decimal = Decimal("30"),
    ) -> List[WishlistMatch]:
        """
        Find matches for all active wishlist items against provided lots.

        Args:
            lots: List of auction lots to evaluate
            min_score: Minimum score threshold (default 30)

        Returns:
            List of WishlistMatch records for qualifying matches
        """
        # Get all active wishlist items
        active_items = self._wishlist_repo.list_all(status="wanted")
        logger.info("Finding matches: %d wishlist items x %d lots", len(active_items), len(lots))

        matches: List[WishlistMatch] = []
        match_count_by_item: dict[int, int] = {}

        for item in active_items:
            for lot in lots:
                score_result = self.score_lot(item, lot)

                if score_result.score >= min_score:
                    match = self.create_match(item.id, lot, score_result)
                    if match:
                        matches.append(match)
                        match_count_by_item[item.id] = match_count_by_item.get(item.id, 0) + 1

        if matches:
            logger.info(
                "Found %d matches across %d wishlist items (min_score=%.0f)",
                len(matches), len(match_count_by_item), min_score
            )
        else:
            logger.debug("No matches found above threshold %.0f", min_score)

        return matches

    def create_match(
        self,
        item_id: int,
        lot: AuctionLot,
        score: MatchScore,
    ) -> Optional[WishlistMatch]:
        """
        Create a new wishlist match record.

        Args:
            item_id: ID of the wishlist item
            lot: The matching auction lot
            score: The calculated MatchScore

        Returns:
            Created WishlistMatch if successful, None otherwise
        """
        # Determine price for comparison - use hammer_price (realized) or estimate
        lot_price = lot.hammer_price or lot.estimate_low

        # Construct title from available lot data
        title = f"{lot.issuer or ''} {lot.mint or ''}".strip() or "Unknown Lot"

        # Get image URL - prefer primary, fall back to first additional
        image_url = lot.primary_image_url
        if not image_url and lot.additional_images:
            image_url = lot.additional_images[0]

        match = WishlistMatch(
            wishlist_item_id=item_id,
            match_type="auction_lot",
            match_source=lot.source,
            match_id=lot.lot_id or str(lot.lot_number or lot.url or ""),
            match_url=lot.url,
            title=title,
            description=lot.description,
            image_url=image_url,
            grade=lot.grade,
            grade_numeric=self._parse_grade_numeric(lot.grade),
            price=lot_price,
            estimate_low=lot.estimate_low,
            estimate_high=lot.estimate_high,
            currency=lot.currency,
            auction_date=lot.auction_date,
            match_score=score.score,
            match_confidence=score.confidence,
            match_reasons=json.dumps(score.reason_list),
            is_below_budget=score.is_below_budget,
            is_below_market=score.is_below_market,
            created_at=datetime.now(timezone.utc),
        )

        return self._match_repo.create(item_id, match)

    def _match_issuer(self, item: WishlistItem, lot: AuctionLot) -> Decimal:
        """Score issuer match."""
        if not item.issuer or not lot.issuer:
            return Decimal("0")

        item_issuer = item.issuer.lower().strip()
        lot_issuer = lot.issuer.lower().strip()

        # Exact match
        if item_issuer == lot_issuer:
            return Decimal(self.WEIGHT_ISSUER)

        # Partial match (one contains the other)
        if item_issuer in lot_issuer or lot_issuer in item_issuer:
            return Decimal(self.WEIGHT_ISSUER * 0.7)

        # Word overlap
        item_words = set(item_issuer.split())
        lot_words = set(lot_issuer.split())
        if item_words & lot_words:
            return Decimal(self.WEIGHT_ISSUER * 0.4)

        return Decimal("0")

    # Compiled regex patterns for catalog matching (cached for performance)
    # Roman numerals I through X for RIC volumes
    _ROMAN_NUMERALS = r'(?:I{1,3}|IV|VI{0,3}|IX|X)'

    def _match_catalog_ref(self, item: WishlistItem, lot: AuctionLot) -> Decimal:
        """
        Score catalog reference match.

        Supports common ancient coin catalog systems:
        - RIC (Roman Imperial Coinage) volumes I-X
        - RPC (Roman Provincial Coinage) with supplements
        - Crawford (Roman Republican)
        - RSC (Roman Silver Coins)
        - Sear (various editions: S, SG, SGCV)
        - BMC (British Museum Catalog)
        - SNG (Sylloge Nummorum Graecorum)
        - Cohen

        Note: AuctionLot doesn't currently have a references field.
        This method searches the lot description for catalog references.
        """
        if not item.catalog_ref:
            return Decimal("0")

        # AuctionLot doesn't have a references field - search in description
        if not lot.description:
            return Decimal("0")

        item_ref = item.catalog_ref.upper().replace(" ", "")
        desc_upper = lot.description.upper()

        # Pattern match if configured (user-provided regex)
        if item.catalog_ref_pattern:
            if re.search(item.catalog_ref_pattern, lot.description, re.IGNORECASE):
                return Decimal(self.WEIGHT_CATALOG_REF * 0.8)

        # Exact match (normalized)
        # Common formats: "RIC 207", "RIC VII 207", "Crawford 44/5"
        if item_ref in desc_upper.replace(" ", ""):
            return Decimal(self.WEIGHT_CATALOG_REF)

        # Check for Crawford fraction notation (e.g., "44/5", "494/42a")
        crawford_match = re.search(r'(\d+)/(\d+[a-z]?)', item_ref)
        if crawford_match:
            crawford_pattern = rf'CRAWFORD\s*{crawford_match.group(1)}\s*/\s*{crawford_match.group(2)}'
            if re.search(crawford_pattern, desc_upper, re.IGNORECASE):
                return Decimal(self.WEIGHT_CATALOG_REF)

        # Partial match - look for catalog prefix and number
        if len(item_ref) >= 2:
            # Extract prefix and numbers
            prefix_match = re.match(r'([A-Z]+)', item_ref)
            if prefix_match:
                prefix = prefix_match.group(1)
                item_nums = re.findall(r'\d+', item_ref)

                if item_nums and prefix in desc_upper:
                    # Build pattern based on catalog system
                    if prefix in ('RIC', 'RPC'):
                        # RIC/RPC with optional volume (I-X) and supplements (S, S2)
                        pattern = rf'{prefix}\s*(?:{self._ROMAN_NUMERALS}|S\d?)?\s*{item_nums[0]}'
                    elif prefix in ('RSC', 'COHEN', 'BMC'):
                        # Simple number after prefix
                        pattern = rf'{prefix}\s*{item_nums[0]}'
                    elif prefix in ('S', 'SG', 'SGCV', 'SEAR'):
                        # Sear references
                        pattern = rf'(?:SEAR|SG(?:CV)?|S)\s*{item_nums[0]}'
                    elif prefix == 'SNG':
                        # SNG requires collection name
                        pattern = rf'SNG\s+\w+\s+{item_nums[0]}'
                    else:
                        # Generic pattern
                        pattern = rf'{re.escape(prefix)}\s*{item_nums[0]}'

                    if re.search(pattern, desc_upper, re.IGNORECASE):
                        return Decimal(self.WEIGHT_CATALOG_REF * 0.6)

        return Decimal("0")

    def _match_denomination(self, item: WishlistItem, lot: AuctionLot) -> Decimal:
        """
        Score denomination match.

        Note: AuctionLot doesn't have a denomination field.
        This method searches for denomination in the lot description.
        """
        if not item.denomination:
            return Decimal("0")

        if not lot.description:
            return Decimal("0")

        item_denom = item.denomination.lower().strip()
        desc_lower = lot.description.lower()

        # Direct match in description
        if item_denom in desc_lower:
            return Decimal(self.WEIGHT_DENOMINATION)

        # Handle common variants - comprehensive for ancient coins
        variants = {
            # Roman Imperial/Republic
            "denarius": ["denar", "den", "denarii"],
            "antoninianus": ["ant", "antoninian", "antoniniani", "radiates", "radiate"],
            "sestertius": ["sest", "sestertii", "sesterces"],
            "as": ["asses", "aes"],  # Note: "as" collision with English handled below
            "aureus": ["aurei", "gold aureus"],
            "solidus": ["solidi", "gold solidus"],
            "follis": ["folles", "nummus", "nummi"],
            "siliqua": ["siliquae"],
            "tremissis": ["tremisses"],
            "semis": ["semisses"],
            "dupondius": ["dupondii"],
            "quadrans": ["quadrantes"],
            "quinarius": ["quinarii", "half denarius"],

            # Late Roman bronze size classifications
            "ae1": ["ae 1", "large bronze"],
            "ae2": ["ae 2", "medium bronze"],
            "ae3": ["ae 3", "small bronze"],
            "ae4": ["ae 4", "minimus", "minimi"],

            # Late Roman silver/gold
            "miliarense": ["miliarensia", "heavy miliarense", "light miliarense"],
            "centenionalis": ["centenionales", "maiorina"],
            "argenteus": ["argentei"],

            # Greek silver
            "tetradrachm": ["tetradrachms", "tetra", "4 drachm"],
            "didrachm": ["didrachms", "2 drachm"],
            "tridrachm": ["tridrachms", "3 drachm"],
            "drachm": ["drachms", "drachma", "drachmae"],
            "hemidrachm": ["hemidrachms", "half drachm"],
            "triobol": ["triobols", "triobolus"],
            "diobol": ["diobols", "diobolus"],
            "obol": ["obols", "obolus", "oboli"],
            "hemiobol": ["hemiobols", "half obol"],
            "trihemiobol": ["trihemiobols"],
            "tetartemorion": ["tetartemoria"],

            # Greek gold
            "stater": ["staters", "gold stater"],
            "hecte": ["hectai", "1/6 stater"],
            "hemistater": ["hemistaters", "half stater"],

            # Greek/Macedonian large denominations
            "decadrachm": ["decadrachms", "10 drachm"],
            "octodrachm": ["octodrachms", "8 drachm"],
            "pentadrachm": ["pentadrachms", "5 drachm"],
        }

        for standard, alts in variants.items():
            all_forms = [standard] + alts
            if item_denom in all_forms:
                for form in all_forms:
                    # Special handling for "as" to avoid false positives
                    if form == "as":
                        # Look for "as" as a complete word or with common suffixes
                        if re.search(r'\b(as|asses|aes)\b', desc_lower):
                            return Decimal(self.WEIGHT_DENOMINATION)
                    elif form in desc_lower:
                        return Decimal(self.WEIGHT_DENOMINATION)

        return Decimal("0")

    def _match_date_range(self, item: WishlistItem, lot: AuctionLot) -> Decimal:
        """Score date range compatibility."""
        # Need at least one endpoint on each
        if item.year_start is None and item.year_end is None:
            return Decimal("0")

        # Use AuctionLot's year_start/year_end fields
        lot_start = lot.year_start
        lot_end = lot.year_end

        if lot_start is None and lot_end is None:
            return Decimal("0")

        # Use available endpoints with safe defaults
        item_start = item.year_start if item.year_start is not None else item.year_end
        item_end = item.year_end if item.year_end is not None else item.year_start
        lot_start_val = lot_start if lot_start is not None else lot_end
        lot_end_val = lot_end if lot_end is not None else lot_start

        # All values should be non-None at this point, but add safety check
        if item_start is None or item_end is None or lot_start_val is None or lot_end_val is None:
            return Decimal("0")

        # Check for overlap
        if lot_start_val <= item_end and lot_end_val >= item_start:
            return Decimal(self.WEIGHT_DATE_RANGE)

        # Close proximity (within 50 years)
        gap = min(abs(lot_start_val - item_end), abs(item_start - lot_end_val))
        if gap <= 50:
            return Decimal(self.WEIGHT_DATE_RANGE * 0.5)

        return Decimal("0")

    def _match_grade(self, item: WishlistItem, lot: AuctionLot) -> Decimal:
        """Score grade compatibility."""
        if not item.min_grade:
            return Decimal(self.WEIGHT_GRADE)  # No requirement = match

        if not lot.grade:
            return Decimal("0")

        item_grade_num = item.min_grade_numeric or self._parse_grade_numeric(item.min_grade)
        lot_grade_num = self._parse_grade_numeric(lot.grade)

        if item_grade_num is None or lot_grade_num is None:
            return Decimal("0")

        if lot_grade_num >= item_grade_num:
            return Decimal(self.WEIGHT_GRADE)

        # Close to minimum
        if lot_grade_num >= item_grade_num - 5:
            return Decimal(self.WEIGHT_GRADE * 0.5)

        return Decimal("0")

    def _parse_grade_numeric(self, grade: Optional[str]) -> Optional[int]:
        """
        Parse a grade string to numeric value.

        Supports multiple grading conventions:
        - NGC/PCGS numeric (MS 63, AU 55, etc.)
        - NGC Ancients (Ch VF, Ch XF, Ch AU)
        - Traditional text grades (VF, EF, AU)
        - European conventions (GVF, GEF, NEF)
        - Modifiers (+, -, Near, Choice, Superb)
        """
        if not grade:
            return None

        grade_upper = grade.upper().strip()

        # NGC Ancients specific patterns first (Ch VF, Ch XF, etc.)
        ngc_ancient_patterns = [
            (r'CH\s*MS\s*(\d+)', lambda m: int(m.group(1))),  # Ch MS 63
            (r'CH\s*AU', lambda m: 58),  # Choice AU
            (r'CH\s*XF', lambda m: 43),  # Choice XF
            (r'CH\s*EF', lambda m: 43),  # Choice EF
            (r'CH\s*VF', lambda m: 30),  # Choice VF
            (r'CH\s*F', lambda m: 15),   # Choice Fine
            (r'GEM\s*MS\s*(\d+)', lambda m: int(m.group(1))),  # Gem MS 65
            (r'GEM\s*MS', lambda m: 65),  # Gem MS (no number)
            (r'SUPERB\s*MS', lambda m: 67),
        ]

        for pattern, value_fn in ngc_ancient_patterns:
            match = re.search(pattern, grade_upper)
            if match:
                return value_fn(match)

        # Direct numeric extraction (MS 63, AU 55, etc.)
        ms_match = re.search(r'(?:MS|MINT\s*STATE)\s*(\d+)', grade_upper)
        if ms_match:
            return int(ms_match.group(1))

        au_match = re.search(r'AU\s*(\d+)', grade_upper)
        if au_match:
            return int(au_match.group(1))

        # Generic numeric extraction
        nums = re.findall(r'\d+', grade_upper)
        if nums:
            num = int(nums[0])
            # Validate it's in Sheldon scale range
            if 1 <= num <= 70:
                return num

        # Text grade mapping - expanded for ancient coins and European conventions
        # Priority order matters (check more specific patterns first)
        grade_map = [
            # Mint State with modifiers
            ("SUPERB MS", 67), ("SUPERB", 67),
            ("GEM MS", 65), ("GEM", 65),
            ("CHOICE MS", 63), ("CH MS", 63),
            ("MS", 60), ("MINT STATE", 60), ("UNC", 60), ("FDC", 70),

            # About Uncirculated
            ("CHOICE AU", 58), ("CH AU", 58),
            ("AU+", 58), ("AU", 55), ("ABOUT UNC", 55), ("ALMOST UNC", 55),

            # Extremely Fine (with European variants)
            ("CHOICE XF", 43), ("CHOICE EF", 43), ("CH XF", 43), ("CH EF", 43),
            ("NEAR EF", 38), ("NEF", 38),
            ("GOOD EF", 43), ("GEF", 43), ("GOOD XF", 43), ("GXF", 43),
            ("EF+", 43), ("XF+", 43),
            ("EF", 40), ("XF", 40), ("EXTREMELY FINE", 40),

            # Very Fine (with European variants)
            ("CHOICE VF", 30), ("CH VF", 30),
            ("NEAR VF", 23), ("NVF", 23),
            ("GOOD VF", 30), ("GVF", 30),
            ("VF+", 30),
            ("VF", 25), ("VERY FINE", 25),

            # Fine
            ("CHOICE F", 15), ("CH F", 15),
            ("NEAR F", 10), ("NF", 10),
            ("F+", 15),
            ("F", 12), ("FINE", 12),

            # Very Good
            ("VG+", 10),
            ("VG", 8), ("VERY GOOD", 8),

            # Good
            ("G+", 6),
            ("G", 4), ("GOOD", 4),

            # Below Good
            ("AG", 3), ("ABOUT GOOD", 3),
            ("FAIR", 2),
            ("POOR", 1),
        ]

        for text, value in grade_map:
            if text in grade_upper:
                return value

        return None
