from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
import re
import difflib
from src.infrastructure.persistence.models_vocab import IssuerModel, IssuerAliasModel

class MatchMethod(str, Enum):
    EXACT = "exact_match"
    ALIAS = "alias_match"
    FUZZY = "fuzzy_match"
    MANUAL = "manual"

@dataclass
class NormalizationResult:
    success: bool
    canonical_id: Optional[int] = None
    canonical_name: Optional[str] = None
    method: Optional[MatchMethod] = None
    confidence: float = 0.0
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    needs_review: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

class VocabNormalizer:
    _issuer_cache: Optional[Dict[str, int]] = None

    def __init__(self, session: Session):
        self.session = session

    def normalize_issuer(self, raw: str) -> NormalizationResult:
        if not raw:
            return NormalizationResult(success=False)

        normalized = self._normalize_string(raw)

        # 1. Exact Match
        stmt = select(IssuerModel).where(IssuerModel.canonical_name == raw) # Case sensitive often preferred for exact, but let's assume raw might vary
        # Actually, let's try case-insensitive exact match
        # stmt = select(IssuerModel).where(IssuerModel.canonical_name.ilike(raw))
        # But for 'Exact' strictness, let's try normalized vs normalized canonical if we had it.
        # Let's stick to strict name match first.
        result = self.session.scalar(stmt)
        if result:
            return NormalizationResult(
                success=True,
                canonical_id=result.id,
                canonical_name=result.canonical_name,
                method=MatchMethod.EXACT,
                confidence=1.0
            )

        # 2. Alias Match
        stmt = select(IssuerAliasModel).where(IssuerAliasModel.normalized_form == normalized)
        alias_result = self.session.scalar(stmt)
        if alias_result:
             # We need to fetch the issuer to get canonical name
             # Assuming relationship is eager or we can access it
             # If lazy, this triggers a query
             issuer = alias_result.issuer
             return NormalizationResult(
                success=True,
                canonical_id=issuer.id,
                canonical_name=issuer.canonical_name,
                method=MatchMethod.ALIAS,
                confidence=0.95 # High confidence for explicit alias
             )

        # 3. Fuzzy Match
        return self._fuzzy_issuer_match(normalized)

    def _fuzzy_issuer_match(self, normalized: str) -> NormalizationResult:
        if VocabNormalizer._issuer_cache is None:
            self._build_issuer_cache()
        
        matches = difflib.get_close_matches(normalized, VocabNormalizer._issuer_cache.keys(), n=1, cutoff=0.8)
        
        if matches:
            best_match = matches[0]
            issuer_id = VocabNormalizer._issuer_cache[best_match]
            # Fetch issuer
            issuer = self.session.get(IssuerModel, issuer_id)
            
            # Calculate simple confidence ratio
            ratio = difflib.SequenceMatcher(None, normalized, best_match).ratio()
            
            return NormalizationResult(
                success=True,
                canonical_id=issuer.id,
                canonical_name=issuer.canonical_name,
                method=MatchMethod.FUZZY,
                confidence=ratio,
                details={"matched_string": best_match}
            )

        return NormalizationResult(success=False)

    def _build_issuer_cache(self):
        cache = {}
        # Load all issuers
        issuers = self.session.execute(select(IssuerModel)).scalars().all()
        for i in issuers:
            cache[self._normalize_string(i.canonical_name)] = i.id
        
        # Load all aliases
        aliases = self.session.execute(select(IssuerAliasModel)).scalars().all()
        for a in aliases:
             cache[a.normalized_form] = a.issuer_id
             
        VocabNormalizer._issuer_cache = cache

    def _normalize_string(self, s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s
