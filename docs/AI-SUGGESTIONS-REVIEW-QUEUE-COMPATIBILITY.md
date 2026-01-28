# AI Suggestions & Review Queue – API/Schema Compatibility

**Date**: 2026-01-27  
**Scope**: “AI Suggestions” and “Vocabulary Review” queues used by Review Center, Audit page, and Review Queue page.

---

## 1. Two Queues in Scope

| Queue | Purpose | Frontend entry points | Backend API |
|-------|---------|----------------------|-------------|
| **Vocabulary Review** | Pending issuer/mint/denomination assignments from normalization | ReviewQueuePage, VocabularyReviewTab, Review Center “Vocabulary” tab | `GET/POST /api/v2/vocab/review*` |
| **LLM Suggestions (AI Suggestions)** | Pending catalog references & rarity from historical context / LLM | AuditPage, LLMReviewTab, AIReviewTab, Review Center “AI Suggestions” tab | `GET/POST /api/v2/llm/review*` |

---

## 2. Vocabulary Review Queue

### 2.1 API

- **List**: `GET /api/v2/vocab/review`
  - Query: `status` (e.g. `pending_review`, `assigned`, `approved`, `rejected`), `limit` (1–200, default 50).
- **Approve**: `POST /api/v2/vocab/review/{assignment_id}/approve`
- **Reject**: `POST /api/v2/vocab/review/{assignment_id}/reject`

### 2.2 Response shape (list)

Backend returns `List[ReviewQueueItem]`:

```ts
{
  id: number;           // assignment id
  coin_id: number;
  field_name: string;   // "issuer" | "mint" | "denomination"
  raw_value: string;
  vocab_term_id: number | null;
  confidence: number | null;
  method: string | null; // "exact" | "exact_ci" | "fts" | "nomisma" | "llm" | "manual"
  suggested_name: string | null;
}
```

Frontend (`ReviewQueuePage`, `VocabularyReviewTab`) uses the same shape. **Compatible.**

### 2.3 Schema / data source

- **Table**: `coin_vocab_assignments` (see `020_vocab_v3.sql`).
- **Filled by**: bulk normalization (vocab “bulk” flow). Each low-confidence or ambiguous assignment is stored with `status='pending_review'`.

### 2.4 Compatibility verdict

- **API**: Paths and request/response match frontend usage. **Compatible.**
- **Schema**: Depends on Vocab V3 migration and bulk normalize:
  - If `coin_vocab_assignments` (and `vocab_terms`, FTS, etc.) were never created → run `020_vocab_v3.sql` or `migrate_vocab_v3.py`.
  - If the table exists but the queue is always empty → **re-run bulk normalize** from the Collection (or wherever the “Bulk normalize” action is) so new rows are written with `status='pending_review'`.

**Re-run needed only to populate data**, not to “fix” the API or schema.

---

## 3. LLM Suggestions (AI Suggestions) Queue

### 3.1 API

- **List**: `GET /api/v2/llm/review`
  - Query: `limit` (1–500, default 100).
- **Dismiss**: `POST /api/v2/llm/review/{coin_id}/dismiss`
  - Query: `dismiss_references` (default true), `dismiss_rarity` (default true), `dismiss_design` (default true), `dismiss_attribution` (default true).
- **Approve**: `POST /api/v2/llm/review/{coin_id}/approve` — applies pending rarity, references, design, and attribution to the coin and clears suggestion columns.

### 3.2 Response shape (list)

Backend returns `LLMReviewQueueResponse`:

```ts
{
  items: LLMSuggestionItem[];
  total: number;
}

interface LLMSuggestionItem {
  coin_id: number;
  issuer, denomination, mint, category, year_start, year_end: nullable;
  obverse_legend, reverse_legend: nullable;
  existing_references: string[];
  suggested_references: string[];
  validated_references: CatalogReferenceValidation[];
  rarity_info: LLMRarityInfo | null;
  suggested_design: LlmSuggestedDesign | null;
  suggested_attribution: LlmSuggestedAttribution | null;
  enriched_at: string | null;
}
```

Frontend types (`@/types/audit`: `LLMSuggestionItem`, `LLMReviewQueueResponse`, `LlmSuggestedDesign`, `LlmSuggestedAttribution`, `CatalogReferenceValidation`, `LLMRarityInfo`) align with backend Pydantic models. **Compatible.**

### 3.3 Schema / data source

- **Source**: `coins_v2` columns `llm_suggested_references`, `llm_suggested_rarity`, `llm_suggested_design`, `llm_suggested_attribution`, `llm_enriched_at`. No separate “queue” table.
- **Filled by**: Historical context generation (LLM) per coin. When the LLM returns new references, rarity, design, or attribution, they are written into these fields. Transcribe/identify endpoints also write design/attribution.

### 3.4 Compatibility verdict

- **API**: Paths and request/response match. **Compatible.**
- **Schema**: Uses existing `coins_v2` fields. No extra migration.
- **Re-run**: Nothing to “re-run” for compatibility. New suggestions appear when you run **“Generate context”** (or equivalent) on coins; the queue is “live” over current DB content.

---

## 4. Doc vs implementation

- **07-API-REFERENCE.md** currently documents:
  - `GET /api/v2/vocab/review-queue` and `POST /api/v2/vocab/review-queue/{item_id}/approve|reject`
- **Actual implementation** (and frontend) use:
  - `GET /api/v2/vocab/review`, `POST /api/v2/vocab/review/{assignment_id}/approve|reject`

So the **documented paths are wrong**. The implementation is the source of truth; the doc should be updated to use `/api/v2/vocab/review` and `assignment_id` (see below).

---

## 5. Summary

| Queue | API compatible? | Schema/backend match? | Re-run or migration? |
|-------|-----------------|------------------------|------------------------|
| **Vocabulary Review** | Yes | Yes, if Vocab V3 migration applied | Run bulk normalize to populate; run vocab v3 migration if tables missing |
| **LLM Suggestions** | Yes | Yes | No re-run for compatibility; run “Generate context” to get new suggestions |

**Conclusion**: Both “AI Suggestions” (LLM) and the Vocabulary Review queue are compatible with the current API and schema. No backend or frontend change is required for compatibility.  
- For **Vocabulary Review**: ensure `coin_vocab_assignments` exists (migrate if not) and run bulk normalize to fill the queue.  
- For **LLM Suggestions**: no schema or job re-run is needed; just generate context on coins to see suggestions.

---

## 6. References

- Backend: `backend/src/infrastructure/web/routers/vocab.py` (vocab review), `llm.py` (LLM review).
- Frontend: `ReviewQueuePage.tsx`, `VocabularyReviewTab.tsx`, `LLMReviewTab.tsx`, `useAudit.ts` (`useLLMSuggestions`, `useDismissLLMSuggestion`).
- Types: `frontend/src/types/audit.ts` (LLM types); review queue item shape in `ReviewQueuePage` / `VocabularyReviewTab`.
- Schema: `020_vocab_v3.sql`, `coin_vocab_assignments`; `coins_v2.llm_suggested_*`, `llm_enriched_at`.
