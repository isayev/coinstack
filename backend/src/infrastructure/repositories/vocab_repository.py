"""
Vocabulary Repository Implementation (V3)

This module implements the IVocabRepository interface using SQLAlchemy
with FTS5 full-text search for fast autocomplete and normalization.
"""

import json
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Optional, List, Dict, Any, Union

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.vocab import (
    VocabTerm, 
    VocabType, 
    NormalizationResult, 
    IVocabRepository,
    Issuer,
    Mint,
)
from src.domain.llm import FuzzyMatch
from src.infrastructure.persistence.models_vocab import (
    VocabTermModel,
    CoinVocabAssignmentModel,
)

logger = logging.getLogger(__name__)


class SqlAlchemyVocabRepository(IVocabRepository):
    """
    SQLAlchemy implementation of the vocabulary repository.
    
    Uses FTS5 for full-text search and a simple caching layer
    for performance optimization.
    """
    
    NOMISMA_SPARQL = "http://nomisma.org/query/sparql"
    NOMISMA_RECONCILE = "http://nomisma.org/apis/reconcile"
    
    SPARQL_QUERIES = {
        VocabType.ISSUER: """
            PREFIX nmo: <http://nomisma.org/ontology#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            SELECT ?uri ?label ?start ?end WHERE {
                ?uri a nmo:Person ; skos:prefLabel ?label .
                FILTER(lang(?label) = "en")
                OPTIONAL { ?uri nmo:hasStartDate ?start }
                OPTIONAL { ?uri nmo:hasEndDate ?end }
            }
        """,
        VocabType.MINT: """
            PREFIX nmo: <http://nomisma.org/ontology#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            SELECT ?uri ?label WHERE {
                ?uri a nmo:Mint ; skos:prefLabel ?label .
                FILTER(lang(?label) = "en")
            }
        """,
        VocabType.DENOMINATION: """
            PREFIX nmo: <http://nomisma.org/ontology#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            SELECT ?uri ?label WHERE {
                ?uri a nmo:Denomination ; skos:prefLabel ?label .
                FILTER(lang(?label) = "en")
            }
        """
    }

    def __init__(self, session: Session):
        self.session = session
    
    # -------------------------------------------------------------------------
    # Cache helpers
    # -------------------------------------------------------------------------
    
    def _cache_get(self, key: str) -> Optional[str]:
        """Get cached data if not expired."""
        try:
            result = self.session.execute(
                text("SELECT data FROM vocab_cache WHERE cache_key = :key AND expires_at > datetime('now')"),
                {"key": key}
            )
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.debug(f"Cache get failed for key: {e}")
            return None
    
    def _cache_set(self, key: str, data: str, ttl_hours: int = 1):
        """Set cache with TTL."""
        try:
            expires = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat()
            self.session.execute(
                text("INSERT OR REPLACE INTO vocab_cache (cache_key, data, expires_at) VALUES (:key, :data, :expires)"),
                {"key": key, "data": data, "expires": expires}
            )
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    def _cache_clear_expired(self):
        """Clear expired cache entries."""
        try:
            self.session.execute(
                text("DELETE FROM vocab_cache WHERE expires_at < datetime('now')")
            )
        except Exception as e:
            logger.debug(f"Cache clear expired failed: {e}")
    
    # -------------------------------------------------------------------------
    # Core repository methods
    # -------------------------------------------------------------------------
    
    def search(self, vocab_type: VocabType, query: str, limit: int = 10) -> List[VocabTerm]:
        """
        Search vocabulary terms using FTS5 full-text search.
        
        Supports prefix matching (e.g., "Aug" matches "Augustus").
        Results are cached for 1 hour.
        """
        if not query or len(query) < 1:
            return []
        
        # Check cache first
        cache_key = f"search:{vocab_type.value}:{query.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return [VocabTerm.from_dict(t) for t in data]
            except Exception as e:
                logger.debug(f"Cache deserialization failed for search results: {e}")
        
        # FTS5 query with type filter
        try:
            # Escape special FTS5 characters
            safe_query = query.replace('"', '""').replace("'", "''")
            
            result = self.session.execute(
                text("""
                    SELECT vt.id, vt.vocab_type, vt.canonical_name, vt.nomisma_uri, vt.metadata
                    FROM vocab_terms vt
                    JOIN vocab_terms_fts fts ON vt.id = fts.rowid
                    WHERE vocab_terms_fts MATCH :query
                      AND vt.vocab_type = :vtype
                    LIMIT :limit
                """),
                {"query": f'"{safe_query}"*', "vtype": vocab_type.value, "limit": limit}
            )
            
            terms = []
            for row in result.fetchall():
                terms.append(VocabTerm(
                    id=row[0],
                    vocab_type=VocabType(row[1]),
                    canonical_name=row[2],
                    nomisma_uri=row[3],
                    metadata=json.loads(row[4] or "{}")
                ))
            
            # Cache results
            if terms:
                self._cache_set(cache_key, json.dumps([t.to_dict() for t in terms]))
            
            return terms
            
        except Exception as e:
            logger.warning(f"FTS5 search failed, falling back to LIKE: {e}")
            # Fallback to LIKE query if FTS5 fails
            return self._search_fallback(vocab_type, query, limit)
    
    def _search_fallback(self, vocab_type: VocabType, query: str, limit: int) -> List[VocabTerm]:
        """Fallback search using LIKE (when FTS5 is not available)."""
        result = self.session.execute(
            text("""
                SELECT id, vocab_type, canonical_name, nomisma_uri, metadata
                FROM vocab_terms
                WHERE vocab_type = :vtype
                  AND canonical_name LIKE :query
                LIMIT :limit
            """),
            {"vtype": vocab_type.value, "query": f"{query}%", "limit": limit}
        )
        
        terms = []
        for row in result.fetchall():
            terms.append(VocabTerm(
                id=row[0],
                vocab_type=VocabType(row[1]),
                canonical_name=row[2],
                nomisma_uri=row[3],
                metadata=json.loads(row[4] or "{}")
            ))
        return terms
    
    def normalize(
        self, 
        raw: str, 
        vocab_type: VocabType, 
        context: Optional[Dict[str, Any]] = None
    ) -> NormalizationResult:
        """
        Normalize raw text to a canonical vocabulary term.
        
        Uses a chain of matching strategies:
        1. Exact match on canonical_name (case-sensitive)
        2. Case-insensitive exact match
        3. FTS5 fuzzy match with confidence scoring
        4. Nomisma reconciliation API (external)
        
        Returns needs_review=True if confidence < 0.92 or no match found.
        """
        context = context or {}
        
        if not raw or not raw.strip():
            return NormalizationResult(
                success=False, 
                method="", 
                confidence=0.0, 
                raw_input=raw or "",
                needs_review=True
            )
        
        raw_stripped = raw.strip()
        
        # 1. Exact canonical match (case-sensitive)
        result = self.session.execute(
            text("""
                SELECT id, canonical_name, nomisma_uri, metadata 
                FROM vocab_terms 
                WHERE canonical_name = :name AND vocab_type = :vtype
            """),
            {"name": raw_stripped, "vtype": vocab_type.value}
        )
        row = result.fetchone()
        if row:
            term = VocabTerm(
                id=row[0], 
                vocab_type=vocab_type, 
                canonical_name=row[1], 
                nomisma_uri=row[2], 
                metadata=json.loads(row[3] or "{}")
            )
            return NormalizationResult(
                success=True, 
                term=term, 
                method="exact", 
                confidence=1.0, 
                raw_input=raw_stripped
            )
        
        # 2. Case-insensitive exact match
        result = self.session.execute(
            text("""
                SELECT id, canonical_name, nomisma_uri, metadata 
                FROM vocab_terms 
                WHERE LOWER(canonical_name) = LOWER(:name) AND vocab_type = :vtype
            """),
            {"name": raw_stripped, "vtype": vocab_type.value}
        )
        row = result.fetchone()
        if row:
            term = VocabTerm(
                id=row[0], 
                vocab_type=vocab_type, 
                canonical_name=row[1], 
                nomisma_uri=row[2], 
                metadata=json.loads(row[3] or "{}")
            )
            return NormalizationResult(
                success=True, 
                term=term, 
                method="exact_ci", 
                confidence=0.98, 
                raw_input=raw_stripped
            )
        
        # 3. FTS5 fuzzy match (top results)
        fts_results = self.search(vocab_type, raw_stripped, limit=5)
        if fts_results:
            best = fts_results[0]
            # Calculate confidence via sequence matching
            conf = SequenceMatcher(
                None, 
                raw_stripped.lower(), 
                best.canonical_name.lower()
            ).ratio()
            
            if conf >= 0.80:
                return NormalizationResult(
                    success=True, 
                    term=best, 
                    method="fts", 
                    confidence=conf, 
                    raw_input=raw_stripped,
                    needs_review=(conf < 0.92),
                    alternatives=fts_results[1:3]  # Include alternatives for review
                )
        
        # 4. Nomisma reconciliation API (external)
        nomisma_result = self._reconcile_nomisma(raw_stripped, vocab_type)
        if nomisma_result:
            return NormalizationResult(
                success=True, 
                term=nomisma_result, 
                method="nomisma", 
                confidence=0.85, 
                raw_input=raw_stripped, 
                needs_review=True
            )
        
        # 5. No match found - queue for manual review
        return NormalizationResult(
            success=False, 
            method="", 
            confidence=0.0, 
            raw_input=raw_stripped, 
            needs_review=True,
            alternatives=fts_results[:3] if fts_results else []
        )
    
    def _reconcile_nomisma(self, raw: str, vocab_type: VocabType) -> Optional[VocabTerm]:
        """Try Nomisma reconciliation API for unknown terms."""
        # Only reconcile for types that Nomisma supports
        if vocab_type not in (VocabType.ISSUER, VocabType.MINT, VocabType.DENOMINATION):
            return None
        
        try:
            # Map vocab type to Nomisma type URI
            type_map = {
                VocabType.ISSUER: "http://nomisma.org/id/person",
                VocabType.MINT: "http://nomisma.org/id/mint",
                VocabType.DENOMINATION: "http://nomisma.org/id/denomination",
            }
            
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    self.NOMISMA_RECONCILE,
                    params={"query": raw, "type": type_map.get(vocab_type, "")}
                )
                
                if resp.status_code != 200:
                    return None
                
                data = resp.json()
                
                # Check for results
                if data.get("result") and len(data["result"]) > 0:
                    best = data["result"][0]
                    if best.get("match") or best.get("score", 0) > 0.7:
                        # Upsert to vocab_terms
                        return self._upsert_term(
                            vocab_type, 
                            best.get("name", raw), 
                            best.get("id", "")
                        )
                        
        except Exception as e:
            logger.warning(f"Nomisma reconciliation failed: {e}")
        
        return None
    
    def _upsert_term(
        self, 
        vocab_type: VocabType, 
        name: str, 
        uri: str, 
        metadata: Optional[Dict] = None
    ) -> VocabTerm:
        """Insert or get existing term."""
        self.session.execute(
            text("""
                INSERT OR IGNORE INTO vocab_terms (vocab_type, canonical_name, nomisma_uri, metadata)
                VALUES (:vtype, :name, :uri, :meta)
            """),
            {
                "vtype": vocab_type.value, 
                "name": name, 
                "uri": uri,
                "meta": json.dumps(metadata) if metadata else None
            }
        )
        self.session.flush()
        
        result = self.session.execute(
            text("SELECT id, metadata FROM vocab_terms WHERE vocab_type = :vtype AND canonical_name = :name"),
            {"vtype": vocab_type.value, "name": name}
        )
        row = result.fetchone()
        
        return VocabTerm(
            id=row[0], 
            vocab_type=vocab_type, 
            canonical_name=name, 
            nomisma_uri=uri,
            metadata=json.loads(row[1] or "{}") if row[1] else (metadata or {})
        )
    
    def sync_nomisma(self, vocab_type: VocabType) -> Dict[str, int]:
        """
        Bulk sync vocabulary from Nomisma SPARQL endpoint.
        
        Only supports ISSUER, MINT, and DENOMINATION types.
        Returns stats dict with {"added": N, "unchanged": M}.
        """
        query = self.SPARQL_QUERIES.get(vocab_type)
        if not query:
            raise ValueError(f"No SPARQL query defined for {vocab_type}")
        
        stats = {"added": 0, "unchanged": 0, "errors": 0}
        
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    self.NOMISMA_SPARQL,
                    data={"query": query},
                    headers={"Accept": "application/sparql-results+json"}
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.error(f"Nomisma SPARQL query failed: {e}")
            raise RuntimeError(f"Failed to fetch from Nomisma: {e}")
        
        bindings = data.get("results", {}).get("bindings", [])
        logger.info(f"Fetched {len(bindings)} {vocab_type.value} entries from Nomisma")
        
        for binding in bindings:
            try:
                uri = binding["uri"]["value"]
                label = binding["label"]["value"]
                
                # Build metadata
                metadata = {}
                if "start" in binding:
                    metadata["reign_start"] = self._parse_year(binding["start"]["value"])
                if "end" in binding:
                    metadata["reign_end"] = self._parse_year(binding["end"]["value"])
                
                # Upsert
                result = self.session.execute(
                    text("""
                        INSERT INTO vocab_terms (vocab_type, canonical_name, nomisma_uri, metadata)
                        VALUES (:vtype, :name, :uri, :meta)
                        ON CONFLICT(vocab_type, canonical_name) DO NOTHING
                    """),
                    {
                        "vtype": vocab_type.value, 
                        "name": label, 
                        "uri": uri, 
                        "meta": json.dumps(metadata) if metadata else None
                    }
                )
                
                if result.rowcount > 0:
                    stats["added"] += 1
                else:
                    stats["unchanged"] += 1
                    
            except Exception as e:
                logger.warning(f"Error processing binding: {e}")
                stats["errors"] += 1
        
        return stats
    
    @staticmethod
    def _parse_year(value: str) -> Optional[int]:
        """Parse year from various formats."""
        if not value:
            return None
        try:
            # Handle formats like "-0027", "0014", "200"
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def get_by_id(self, term_id: int) -> Optional[VocabTerm]:
        """Get a vocabulary term by ID."""
        result = self.session.execute(
            text("""
                SELECT id, vocab_type, canonical_name, nomisma_uri, metadata
                FROM vocab_terms
                WHERE id = :id
            """),
            {"id": term_id}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return VocabTerm(
            id=row[0],
            vocab_type=VocabType(row[1]),
            canonical_name=row[2],
            nomisma_uri=row[3],
            metadata=json.loads(row[4] or "{}")
        )
    
    def get_by_canonical(
        self, 
        vocab_type: VocabType, 
        name: str
    ) -> Optional[VocabTerm]:
        """Get a vocabulary term by type and canonical name."""
        result = self.session.execute(
            text("""
                SELECT id, vocab_type, canonical_name, nomisma_uri, metadata
                FROM vocab_terms
                WHERE vocab_type = :vtype AND canonical_name = :name
            """),
            {"vtype": vocab_type.value, "name": name}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return VocabTerm(
            id=row[0],
            vocab_type=VocabType(row[1]),
            canonical_name=row[2],
            nomisma_uri=row[3],
            metadata=json.loads(row[4] or "{}")
        )
    
    def save(self, term: VocabTerm) -> VocabTerm:
        """Save or update a vocabulary term."""
        if term.id:
            # Update existing
            self.session.execute(
                text("""
                    UPDATE vocab_terms 
                    SET canonical_name = :name, nomisma_uri = :uri, metadata = :meta
                    WHERE id = :id
                """),
                {
                    "id": term.id,
                    "name": term.canonical_name,
                    "uri": term.nomisma_uri,
                    "meta": json.dumps(term.metadata) if term.metadata else None
                }
            )
            self.session.flush()
            return term
        else:
            # Insert new
            return self._upsert_term(
                term.vocab_type, 
                term.canonical_name, 
                term.nomisma_uri,
                term.metadata
            )
    
    def get_all(
        self, 
        vocab_type: VocabType, 
        limit: int = 1000
    ) -> List[VocabTerm]:
        """Get all vocabulary terms of a given type."""
        result = self.session.execute(
            text("""
                SELECT id, vocab_type, canonical_name, nomisma_uri, metadata
                FROM vocab_terms
                WHERE vocab_type = :vtype
                ORDER BY canonical_name
                LIMIT :limit
            """),
            {"vtype": vocab_type.value, "limit": limit}
        )
        
        terms = []
        for row in result.fetchall():
            terms.append(VocabTerm(
                id=row[0],
                vocab_type=VocabType(row[1]),
                canonical_name=row[2],
                nomisma_uri=row[3],
                metadata=json.loads(row[4] or "{}")
            ))
        return terms
    
    # -------------------------------------------------------------------------
    # Assignment tracking methods
    # -------------------------------------------------------------------------
    
    def record_assignment(
        self,
        coin_id: int,
        field_name: str,
        raw_value: str,
        result: NormalizationResult
    ):
        """Record a vocabulary assignment for audit trail."""
        self.session.execute(
            text("""
                INSERT INTO coin_vocab_assignments 
                (coin_id, field_name, raw_value, vocab_term_id, confidence, method, status, assigned_at)
                VALUES (:coin_id, :field, :raw, :term_id, :conf, :method, :status, datetime('now'))
            """),
            {
                "coin_id": coin_id,
                "field": field_name,
                "raw": raw_value,
                "term_id": result.term.id if result.term else None,
                "conf": result.confidence,
                "method": result.method,
                "status": "pending_review" if result.needs_review else "assigned"
            }
        )
    
    def get_review_queue(
        self, 
        status: str = "pending_review", 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get items needing review."""
        result = self.session.execute(
            text("""
                SELECT cva.id, cva.coin_id, cva.field_name, cva.raw_value, 
                       cva.vocab_term_id, cva.confidence, cva.method,
                       vt.canonical_name as suggested_name
                FROM coin_vocab_assignments cva
                LEFT JOIN vocab_terms vt ON cva.vocab_term_id = vt.id
                WHERE cva.status = :status
                ORDER BY cva.assigned_at DESC
                LIMIT :limit
            """),
            {"status": status, "limit": limit}
        )
        
        return [dict(row._mapping) for row in result.fetchall()]
    
    def approve_assignment(self, assignment_id: int):
        """Approve a pending assignment."""
        self.session.execute(
            text("""
                UPDATE coin_vocab_assignments 
                SET status = 'approved', reviewed_at = datetime('now')
                WHERE id = :id
            """),
            {"id": assignment_id}
        )
    
    def reject_assignment(self, assignment_id: int):
        """Reject a pending assignment."""
        self.session.execute(
            text("""
                UPDATE coin_vocab_assignments 
                SET status = 'rejected', reviewed_at = datetime('now')
                WHERE id = :id
            """),
            {"id": assignment_id}
        )
    
    # -------------------------------------------------------------------------
    # LLM Integration Methods
    # -------------------------------------------------------------------------
    
    def get_by_canonical_str(
        self,
        vocab_type: str,
        canonical_name: str
    ) -> Optional[Union[Issuer, Mint, VocabTerm]]:
        """
        Get vocab term by canonical name (string vocab_type).
        
        Wrapper for get_by_canonical that accepts string types for LLM integration.
        Returns legacy Issuer/Mint for compatibility, or VocabTerm.
        
        Args:
            vocab_type: "issuer", "mint", or "denomination"
            canonical_name: Exact canonical name to match
        
        Returns:
            Issuer, Mint, or VocabTerm if found, None otherwise
        """
        try:
            vtype = VocabType(vocab_type.lower())
        except ValueError:
            logger.warning(f"Invalid vocab_type: {vocab_type}")
            return None
        
        term = self.get_by_canonical(vtype, canonical_name)
        if not term:
            return term
        
        # Return legacy types for compatibility where applicable
        if vtype == VocabType.ISSUER and term.id is not None:
            from src.domain.vocab import IssuerType
            return Issuer(
                id=term.id,
                canonical_name=term.canonical_name,
                nomisma_id=term.nomisma_uri.split("/")[-1] if term.nomisma_uri else "",
                issuer_type=IssuerType(term.metadata.get("issuer_type", "other")),
                reign_start=term.reign_start,
                reign_end=term.reign_end,
            )
        elif vtype == VocabType.MINT and term.id is not None:
            return Mint(
                id=term.id,
                canonical_name=term.canonical_name,
                nomisma_id=term.nomisma_uri.split("/")[-1] if term.nomisma_uri else "",
                active_from=term.metadata.get("active_from"),
                active_to=term.metadata.get("active_to"),
            )
        
        return term
    
    def fuzzy_search(
        self,
        query: str,
        vocab_type: str,
        limit: int = 5,
        min_score: float = 0.5
    ) -> List[FuzzyMatch]:
        """
        Fuzzy search for vocabulary terms using string similarity.
        
        Used as fallback when LLM is unavailable. Combines FTS5 results
        with SequenceMatcher scoring for best matches.
        
        Args:
            query: Search query string
            vocab_type: "issuer", "mint", or "denomination"
            limit: Maximum number of results
            min_score: Minimum similarity score (0.0 to 1.0)
        
        Returns:
            List of FuzzyMatch results sorted by score descending
        """
        if not query or not query.strip():
            return []
        
        try:
            vtype = VocabType(vocab_type.lower())
        except ValueError:
            logger.warning(f"Invalid vocab_type: {vocab_type}")
            return []
        
        query_lower = query.strip().lower()
        
        # First, get FTS5 candidates (broader match)
        fts_results = self.search(vtype, query, limit=limit * 2)
        
        # If FTS5 didn't find anything, try LIKE fallback with broader match
        if not fts_results:
            fts_results = self._search_fallback(vtype, query, limit=limit * 2)
        
        # Also get all terms for comprehensive matching (for short queries)
        if len(query) <= 3:
            all_terms = self.get_all(vtype, limit=200)
        else:
            all_terms = fts_results
        
        # Score each candidate using SequenceMatcher
        scored_matches: List[FuzzyMatch] = []
        seen_names = set()
        
        for term in all_terms:
            if term.canonical_name in seen_names:
                continue
            seen_names.add(term.canonical_name)
            
            # Calculate similarity score
            score = SequenceMatcher(
                None,
                query_lower,
                term.canonical_name.lower()
            ).ratio()
            
            # Boost score for prefix matches
            if term.canonical_name.lower().startswith(query_lower):
                score = min(1.0, score + 0.15)
            
            # Boost score for word boundary matches
            if f" {query_lower}" in f" {term.canonical_name.lower()}":
                score = min(1.0, score + 0.1)
            
            if score >= min_score:
                scored_matches.append(FuzzyMatch(
                    canonical_name=term.canonical_name,
                    score=round(score, 3),
                    vocab_type=vocab_type,
                    vocab_id=term.id,
                ))
        
        # Sort by score descending and limit
        scored_matches.sort(key=lambda m: m.score, reverse=True)
        return scored_matches[:limit]
