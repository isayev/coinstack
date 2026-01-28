# LLM suggestions for legends, descriptions, and identify – implementation plan

This document is a **step-by-step implementation plan** so the LLM can suggest:

1. **Legends and exergue** – from **POST /api/v2/llm/legend/transcribe** (transcribe legends from coin image).
2. **Descriptions** – obverse/reverse descriptions from transcribe (if added) or from **POST /api/v2/llm/identify**.
3. **Identify** – ruler, denomination, mint, date range, descriptions, and suggested references from **POST /api/v2/llm/identify** (identify coin from image).

The goal is to **store** these as suggestions on the coin, **show** them in the LLM review queue, and **apply** them on approve (same pattern as rarity and references).

---

## Scope

| Source | Fields suggested | Stored as | Applied to |
|--------|------------------|-----------|------------|
| **legend/transcribe** | obverse_legend, reverse_legend, exergue, obverse_legend_expanded, reverse_legend_expanded | `llm_suggested_design` | `coin.design` |
| **identify** | ruler → issuer, denomination, mint, date_range → year_start/year_end, obverse_description, reverse_description, suggested_references | `llm_suggested_attribution` + `llm_suggested_references` (merge), obverse/reverse_description in `llm_suggested_design` | `coin.attribution`, `coin.denomination`, `coin.design`, refs |

We use two new JSON columns:

- **llm_suggested_design** – `{ obverse_legend?, reverse_legend?, exergue?, obverse_description?, reverse_description?, obverse_legend_expanded?, reverse_legend_expanded? }`. Filled by transcribe and/or identify.
- **llm_suggested_attribution** – `{ issuer?, mint?, denomination?, year_start?, year_end? }`. Filled by identify only.

Identify’s `suggested_references` are merged into the existing **llm_suggested_references** (no schema change for refs).

---

## Prerequisites

- Existing flow for rarity and references: `llm_suggested_rarity`, `llm_suggested_references`, **GET /api/v2/llm/review**, **POST /api/v2/llm/review/{id}/approve**, **POST /api/v2/llm/review/{id}/dismiss**.
- Domain: `Design(obverse_legend, obverse_description, reverse_legend, reverse_description, exergue)`, `Attribution(issuer, mint, year_start, year_end)`, `Coin.denomination`.
- ORM: flat columns `obverse_legend`, `obverse_description`, `reverse_legend`, `reverse_description`, `exergue` on `CoinModel`.
- **docs/ENRICHMENT-CONSOLIDATION-ASSESSMENT.md** – field→domain mapping (e.g. design → `Design(...)`, attribution → `Attribution(...)`).

---

## Phase 1 – Storage and domain

### Step 1.1 – Add DB columns (no migration script; optional backup)

Add two nullable text columns to `coins_v2`:

- `llm_suggested_design` – Text/JSON. Shape: `{ obverse_legend?, reverse_legend?, exergue?, obverse_description?, reverse_description?, obverse_legend_expanded?, reverse_legend_expanded? }`.
- `llm_suggested_attribution` – Text/JSON. Shape: `{ issuer?, mint?, denomination?, year_start?, year_end? }`.

**Where:** `backend/src/infrastructure/persistence/orm.py` (e.g. next to `llm_suggested_references`).

**Options:**

- **A)** Add columns in ORM and create/run a small migration (Alembic or one-off script).
- **B)** Add columns in ORM and document that “create new DB / re-run from seed” is acceptable (per your “no DB migration; create new one” preference, you may add columns manually once or via a one-off SQL script).

**Deliverable:** `CoinModel` has `llm_suggested_design` and `llm_suggested_attribution` (both `Mapped[Optional[str]]`).

### Step 1.2 – Domain and repository

- **Domain (`backend/src/domain/coin.py`):**  
  On `Coin`, add:
  - `llm_suggested_design: Optional[Dict[str, Any]] = None`
  - `llm_suggested_attribution: Optional[Dict[str, Any]] = None`
- **Repository (`backend/src/infrastructure/repositories/coin_repository.py`):**  
  In `_to_domain` / `_to_model` (or equivalent), read/write `llm_suggested_design` and `llm_suggested_attribution` as JSON (same pattern as `llm_suggested_references` / `llm_suggested_rarity`).

**Deliverable:** Domain `Coin` and repository round-trip both new fields.

### Step 1.3 – Coins API exposure

- **V2 API (`backend/src/infrastructure/web/routers/v2.py`):**  
  Add `llm_suggested_design` and `llm_suggested_attribution` to the coin response and to the update-coin path (read from domain, merge on update so other code paths do not strip them).

**Deliverable:** GET/PUT coin and list responses include the two new fields when present.

---

## Phase 2 – “Save as suggestions” entry points

### Step 2.1 – Transcribe for coin (legend/transcribe + persist)

**Goal:** For a given coin, run legend/transcribe on its primary image and store the result in `llm_suggested_design`.

**Options:**

- **A) New endpoint:** `POST /api/v2/llm/legend/transcribe/coin/{coin_id}` – load coin, resolve primary image, call `llm_service.transcribe_legend(image_b64)`, map response into `llm_suggested_design`, save, set `llm_enriched_at`.
- **B) Extend existing:** `POST /api/v2/llm/legend/transcribe` – body accepts optional `coin_id` and optional `image_b64`. If `coin_id` is set, load coin and primary image; if `image_b64` is missing, derive it from the coin’s primary image (fetch URL or read file, then base64). Call transcribe, then persist to that coin.

**Response:** Either return the same `LegendTranscribeResponse` as today, or a small wrapper that adds `saved_to_coin: true` and `coin_id` when suggestions were stored.

**Backend tasks:**

1. Resolve coin primary image to something the LLM can consume (e.g. URL → HTTP fetch → base64, or stored path → read file → base64). Reuse or add a small helper used by identify-for-coin later.
2. Call `llm_service.transcribe_legend(image_b64)`.
3. Build design JSON from response:
   - `obverse_legend`, `reverse_legend`, `exergue`, `obverse_legend_expanded`, `reverse_legend_expanded`.
4. Write into `coin.llm_suggested_design` (merge with existing if you support multiple sources; else overwrite). Set `llm_enriched_at`. Commit.

**Deliverable:** One way to call legend/transcribe in a “coin context” and have design suggestions stored on that coin.

### Step 2.2 – Identify for coin (identify + persist)

**Goal:** For a given coin, run identify on its primary image and store attribution + descriptions + merge suggested_references into `llm_suggested_references`.

**Options:**

- **A) New endpoint:** `POST /api/v2/llm/identify/coin/{coin_id}`.
- **B) Extend existing:** `POST /api/v2/llm/identify` – body accepts optional `coin_id` and optional `image_b64`. If `coin_id` set, load primary image when `image_b64` missing; run identify; persist to that coin.

**Backend tasks:**

1. Reuse the same “resolve coin primary image → base64” as in Step 2.1.
2. Call `llm_service.identify_coin(image_b64)`.
3. Map response into storage:
   - **llm_suggested_attribution:**  
     `issuer` ← ruler (or keep both keys and use `issuer` when applying), `mint`, `denomination`, `year_start`/`year_end` parsed from `date_range` if possible (otherwise leave null).
   - **llm_suggested_design:**  
     Set or merge `obverse_description`, `reverse_description` from identify. (Legends from identify are not in the current identify response; if you add them later, merge here.)
   - **llm_suggested_references:**  
     Merge `result.suggested_references` into existing list, dedupe, then assign back to coin.
4. Set `llm_enriched_at`, commit.

**Deliverable:** One way to call identify in a “coin context” and have attribution + design descriptions + refs stored as suggestions on that coin.

---

## Phase 3 – Review queue and dismiss

### Step 3.1 – Include design and attribution in review queue

- **GET /api/v2/llm/review:**  
  Extend the “coins with pending LLM suggestions” filter to include coins where `llm_suggested_design IS NOT NULL OR llm_suggested_attribution IS NOT NULL` (in addition to references and rarity).
- **LLMSuggestionItem:**  
  Add optional fields, e.g.:
  - `suggested_design: Optional[LlmSuggestedDesign] = None`  
    (e.g. obverse_legend, reverse_legend, exergue, obverse_description, reverse_description, obverse_legend_expanded, reverse_legend_expanded).
  - `suggested_attribution: Optional[LlmSuggestedAttribution] = None`  
    (e.g. issuer, mint, denomination, year_start, year_end).

**Backend:** In the review handler, when building each item, parse `llm_suggested_design` / `llm_suggested_attribution` from the row and attach to `LLMSuggestionItem`. Frontend and API contract can use the same shape as the JSON (or a flatter view for UI).

**Deliverable:** Review queue returns items that can have `suggested_design` and/or `suggested_attribution` in addition to `suggested_references` and `rarity_info`.

### Step 3.2 – Dismiss design and attribution

- **POST /api/v2/llm/review/{coin_id}/dismiss:**  
  Add query params (or body flags) e.g. `dismiss_design` and `dismiss_attribution` (default true when “dismiss all” is intended). When set, run:
  - `UPDATE coins_v2 SET llm_suggested_design = NULL WHERE id = :coin_id` (when dismiss_design),
  - same for `llm_suggested_attribution` when dismiss_attribution.

**Deliverable:** Dismiss can clear design and attribution suggestions without applying them.

---

## Phase 4 – Apply on approve

### Step 4.1 – Field→domain mapping for design and attribution

Use the same pattern as in **docs/ENRICHMENT-CONSOLIDATION-ASSESSMENT.md**: no raw `setattr`; build new value objects and `replace(coin, …)`.

- **suggested_design → Design**
  - Read `llm_suggested_design` from coin.
  - Build `Design(obverse_legend=…, obverse_description=…, reverse_legend=…, reverse_description=…, exergue=…)` using suggested values, falling back to existing `coin.design` for any missing key.
  - `updated = replace(coin, design=new_design)`.
- **suggested_attribution → Attribution + denomination**
  - Read `llm_suggested_attribution`.
  - Build `Attribution(issuer=…, mint=…, year_start=…, year_end=…)` from suggested values, keeping existing where not provided.
  - If suggested has `denomination`, set `updated.denomination` (or equivalent on your aggregate).
  - `updated = replace(coin, attribution=new_attribution, denomination=…)`.

**Note:** Repository and ORM today use flat columns for design/attribution. The “apply” logic can either (a) work on the domain `Coin` and call `repo.save(updated)` so the repository writes all fields, or (b) run a small inline “patch” that updates only design/attribution columns from the suggestion blobs. (a) is preferable for consistency with existing approve and with ENRICHMENT-CONSOLIDATION-ASSESSMENT.

### Step 4.2 – Extend approve endpoint

- **POST /api/v2/llm/review/{coin_id}/approve:**  
  After applying rarity and references (existing behavior), do:
  1. If `coin.llm_suggested_design` is set:
     - Parse JSON, build new `Design` (merge with existing design), assign to coin, persist.
     - Set `coin.llm_suggested_design = None`.
  2. If `coin.llm_suggested_attribution` is set:
     - Parse JSON, build new `Attribution` and set `denomination` if present, persist.
     - Set `coin.llm_suggested_attribution = None`.

Return summary still includes e.g. `applied_rarity`, `applied_references`; add `applied_design: bool` and `applied_attribution: bool` (or counts) so the frontend can show “Applied design and attribution” in toasts.

**Deliverable:** Approve applies design and attribution suggestions and clears the two new columns.

---

## Phase 5 – Frontend

### Step 5.1 – Types and API client

- **Types:** Extend `LLMSuggestionItem` (or equivalent) with `suggested_design` and `suggested_attribution` with the same shape as backend (obverse_legend, reverse_legend, exergue, obverse_description, reverse_description; issuer, mint, denomination, year_start, year_end).
- **API:** Ensure GET `/api/v2/llm/review` and GET coin are typed so that `llm_suggested_design` / `llm_suggested_attribution` (and their review-shape equivalents) are recognized.

### Step 5.2 – Triggers “save as suggestions”

- **Transcribe for coin:**  
  Add UI that calls the “transcribe for this coin” endpoint (e.g. from coin detail or review row). Options: “Transcribe legends” on the coin detail page, or an action on the review queue that runs transcribe for that coin and then refetches the queue.
- **Identify for coin:**  
  Same idea: “Identify from image” for this coin (e.g. on coin detail, using the coin’s primary image). Call the “identify for coin” endpoint; on success, refetch review queue or show “Suggestions saved; review in AI Suggestions”.

### Step 5.3 – Review queue UI

- **AI Review tab / row:**  
  For each item, if `suggested_design` or `suggested_attribution` is present, render a short summary (e.g. “Legends: obv/reverse/exergue”, “Attribution: issuer, mint, dates”) and keep showing existing “references” and “rarity” when present.
- **Approve / Dismiss:**  
  Approve already calls the same approve endpoint; no change beyond possibly showing “Design and attribution applied” when the response says so. Dismiss: if you add “dismiss design only” / “dismiss attribution only” in the UI, pass the new flags; otherwise keep “dismiss all” and pass dismiss_design / dismiss_attribution as true.

### Step 5.4 – Coin detail

- Optional: on the coin detail page, show pending “LLM design” and “LLM attribution” in a small “Pending suggestions” block (or link to “Review in AI Suggestions”) when `llm_suggested_design` or `llm_suggested_attribution` is set.

**Deliverable:** User can trigger transcribe/identify for a coin, see design/attribution in the review queue, and approve or dismiss them.

---

## Phase 6 – Docs and tests

### Step 6.1 – Docs

- **docs/ai-guide/07-API-REFERENCE.md:** Document:
  - New or extended endpoints: transcribe-for-coin, identify-for-coin (or extended bodies/params).
  - New fields on coin: `llm_suggested_design`, `llm_suggested_attribution`.
  - GET /api/v2/llm/review: new fields `suggested_design`, `suggested_attribution` on items.
  - POST /api/v2/llm/review/{id}/dismiss: new params `dismiss_design`, `dismiss_attribution`.
  - POST /api/v2/llm/review/{id}/approve: new response fields `applied_design`, `applied_attribution`.
- **docs/LLM-SUGGESTABLE-FIELDS-ANALYSIS.md:** Update the “Can the LLM suggest this?” table and the legend/transcribe and identify sections to state that design and attribution are stored and applied when using the “for coin” flows.

### Step 6.2 – Tests

- **Backend**
  - Transcribe-for-coin: with coin_id and mocked primary image → transcribe called, `llm_suggested_design` updated.
  - Identify-for-coin: with coin_id and mocked image → identify called, `llm_suggested_attribution` and `llm_suggested_references` updated; descriptions in `llm_suggested_design` when implemented.
  - Review queue: coin with only `llm_suggested_design` (or only `llm_suggested_attribution`) appears and has the right item shape.
  - Approve: applying design merges into `coin.design` and clears `llm_suggested_design`; applying attribution updates `coin.attribution` and denomination and clears `llm_suggested_attribution`.
  - Dismiss: dismiss_design / dismiss_attribution clear the corresponding column.
- **Frontend (optional but useful)**
  - Review row shows design/attribution summary when present.
  - Approve success toast reflects “design/attribution applied” when relevant.

**Deliverable:** API and behavior described in docs and covered by tests.

---

## Implementation order (summary)

| Order | Phase | Steps | Dependency |
|-------|--------|--------|------------|
| 1 | Storage & domain | 1.1 DB columns, 1.2 domain + repo, 1.3 v2 API exposure | — |
| 2 | Save-as-suggestions | 2.1 transcribe-for-coin, 2.2 identify-for-coin | 1; need “primary image → base64” helper |
| 3 | Review & dismiss | 3.1 review queue includes design/attribution, 3.2 dismiss params | 1 |
| 4 | Apply | 4.1 field→domain mapping, 4.2 extend approve | 1 |
| 5 | Frontend | 5.1 types/API, 5.2 triggers, 5.3 review UI, 5.4 coin detail (optional) | 2, 3, 4 |
| 6 | Docs & tests | 6.1 API/analysis docs, 6.2 backend (and optionally frontend) tests | 1–5 |

---

## Design choices to fix early

1. **Transcribe/identify “for coin” API shape**  
   New route per action (e.g. `/legend/transcribe/coin/{id}`) vs optional `coin_id` on existing routes. New routes keep existing clients unchanged and make “for coin” explicit.
2. **Primary image resolution**  
   Where images live (table `coin_images` with URLs vs file paths), and how the backend turns that into base64 for the LLM (e.g. HTTP GET vs file read). Define once and reuse for both transcribe and identify.
3. **date_range → year_start/year_end**  
   Identify returns `date_range: Optional[str]`. Decide rule for parsing (e.g. “ca. 260–268” → year_start=260, year_end=268; “268” → both 268; no parse → leave null) and document it.
4. **Overwrite vs merge**  
   When saving `llm_suggested_design` from transcribe and later from identify, choose: overwrite whole blob, or merge by key (e.g. identify only sets obverse_description/reverse_description and leaves legends from transcribe). Merging is more flexible but slightly more logic.

---

## File checklist (for implementers)

| Area | Files to touch |
|------|------------------|
| Persistence | `backend/src/infrastructure/persistence/orm.py` |
| Domain | `backend/src/domain/coin.py` |
| Repository | `backend/src/infrastructure/repositories/coin_repository.py` |
| Coins API | `backend/src/infrastructure/web/routers/v2.py` |
| LLM routes | `backend/src/infrastructure/web/routers/llm.py` (transcribe-for-coin, identify-for-coin, review, dismiss, approve) |
| Frontend types | `frontend/src/types/audit.ts` (or equivalent for LLM suggestions) |
| Frontend API / hooks | `frontend/src/hooks/useAudit.ts` (or useLLM), `frontend/src/api/` |
| Review UI | `frontend/src/components/review/AIReviewTab.tsx`, `frontend/src/pages/ReviewQueuePage.tsx` |
| Coin detail / actions | Page or component where “Transcribe legends” / “Identify from image” are triggered |
| Docs | `docs/ai-guide/07-API-REFERENCE.md`, `docs/LLM-SUGGESTABLE-FIELDS-ANALYSIS.md` |
| Tests | `backend/tests/` for new endpoints and approve/dismiss logic |

This plan keeps the same “suggest → review → approve/dismiss” pattern as rarity and references, and adds legends, descriptions, and identify-based attribution in a consistent way.
