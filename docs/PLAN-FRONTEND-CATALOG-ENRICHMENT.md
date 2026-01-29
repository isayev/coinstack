# Plan: Frontend Catalog Enrichment (Step-by-Step)

**Goal:** Enrich and expand catalog functionality across the frontend so that:
1. RPC coins (add/edit/quick-add) fetch catalog data and fill the form like RIC/CRRO when the RPC scraper is enabled.
2. When a catalog number is present, form a direct link to the online DB for easy reference.
3. Apply catalog behavior consistently everywhere (forms, detail, import, references card).

**Status:** Implemented. Direct type links (RPC, RRC) in `referenceLinks.ts` and `getReferenceUrl`; clickable primary and concordance refs in ReferencesCard; IdentityHeader and CoinCard reference text as links; form date_string → personal_notes and IdentityStep placeholder; import date_string → dating_notes, deferred badge/style, and RPC in placeholder; docs updated.

---

## Current state (brief)

- **Backend:** Catalog lookup `POST /api/catalog/lookup` uses `CatalogRegistry.lookup()`. When `CATALOG_SCRAPER_RPC_ENABLED=true`, RPC returns `status: "success"` with `payload` (authority, mint, date_string, obverse/reverse, etc.). Import enrich-preview `POST /api/v2/import/enrich-preview` already merges RPC success payload into `suggestions` and `lookup_results`.
- **Frontend:** `useCatalog.ts` calls `/api/catalog/lookup`; `ReferenceSuggest` handles success, ambiguous, deferred, error. `CoinForm` `handleReferenceSelect` maps `payload` to form fields (authority, mint, date_from/date_to, metal, design) and adds the reference. `referenceLinks.ts` builds one “RPC Online” link per reference set but uses **search** URL (`/search?q=...`) instead of a **direct type** URL.
- **Gaps:** RPC direct type URLs missing; optional per-reference links and date_string handling; ensure deferred vs success messaging and import UI treat RPC like other catalogs.

---

## Step 1: Direct catalog links (RPC and others)

**Objective:** When a catalog number is present, link directly to the type page where possible (not just search).

**1.1** **`lib/referenceLinks.ts`**
- Add a helper that returns a **direct type URL** for a single reference when applicable:
  - **RPC:** If `ref.catalog === "RPC"` and `ref.volume` and `ref.number` exist → `https://rpc.ashmus.ox.ac.uk/coins/{arabic_volume}/{number}` (convert Roman volume to Arabic, e.g. I→1). Reuse logic consistent with backend (e.g. small Roman→Arabic map for I–X).
  - **RIC:** OCRE type URL pattern if we have external_id or volume+number (optional; current search link may suffice).
  - **RRC/Crawford:** CRRO already uses direct ID URL; keep as-is.
- In `buildExternalLinks`, for **RPC**:
  - When building the single “RPC Online” link, use the **direct type URL** for the **primary** (or first) RPC reference that has volume+number; otherwise fall back to current search URL.
- Optionally: add `getReferenceUrl(ref: CatalogReference): string | null` that returns the best URL for one reference (for use in detail view, list view, etc.).

**1.2** **Tests**
- In `referenceLinks.test.ts`, add cases: RPC with volume+number → direct `/coins/1/4374`-style URL; RPC without volume → search URL.

**Deliverable:** RPC (and optionally RIC) references produce direct type links in “External Resources”; reusable helper for per-reference URL.

---

## Step 2: ReferencesCard — per-reference link (optional but recommended)

**Objective:** Make the primary (and optionally each) reference text clickable to its catalog type page.

**2.1** **`ReferencesCard.tsx`**
- For the primary reference display (the line showing `formatReference(primaryRef)`):
  - Use `getReferenceUrl(primaryRef)` (or equivalent from Step 1). If non-null, render it as an `<a href={url} target="_blank" rel="noopener noreferrer">` around the reference text, with an optional small external-link icon.
- Optionally: for concordance refs, render each as a link when `getReferenceUrl(ref)` is non-null (e.g. RPC I 4374, RIC II 118 each link to their type page).

**Deliverable:** Primary reference (and optionally others) are clickable to the correct online DB page.

---

## Step 3: Add/Edit form — RPC same as RIC/CRRO

**Objective:** When user types an RPC reference and the backend returns success with payload (scraper on), the form fills exactly like RIC/CRRO; when deferred, show “open catalog” and add reference only.

**3.1** **`ReferenceSuggest.tsx`**
- Already handles `status === "success"` with payload and `status === "deferred"`. No change required for RPC success vs deferred; backend drives status.
- Optional: In the deferred row, ensure the “Open catalog” link uses the **direct type URL** when available (e.g. from `suggestions.external_url` — backend already returns this). Verify that `external_url` for RPC is the direct type URL (backend `build_url_from_parts` already fixed). No frontend change if backend sends it.

**3.2** **`CoinForm/index.tsx` — `handleReferenceSelect`**
- Payload mapping already fills authority, mint, date_from/date_to, metal, design. RPC payload may include `date_string` but not `date_from`/`date_to`. Optional: if `payload.date_string` is present and `date_from`/`date_to` are absent, set a notes field or a single “date (text)” field if the form has one; otherwise leave as-is.
- Toast: When `suggestion.payload` is null (deferred RPC), keep “RPC has no API — use the link to look up details manually.” When `suggestion.payload` is present (RPC success), use the same success toast as for RIC (“Populated details from …”). Confirm current logic does this (payload vs no payload).

**3.3** **`IdentityStep.tsx`**
- Placeholder already says “e.g. RIC III 712”. Optionally add “RPC I 4374” in placeholder or help text so users know RPC is supported.

**Deliverable:** RPC success fills form; deferred RPC adds reference + link; copy and placeholders consistent with other catalogs.

---

## Step 4: Import flow — RPC in enrich-preview and EnrichmentPanel

**Objective:** Import enrich-preview and EnrichmentPanel treat RPC like RIC/CRRO (show success, fill suggestions, show direct link).

**4.1** **Backend (optional but recommended)**  
**`import_v2.py` — `_payload_to_suggestions`**
- RPC often returns `date_string` (e.g. "AD 14/15") and not `date_from`/`date_to`. Add mapping: if `payload.get("date_string")` and neither `date_from` nor `date_to` in payload, add a suggestion e.g. `mint_date_string` or reuse an existing text field in `CoinPreviewData` so import can show/apply it. Only if `CoinPreviewData` has a suitable field.

**4.2** **`EnrichmentPanel.tsx`**
- `lookup_results` already shows status (success, deferred, error). For **deferred** RPC, ensure the row shows “Open catalog” (or “Manual lookup”) with a link. Use `external_url` from each `lookup_results` entry; backend already returns it. If the UI currently only shows status text, add a small link when `external_url` is present.
- For **success** RPC, suggestions are already merged by backend; EnrichmentPanel shows and applies them like RIC. No change unless we add `date_string` suggestion (then show in panel if present).

**4.3** **`CoinPreviewEditor.tsx`**
- References tab: quick-add buttons already insert catalog names. Optional: ensure placeholder or hint mentions “e.g. RPC I 4374” so users try RPC.

**Deliverable:** Import enrich-preview shows RPC success/deferred and direct link; RPC suggestions apply like other catalogs; optional date_string in import.

---

## Step 5: Detail and list views — reference as link

**Objective:** Where a catalog reference is shown (detail header, table row, card), make it a link to the type page when we have a direct URL.

**5.1** **`IdentityHeader.tsx` (or wherever references string is rendered)**
- Currently references are shown as plain text. If we have a single primary reference (or first reference), get URL via `getReferenceUrl(primaryRef)`. If URL exists, render the reference segment as `<a href={url}>…</a>` with external-link icon; otherwise keep text.

**5.2** **Coin card / table row**
- If the card or table shows “reference” (e.g. primary ref string), make it a link using `getReferenceUrl(ref)` when ref has catalog+number (and optionally volume). Depends on whether the row has full `references[]` or only a formatted string; if only string, we may need to parse it (e.g. `parseReference`) to get ref object for `getReferenceUrl`. Prefer passing the reference object from parent when available.

**Deliverable:** Detail header and list/card reference text link to catalog type page where possible.

---

## Step 6: Consistency and docs

**6.1** **useCatalog.ts**
- `LookupResponse` already includes `external_url` and `payload`. No change unless we add optional `cache_hit` from backend later. Ensure TypeScript types allow `date_string` in payload if we use it in UI.

**6.2** **11-FRONTEND-COMPONENTS.md**
- Update ReferencesCard: “Validated external links (OCRE, CRRO, RPC)” and note that RPC uses direct type URL when volume+number present.
- Update “Reference Links and Catalog Parse”: document `getReferenceUrl` (if added) and that RPC links are direct type links when possible.

**6.3** **07-API-REFERENCE.md**
- Already documents RPC scraper and config. Optional: mention that frontend uses `external_url` from lookup for “Open catalog” and direct type links.

**Deliverable:** Types and docs aligned with new behavior.

---

## Implementation order (summary)

| Step | Focus | Dependency |
|------|--------|------------|
| 1 | Direct links in `referenceLinks.ts` (RPC type URL, optional getReferenceUrl) | None |
| 2 | ReferencesCard: clickable primary (and optionally concordance) refs | Step 1 |
| 3 | CoinForm/ReferenceSuggest: RPC = RIC (payload fill + deferred messaging) | None (verify only) |
| 4 | Import: EnrichmentPanel link for deferred; optional date_string suggestion | Step 1 for link; backend optional |
| 5 | Detail/IdentityHeader and list/card: reference text as link | Step 1 |
| 6 | Docs and types | After 1–5 |

---

## Out of scope (for later)

- Parsing `date_string` (e.g. "AD 14/15") into numeric year_start/year_end in the frontend (complex, locale-dependent).
- Per-reference external link for every ref in ReferencesCard (e.g. 5 refs → 5 links); Step 2 can start with primary only.
- Catalog status endpoint (`/api/catalog/status`) from polite-scraper plan; no frontend dependency for this plan.
