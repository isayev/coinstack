# LLM-Suggestable Fields – Column-by-Column Analysis

This document analyzes, **column by column**, which fields the LLM can suggest, where they are stored, and whether they are applied on approve. It covers:

1. **LLM review queue item** (`LLMSuggestionItem`) – every column and its role
2. **Other LLM endpoints** that return coin-related data – each endpoint and each output “column”

---

## 1. LLM Review Queue Item (`LLMSuggestionItem`) – Column by Column

The review queue is built from **GET /api/v2/llm/review**. Each item is an `LLMSuggestionItem`. **Stored suggestions** on the coin are: `llm_suggested_references`, `llm_suggested_rarity`, **`llm_suggested_design`**, and **`llm_suggested_attribution`**. Everything else is either context (current coin) or derived for display.

| Column | Stored as suggestion on coin? | Applied on approve? | Exposed in API? | Source / notes |
|--------|-------------------------------|---------------------|-----------------|----------------|
| **coin_id** | — | — | ✅ GET /api/v2/llm/review, GET /api/v2/coins/{id} | Primary key; identifies the coin. |
| **issuer** | ❌ No | ❌ No | ✅ In review item and in coin response | **Context:** current coin attribution, from `coins_v2.issuer`. Display only in queue. |
| **denomination** | ❌ No | ❌ No | ✅ In review item and in coin response | **Context:** current coin, from DB. Display only. |
| **mint** | ❌ No | ❌ No | ✅ In review item and in coin response | **Context:** current coin, from DB. Display only. |
| **year_start** | ❌ No | ❌ No | ✅ In review item and in coin response | **Context:** current coin attribution. Display only. |
| **year_end** | ❌ No | ❌ No | ✅ In review item and in coin response | **Context:** current coin attribution. Display only. |
| **category** | ❌ No | ❌ No | ✅ In review item and in coin response | **Context:** current coin. Display only. |
| **obverse_legend** | ❌ No | ❌ No | ✅ In review item and in coin response | **Context:** current coin design. Display only. |
| **reverse_legend** | ❌ No | ❌ No | ✅ In review item and in coin response | **Context:** current coin design. Display only. |
| **existing_references** | ❌ No | — | ✅ In review item only | **Context:** references already on the coin (from `coin_references` + `reference_types`). Used to show “already in DB” and to derive validated_references. |
| **suggested_references** | ✅ **Yes** (`llm_suggested_references`) | ✅ **Yes** | ✅ GET review, GET coin (as `llm_suggested_references`) | **Suggestions:** from context/generate, identify/coin, or bulk enrichment. Stored as JSON array on coin; on approve → create `reference_types` + `coin_references`, then clear. |
| **validated_references** | ❌ No | — | ✅ In review item only | **Derived:** per-suggestion validation (parsed catalog, match/mismatch, confidence). Built in review handler from suggested_references + coin context. |
| **rarity_info** | ✅ **Yes** (`llm_suggested_rarity`) | ✅ **Yes** | ✅ GET review, GET coin (as `llm_suggested_rarity`) | **Suggestions:** from context/generate or bulk enrichment. Stored as JSON on coin; on approve → `coin.rarity`, `coin.rarity_notes`, then clear. |
| **suggested_design** | ✅ **Yes** (`llm_suggested_design`) | ✅ **Yes** | ✅ GET review, GET coin (as `llm_suggested_design`) | **Suggestions:** from **POST /api/v2/llm/legend/transcribe/coin/{id}** or merged from **POST /api/v2/llm/identify/coin/{id}**. Stored as JSON (obverse_legend, reverse_legend, exergue, obverse/reverse_description, obverse/reverse_legend_expanded); on approve → merge into design fields, then clear. |
| **suggested_attribution** | ✅ **Yes** (`llm_suggested_attribution`) | ✅ **Yes** | ✅ GET review, GET coin (as `llm_suggested_attribution`) | **Suggestions:** from **POST /api/v2/llm/identify/coin/{id}**. Stored as JSON (issuer, mint, denomination, year_start, year_end); on approve → merge into attribution fields, then clear. |
| **enriched_at** | — | — | ✅ In review item | **Metadata:** `llm_enriched_at` on coin; when suggestions were last produced. |

**Summary for review queue:**

- **Stored as suggestion and applied on approve:** `suggested_references` (→ catalog refs), `rarity_info` (→ rarity + rarity_notes), **`suggested_design`** (→ legends, exergue, descriptions, expanded legends), **`suggested_attribution`** (→ issuer, mint, denomination, year_start, year_end).
- **Context/display only (not suggestable in this flow):** issuer, denomination, mint, year_start, year_end, category, obverse_legend, reverse_legend, existing_references.
- **Derived for UI:** validated_references.

---

## 2. Other LLM Endpoints That Can Suggest Coin-Like Data

For each endpoint, we list response “columns” and whether they could be suggestable, and whether they are stored or applied today.

### 2.1 POST /api/v2/llm/context/generate

**Role:** Generate historical context for a coin; this is the main flow that **writes** LLM suggestions to the coin (`llm_suggested_references`, `llm_suggested_rarity`).

| Response field | Could suggest a coin field? | Stored as suggestion today? | Applied on approve? | Notes |
|----------------|-----------------------------|-----------------------------|---------------------|------|
| sections | — | No (narrative only) | — | Analysis text; stored in `historical_significance` / `llm_analysis_sections`. |
| raw_content | — | No (narrative) | — | Stored in `historical_significance`. |
| existing_references | — | No | — | Passed in; not a suggestion. |
| all_llm_citations | — | No | — | All refs LLM cited; used to compute suggested_references. |
| **suggested_references** | ✅ Yes | ✅ Yes | ✅ Yes | New citations not in DB → `llm_suggested_references`. |
| matched_references | — | No | — | Refinement of existing_references. |
| **rarity_info** | ✅ Yes | ✅ Yes | ✅ Yes | → `llm_suggested_rarity`; applied as rarity + rarity_notes. |

So for context/generate, the only “suggestable columns” that are stored and applied are **suggested_references** and **rarity_info**.

---

### 2.2 POST /api/v2/llm/auction/parse

**Role:** Parse auction lot description into structured fields. Used when ingesting lots (e.g. scraped text). Response is **not** stored on a coin as “LLM suggestions”; it is used ad-hoc (e.g. pre-fill import or create flow).

| Response field | Could suggest a coin field? | Stored as suggestion today? | Applied on approve? | Notes |
|----------------|-----------------------------|-----------------------------|---------------------|------|
| issuer | ✅ Yes | ❌ No | ❌ No | Would need e.g. `llm_suggested_issuer` + approve logic. |
| denomination | ✅ Yes | ❌ No | ❌ No | Same. |
| metal | ✅ Yes | ❌ No | ❌ No | Same. |
| mint | ✅ Yes | ❌ No | ❌ No | Same. |
| year_start | ✅ Yes | ❌ No | ❌ No | Same. |
| year_end | ✅ Yes | ❌ No | ❌ No | Same. |
| weight_g | ✅ Yes | ❌ No | ❌ No | Same. |
| diameter_mm | ✅ Yes | ❌ No | ❌ No | Same. |
| obverse_legend | ✅ Yes | ❌ No | ❌ No | Same. |
| obverse_description | ✅ Yes | ❌ No | ❌ No | Same. |
| reverse_legend | ✅ Yes | ❌ No | ❌ No | Same. |
| reverse_description | ✅ Yes | ❌ No | ❌ No | Same. |
| references | ✅ Yes | ❌ No | ❌ No | Could be merged into suggested_references if we had a “save auction parse as suggestions” flow. |
| grade | ✅ Yes | ❌ No | ❌ No | Would need suggest + apply. |

**To support “suggest from auction parse”:** add storage (e.g. per-field or one JSON blob), review UX, and apply logic in an approve step (or reuse an ApplyEnrichmentService-style mapper).

---

### 2.3 POST /api/v2/llm/identify and POST /api/v2/llm/identify/coin/{coin_id}

**Role:** Identify coin from image (ruler, denomination, mint, etc.).

- **POST /api/v2/llm/identify** — Ad-hoc: accepts `image_b64` in body; returns ruler, denomination, mint, date_range, descriptions, suggested_references. **Not** stored on a coin.
- **POST /api/v2/llm/identify/coin/{coin_id}** — “For coin”: uses the coin’s primary image, runs identify, then **stores** results as suggestions on the coin and sets `llm_enriched_at`. Ruler → `llm_suggested_attribution.issuer`; mint, denomination, parsed date_range → year_start/year_end in `llm_suggested_attribution`; obverse/reverse descriptions merged into `llm_suggested_design`; suggested_references merged into `llm_suggested_references`. These are applied on **POST /api/v2/llm/review/{coin_id}/approve**.

| Response field | Could suggest a coin field? | Stored as suggestion (identify/coin)? | Applied on approve? | Notes |
|----------------|-----------------------------|----------------------------------------|---------------------|------|
| ruler | ✅ Yes (→ issuer) | ✅ Yes (`llm_suggested_attribution.issuer`) | ✅ Yes | Via identify/coin. |
| denomination | ✅ Yes | ✅ Yes (`llm_suggested_attribution.denomination`) | ✅ Yes | Via identify/coin. |
| mint | ✅ Yes | ✅ Yes (`llm_suggested_attribution.mint`) | ✅ Yes | Via identify/coin. |
| date_range | ✅ Yes (→ year_start/year_end) | ✅ Yes (parsed into year_start/year_end in `llm_suggested_attribution`) | ✅ Yes | Via identify/coin. |
| obverse_description | ✅ Yes | ✅ Yes (merged into `llm_suggested_design`) | ✅ Yes | Via identify/coin. |
| reverse_description | ✅ Yes | ✅ Yes (merged into `llm_suggested_design`) | ✅ Yes | Via identify/coin. |
| suggested_references | ✅ Yes | ✅ Yes (merged into `llm_suggested_references`) | ✅ Yes | Via identify/coin. |

---

### 2.4 POST /api/v2/llm/legend/expand

**Role:** Expand abbreviated Latin legend. One string in → one string out. No structured “columns” that map to coin fields; caller would put result into e.g. obverse_legend or reverse_legend.

| Response field | Could suggest a coin field? | Stored as suggestion today? | Applied on approve? | Notes |
|----------------|-----------------------------|-----------------------------|---------------------|------|
| expanded | ✅ Yes (legend text) | ❌ No | ❌ No | Typically used inline (paste result into legend field). Could add “suggested_obverse_legend” etc. if product needs it. |

---

### 2.5 POST /api/v2/llm/legend/transcribe and POST /api/v2/llm/legend/transcribe/coin/{coin_id}

**Role:** Transcribe legends from coin image. Returns legend and exergue text.

- **POST /api/v2/llm/legend/transcribe** — Ad-hoc: accepts `image_b64` in body; returns obverse/reverse legend, exergue, expanded variants, uncertain_portions. **Not** stored on a coin.
- **POST /api/v2/llm/legend/transcribe/coin/{coin_id}** — “For coin”: uses the coin’s primary image, runs transcribe, then **stores** results in `llm_suggested_design` (obverse_legend, reverse_legend, exergue, obverse_legend_expanded, reverse_legend_expanded) and sets `llm_enriched_at`. These are applied on **POST /api/v2/llm/review/{coin_id}/approve**.

| Response field | Could suggest a coin field? | Stored as suggestion (transcribe/coin)? | Applied on approve? | Notes |
|----------------|-----------------------------|------------------------------------------|---------------------|------|
| obverse_legend | ✅ Yes | ✅ Yes (`llm_suggested_design`) | ✅ Yes | Via transcribe/coin. |
| obverse_legend_expanded | ✅ Yes | ✅ Yes (`llm_suggested_design`) | ✅ Yes | Via transcribe/coin. |
| reverse_legend | ✅ Yes | ✅ Yes (`llm_suggested_design`) | ✅ Yes | Via transcribe/coin. |
| reverse_legend_expanded | ✅ Yes | ✅ Yes (`llm_suggested_design`) | ✅ Yes | Via transcribe/coin. |
| exergue | ✅ Yes | ✅ Yes (`llm_suggested_design`) | ✅ Yes | Via transcribe/coin. |
| uncertain_portions | — | ❌ No | — | Metadata for UI, not stored on coin. |

---

### 2.6 POST /api/v2/llm/attribution/assist

**Role:** Suggest attribution from partial info (e.g. legend, weight). Returns ranked suggestions with attribution string and reference.

| Response field | Could suggest a coin field? | Stored as suggestion today? | Applied on approve? | Notes |
|----------------|-----------------------------|-----------------------------|---------------------|------|
| suggestions[].attribution | ✅ Yes (often “Issuer, Mint, Date”) | ❌ No | ❌ No | Would need parsing into issuer/mint/dates or storage of full string. |
| suggestions[].reference | ✅ Yes (catalog ref) | ❌ No | ❌ No | Could append to suggested_references if we had a “save attribution as suggestions” flow. |
| questions_to_resolve | — | — | — | UX only. |

---

### 2.7 POST /api/v2/llm/reference/validate

**Role:** Validate/normalize a catalog reference. Does not write to coin.

| Response field | Could suggest a coin field? | Stored as suggestion today? | Applied on approve? | Notes |
|----------------|-----------------------------|-----------------------------|---------------------|------|
| is_valid | — | — | — | — |
| normalized | ✅ Yes (as reference text) | ❌ No | ❌ No | Could add to suggested_references if we add “save normalized ref as suggestion”. |
| alternatives | ✅ Yes | ❌ No | ❌ No | Same. |

---

### 2.8 POST /api/v2/llm/catalog/parse

**Role:** Parse reference string into catalog/system/volume/number. No coin storage.

| Response field | Could suggest a coin field? | Stored as suggestion today? | Applied on approve? | Notes |
|----------------|-----------------------------|-----------------------------|---------------------|------|
| raw_reference, catalog_system, volume, number | — | — | — | Used to build reference_type/coin_reference when applying; not stored as “suggestion” on coin. |
| issuer | ✅ Yes | ❌ No | ❌ No | — |
| mint | ✅ Yes | ❌ No | ❌ No | — |

---

### 2.9 POST /api/v2/llm/provenance/parse

**Role:** Extract provenance chain from text. Result is a list of provenance entries, not per-coin “suggestions” in the current model.

| Response field | Could suggest a coin field? | Stored as suggestion today? | Applied on approve? | Notes |
|----------------|-----------------------------|-----------------------------|---------------------|------|
| provenance_chain | ✅ Yes (as events/notes) | ❌ No | ❌ No | Would need a way to “suggest provenance” and apply to coin’s provenance/notes. |

---

### 2.10 POST /api/v2/llm/condition/observe

**Role:** Describe condition from image (wear, surface, strike). Explicitly **not** grades.

| Response field | Could suggest a coin field? | Stored as suggestion today? | Applied on approve? | Notes |
|----------------|-----------------------------|-----------------------------|---------------------|------|
| wear_observations, surface_notes, strike_quality, notable_features, concerns, recommendation | ✅ Yes (e.g. notes or description) | ❌ No | ❌ No | Could map into grading_notes or a condition_notes field if we add suggest/apply. |

---

## 3. Summary Table – “Can the LLM suggest this?”

| Coin field (or concept) | Suggested by context/generate? | Stored as suggestion? | Applied on approve? | Other endpoints that could suggest it |
|-------------------------|-------------------------------|------------------------|---------------------|----------------------------------------|
| **references** (catalog refs) | ✅ suggested_references | ✅ llm_suggested_references | ✅ Yes | **identify/coin** (merged into llm_suggested_references), auction/parse, reference/validate, attribution/assist |
| **rarity** / rarity_notes | ✅ rarity_info | ✅ llm_suggested_rarity | ✅ Yes | — |
| **issuer** | ❌ | ✅ llm_suggested_attribution.issuer | ✅ Yes | **identify/coin** (ruler→issuer), auction/parse, attribution/assist, catalog/parse |
| **mint** | ❌ | ✅ llm_suggested_attribution.mint | ✅ Yes | **identify/coin**, auction/parse, attribution/assist, catalog/parse |
| **year_start / year_end** | ❌ | ✅ llm_suggested_attribution | ✅ Yes | **identify/coin** (date_range parsed), auction/parse |
| **denomination** | ❌ | ✅ llm_suggested_attribution.denomination | ✅ Yes | **identify/coin**, auction/parse |
| metal | ❌ | ❌ | ❌ | auction/parse |
| **obverse_legend / reverse_legend** | ❌ | ✅ llm_suggested_design | ✅ Yes | **legend/transcribe/coin**, auction/parse, legend/expand |
| **obverse_description / reverse_description** | ❌ | ✅ llm_suggested_design | ✅ Yes | **identify/coin**, auction/parse |
| **exergue** | ❌ | ✅ llm_suggested_design | ✅ Yes | **legend/transcribe/coin** |
| weight_g / diameter_mm | ❌ | ❌ | ❌ | auction/parse |
| grade | ❌ | ❌ | ❌ | auction/parse (only; condition/observe is not grades) |
| provenance | ❌ | ❌ | ❌ | provenance/parse |

---

## 4. Gaps and product options

- **Today:** **References**, **rarity**, **design** (legends, exergue, descriptions, expanded legends), and **attribution** (issuer, mint, denomination, year_start, year_end) are stored as LLM suggestions and applied on approve. Storage: `llm_suggested_references`, `llm_suggested_rarity`, `llm_suggested_design`, `llm_suggested_attribution`. The review queue and **POST /api/v2/llm/review/{coin_id}/approve** support all four; **POST /api/v2/llm/review/{coin_id}/dismiss** accepts `dismiss_design` and `dismiss_attribution`.
- **“For coin” flows:** **POST /api/v2/llm/legend/transcribe/coin/{coin_id}** writes design suggestions; **POST /api/v2/llm/identify/coin/{coin_id}** writes attribution + design (descriptions) + references. Both set `llm_enriched_at`.
- **Remaining gaps:** Metal, weight/diameter, grade, provenance are not suggestable in the “for coin” or review flows. **Auction parse** (POST /api/v2/llm/auction/parse) still returns ad-hoc data only; a “save auction parse as suggestions” flow would require extra storage and review/apply logic.

---

**See also:**  
- `docs/AI-SUGGESTIONS-REVIEW-QUEUE-COMPATIBILITY.md` – Review queue vs API/schema.  
- `docs/ENRICHMENT-CONSOLIDATION-ASSESSMENT.md` – ApplyEnrichmentService and field→domain mapping.  
- **`docs/LLM-LEGENDS-DESCRIPTIONS-IDENTIFY-PLAN.md`** – Step-by-step plan to implement LLM suggestions for legends, descriptions (transcribe), and identify (ruler/denomination/mint/descriptions).
