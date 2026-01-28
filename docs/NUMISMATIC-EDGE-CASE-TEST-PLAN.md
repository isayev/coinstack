# CoinStack Numismatic Edge Case Test Plan

Structured tests for domain-specific behavior: dates (BC/AD, ranges, uncertainty), references (RIC/RPC/RSC/BMC), denominations, and die-study flows.

---

## 1. BC/AD and Year Ranges

### 1.1 Input and storage

| # | Input / scenario | Expected | Verify |
|---|-------------------|----------|--------|
| 1.1.1 | `year_start = -44`, `year_end = -44` | Display “44 BC”; store -44. | Form IdentityStep, CoinCard/CoinTableRow, detail header. |
| 1.1.2 | `year_start = -27`, `year_end = 14` | Display “27 BC – AD 14” (or “27 BC – 14 AD” per project convention). | Formatters (`formatYear`, `formatDateRange`), CollectionSidebar “Negative = BC, Positive = AD”. |
| 1.1.3 | `year_start = 0` | Conventions: no year 0; treat as 1 BC or 1 AD per domain rule. | Schema/backend and UI labels (e.g. YearHistogram “1 BC”). |
| 1.1.4 | `year_end < year_start` (e.g. -27 and -44) | Validation error “End year must be after start year.” | CreateCoinSchema superRefine; IdentityStep inline error. |
| 1.1.5 | Blank / null years | Optional; display “—” or “Unknown” where shown. | CoinTableRow, CoinCard, detail. |
| 1.1.6 | Very large | year_start = 2025, year_end = 2026 | Accepted or capped per product rule. | Form + API. |

### 1.2 Filter and display

| # | Scenario | Expected | Verify |
|---|----------|----------|--------|
| 1.2.1 | Filter “year from” -100, “year to” 100 | Coins with overlapping range included. | CollectionSidebar year sliders, `mint_year_gte` / `mint_year_lte`. |
| 1.2.2 | Filter spanning BC/AD (e.g. -10 to 10) | BC and AD coins both match. | Backend filters, histogram “BC\|AD” divider. |
| 1.2.3 | Stats / histogram | BC years appear left of divider; AD right. | YearHistogram, RulerTimeline. |

---

## 2. Uncertain and Range Dates

| # | Scenario | Expected | Verify |
|---|----------|----------|--------|
| 2.1 | Single year (year_start = year_end) | Shown as “27 BC” or “AD 14”, not “27–27 BC”. | formatDateRange, CoinTableRow, CoinCard. |
| 2.2 | Reign / emission range (e.g. 69–79) | “AD 69–79” or “69–79 AD” per style. | IdentityStep, detail, reference links. |
| 2.3 | `dating_certainty` = BROAD / NARROW / EXACT | If shown in UI, label or tooltip explains; filters (if any) behave accordingly. | Domain schemas, CoinForm/CoinDetail. |
| 2.4 | “Circa” or “c.” | If `is_circa` or similar exists, display and filter reflect it. | filterStore, backend, display. |

---

## 3. Reference Formats (RIC, RPC, RSC, BMC, Crawford, etc.)

### 3.1 Structure and validation

| # | Scenario | Expected | Verify |
|---|----------|----------|--------|
| 3.1.1 | Primary reference RIC I 207 | Stored as catalog “RIC”, number “207”, volume “I”; displayed consistently. | ReferencesCard, CoinForm ResearchStep, reference links. |
| 3.1.2 | RPC 1234 (no volume) | volume optional; no spurious “Vol. undefined”. | Schema, display, external link builders. |
| 3.1.3 | Invalid or partial (e.g. “RIC 207” without volume) | Accepted or validated per product rule; no crash. | ReferenceSuggest, ResearchStep. |
| 3.1.4 | Multiple references | Primary vs non-primary distinguished; order or labels clear. | Coin detail, references list, “plate coin” if supported. |

### 3.2 Links and search

| # | Scenario | Expected | Verify |
|---|----------|----------|--------|
| 3.2.1 | OCRE / ID lookup | Link uses correct OCRE URL for RIC. | referenceLinks.ts, ReferencesCard. |
| 3.2.2 | RPC search | Link to RPC search/query. | referenceLinks.ts. |
| 3.2.3 | ACSearch, Wildwinds, CoinArchives | Links use encoded query (catalog + number). | referenceLinks.ts, sanitization. |

---

## 4. Denomination and Issuer/Mint

| # | Scenario | Expected | Verify |
|---|----------|----------|--------|
| 4.1 | Denomination “Aureus” vs “Double aureus” | Controlled vocab vs free text; filters and display consistent. | VocabAutocomplete, filterStore, backend vocab. |
| 4.2 | Issuer/mint from vocab | Normalization and display use canonical name; review queue if confidence &lt; threshold. | Vocab search/normalize, CoinForm, Review Center. |
| 4.3 | “Unknown” ruler or mint | Filter “Unknown ruler” / “Unknown mint”; cards show “Unknown” or “—” where appropriate. | filterStore, CoinCard, CoinTableRow. |

---

## 5. Die Study and Die Linking

| # | Scenario | Expected | Verify |
|---|----------|----------|--------|
| 5.1 | Set obverse_die_id / reverse_die_id | Stored and shown on detail and in die-study UI. | CoinForm ResearchStep, CoinDetail, die-study endpoints. |
| 5.2 | Link multiple coins to same die | Die-study flow allows “same obverse die” (or reverse); list or graph of linked coins. | Die study API and UI (if present). |
| 5.3 | Remove or change die link | No orphan references; history/audit if required. | Edit flow, die-study API. |

---

## 6. Grade, Metal, and Physical Units

| # | Scenario | Expected | Verify |
|---|----------|----------|--------|
| 6.1 | Grade “VF”, “VF-”, “VF+” | Parsed and displayed; sort/filter consistent. | GradeBadge, filter, backend. |
| 6.2 | Weight in grams, diameter in mm | Units clear in form and detail; decimals/formats consistent. | PhysicalStep, SpecificationsCard, locale. |
| 6.3 | Die axis 0–12 | Stored and shown (e.g. clock or numeric); 12 = 0 where applicable. | DieAxisClock, schema. |

---

## 7. Cross-Cutting Data Integrity

| # | Scenario | Expected | Verify |
|---|----------|----------|--------|
| 7.1 | Import from auction scraper | BC years, references, denomination preserved; no truncation of leading zeros in ref numbers. | Scrape → preview → confirm flow. |
| 7.2 | Bulk normalize | Issuer/mint/denomination normalized; low-confidence items in review queue. | BulkEnrichPage, Review Center vocabulary tab. |
| 7.3 | Audit / compare to auction | Discrepancies for date, weight, ref; “accept”/“reject” and optional “apply” update coin. | AuditPanel, DiscrepanciesReviewTab, EnrichmentsReviewTab. |

---

## 8. Test Data Suggestions

- **Dates:** -44 (Caesar), -27–14 (Augustus), 69–79 (Vespasian), 98–117 (Trajan), 284–305 (Diocletian).
- **References:** RIC I 207, RIC II 123, RPC 456, BMC 12, Crawford 123/1.
- **Denominations:** Denarius, Aureus, Antoninianus, Solidus, Follis.
- **Edge values:** year_start = year_end; year_end = null; catalog “RIC” with number “” or very long string.

---

## 9. When to Run

- After any change to date/reference/denomination/die schema or form.
- Before release if numismatic accuracy is a requirement.
- Alongside API contract tests for backend date/reference/vocab endpoints.
