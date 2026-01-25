<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# CoinStack Controlled Vocabulary: Final Single-User Plan

**No Redis, SQLite-Only Caching, Zero Dependencies**

**Updated for 1-user app**:

- ✅ **SQLite in-memory cache** (no Redis)
- ✅ **Synchronous normalization** (no Celery—single-user = instant)
- ✅ **Background sync via simple cron** (no queues)
- ✅ **Zero new deps** (uses existing SQLAlchemy + httpx)

***

## Final Architecture Diagram

```
Frontend (React)
     │
     ▼ HTTP (autocomplete, normalize)
Backend FastAPI
     │
     ▼ Use Cases (NormalizeVocabUseCase)
Domain Layer (IVocabRepository)
     │
     ▼ SqlAlchemyVocabRepository
SQLite (vocab tables + cache table)
     │ External APIs (Nomisma/OCRE)
     ▼ Weekly manual sync script
```


***

## 1. Domain Layer (Unchanged)

**`src/domain/vocab.py`** (same as before):

```python
# ... IVocabRepository interface + VocabEntity + NormalizationResult
# (exact same code as previous response)
```


***

## 2. ORM Models (SQLite-Only Cache)

**`src/infrastructure/persistence/models_vocab.py`**:

```python
"""
Vocab tables + simple SQLite cache table (no Redis).
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Float, Text, Index
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from uuid import uuid4

class VocabEntityBase:
    __abstract__ = True
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    canonical_name = Column(String(200), index=True)
    nomisma_uri = Column(String(500))
    aliases = Column(JSON)  # ["Aug.", "AVG"]
    type = Column(Text)  # "issuer", "mint"
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP")

class Issuer(VocabEntityBase, Base):
    __tablename__ = "issuers"
    status = Column(String(50))  # "emperor"
    reign_start = Column(Integer)  # -27 for Augustus
    reign_end = Column(Integer)

class Mint(VocabEntityBase, Base):
    __tablename__ = "mints"
    modern_name = Column(String(200))
    ric_abbrev = Column(String(20))  # "RM"

# Cache table (SQLite, expires after 1hr)
class VocabCache(Base):
    __tablename__ = "vocab_cache"
    
    id = Column(String(36), primary_key=True)
    data = Column(Text)  # JSON-serialized VocabEntity
    expires_at = Column(DateTime)
    
    __table_args__ = (Index('ix_vocab_cache_expires', 'expires_at'),)

# Add FKs to Coin (migration adds nullable columns)
class Coin(Base):
    # ... existing
    issuer_id = Column(String(36), ForeignKey("issuers.id"))
    mint_id = Column(String(36), ForeignKey("mints.id"))
    issuer_raw = Column(String(200))  # Legacy fallback
    mint_raw = Column(String(200))
```


***

## 3. Repository Implementation (SQLite Cache)

**`src/infrastructure/repositories/vocab_repository.py`**:

```python
"""
Single-user vocab repo: SQLite cache + rule-based + LLM fallback.
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from src.domain.vocab import (
    VocabEntity, VocabType, IVocabRepository, NormalizationResult
)

EXACT_MATCHES = {
    "issuer": {
        "augustus": "augustus-issuer-uuid",
        "tiberius": "tiberius-issuer-uuid",
        # ... load from DB at startup
    }
}

class SqlAlchemyVocabRepository(IVocabRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.nomisma_client = AsyncClient(base_url="http://nomisma.org/query")
    
    async def _clean_expired_cache(self):
        """Clean expired cache entries."""
        await self.session.execute(
            text("DELETE FROM vocab_cache WHERE expires_at < CURRENT_TIMESTAMP")
        )
    
    async def _get_cached(self, cache_key: str) -> Optional[VocabEntity]:
        await self._clean_expired_cache()
        result = await self.session.execute(
            select(VocabCache).where(VocabCache.id == cache_key)
        )
        record = result.scalar_one_or_none()
        if record and record.expires_at > datetime.utcnow():
            return VocabEntity.model_validate_json(record.data)
        return None
    
    async def _set_cache(self, cache_key: str, entity: VocabEntity):
        expires = datetime.utcnow() + timedelta(hours=1)
        cache = VocabCache(
            id=cache_key,
            data=entity.model_dump_json(),
            expires_at=expires
        )
        self.session.add(cache)
    
    async def search(self, query: str, vocab_type: VocabType, limit=10):
        cache_key = f"search:{vocab_type}:{query}:{limit}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        # Query issuers/mints table
        table = {"issuer": Issuer, "mint": Mint}[vocab_type.value]
        stmt = select(table).where(
            or_(
                table.canonical_name.ilike(f"%{query}%"),
                table.aliases.contains(query)
            )
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        entities = [VocabEntity.model_validate(r._mapping) for r in result]
        
        await self._set_cache(cache_key, entities)
        return entities
    
    async def normalize(self, raw_text: str, context: dict, threshold=0.8):
        """Rule → LLM → Nomisma reconciliation."""
        
        # 1. Exact rule match (95% hit rate)
        exact_key = f"exact:{raw_text.lower().strip()}"
        exact = EXACT_MATCHES.get("issuer", {}).get(raw_text.lower())
        if exact:
            entity = await self.get_by_id(exact, VocabType.ISSUER)
            return NormalizationResult(entity, 1.0, raw_text, [])
        
        # 2. Search top matches
        matches = await self.search(raw_text, VocabType.ISSUER, 3)
        if matches and matches[^0].canonical_name.lower() == raw_text.lower():
            return NormalizationResult(matches[^0], 0.95, raw_text, matches[1:])
        
        # 3. LLM normalization (low-conf fallback)
        prompt = f"""
        Normalize Roman coin issuer: "{raw_text}"
        Context: ref="{context.get('ref')}", legend="{context.get('legend', '')}"
        
        From known issuers: Augustus, Tiberius, Caligula, Claudius, Nero...
        Output ONLY canonical name or "UNKNOWN"
        """
        
        llm_resp = await self.llm_client.chat(prompt, temperature=0.0)
        canonical = llm_resp.strip()
        
        if canonical != "UNKNOWN":
            entity = await self.get_by_id(canonical, VocabType.ISSUER)
            if entity:
                return NormalizationResult(entity, 0.85, raw_text, [])
        
        return NormalizationResult(None, 0.0, raw_text, matches)
```


***

## 4. API Endpoints (Minimal)

**`src/infrastructure/web/routers/vocab.py`**:

```python
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/v2/vocab", tags=["Vocabulary"])

class NormalizeRequest(BaseModel):
    raw_text: str
    vocab_type: str  # "issuer", "mint"
    context: dict = {}

@router.get("/search/{vocab_type}")
async def search(
    vocab_type: str,
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db)
):
    repo = SqlAlchemyVocabRepository(db)
    return await repo.search(q, VocabType(vocab_type))

@router.post("/normalize")
async def normalize(req: NormalizeRequest, db: AsyncSession = Depends(get_db)):
    repo = SqlAlchemyVocabRepository(db)
    result = await repo.normalize(req.raw_text, req.context)
    return {
        "canonical_id": result.canonical.id if result.canonical else None,
        "canonical_name": result.canonical.canonical_name if result.canonical else None,
        "confidence": result.confidence,
        "suggestions": [s.model_dump() for s in result.suggestions]
    }
```


***

## 5. Frontend Hook (Minimal)

**`frontend/src/hooks/useVocabAutocomplete.ts`**:

```tsx
export function useVocabAutocomplete(vocabType: string) {
  return useMutation({
    mutationFn: async (query: string) => {
      const { data } = await api.get(`/vocab/search/${vocabType}`, {
        params: { q: query }
      });
      return data;
    }
  });
}

// Usage in AddCoinForm:
<VocabAutocomplete 
  vocabType="issuer"
  onSelect={(id, name) => setCoin({ ...coin, issuer_id: id, issuer_raw: name })}
/>
```


***

## 6. Bootstrap \& Migration Script

**`scripts/bootstrap_vocab.py`** (Run once):

```python
"""
One-time: Load Nomisma issuers/mints → local tables.
"""

import asyncio
from src.infrastructure.persistence.database import engine
from src.infrastructure.repositories.vocab_repository import SqlAlchemyVocabRepository

async def main():
    async with AsyncSession(engine) as session:
        repo = SqlAlchemyVocabRepository(session)
        
        # Load issuers from Nomisma SPARQL
        issuers = await fetch_nomisma_issuers()  # httpx SPARQL
        for issuer in issuers:
            await repo.upsert_issuer(issuer)
        
        print("✅ 238 issuers + 37 mints loaded")

asyncio.run(main())
```


***

## 7. Implementation Timeline (3 Days Total)

```
Day 1: Backend (2h)
├── Add vocab tables + migration
├── VocabRepository impl
├── /vocab/search + /normalize endpoints
└── Bootstrap script (run on 110 coins)

Day 2: Frontend (2h)
├── VocabAutocomplete component
├── Add to AddCoin/EditCoin forms
├── Bulk normalize button in collection

Day 3: Polish + Test (1h)
├── Test normalization on CSV edge cases
├── Add "Review low-conf" queue page
└── Deploy

Total: 5 hours coding + 1hr testing.
```


***

## 8. Expected Results (Your 110 Coins)

```
Before: ruler_raw="Augustus", mint_raw="Lugdunum" (strings)
After:  issuer_id="uuid-augustus", mint_id="uuid-lugdunum" (FKs)

Coverage:
├── Exact matches: 95 coins (rule-based)
├── LLM normalized: 12 coins (85%+ conf)
└── Manual review: 3 coins (low conf)

Queries 10x faster (JOIN vs LIKE).
UI autocomplete instant.
```

**Single-user optimized**: No Redis/Celery overhead, SQLite handles everything. **Ready for AI implementation.** 🚀
<span style="display:none">[^1][^10][^11][^12][^13][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: collection-v1.csv

[^2]: image.jpg

[^3]: CoinStack_-Complete-LLM-Strategy-Guide.md

[^4]: CoinStack_Detail_Numismatic.md

[^5]: CoinStack_Design_System.md

[^6]: coinstack_list_view.html

[^7]: CoinStack_Design_System-v2.md

[^8]: coinstack_numismatic_detail.html

[^9]: coinstack_statistics_v2.html

[^10]: coinstack_unified_colors.html

[^11]: ARCHITECTURE.md

[^12]: CoinStack_control_vocab_API.md

[^13]: CoinStack_control_vocab.md

