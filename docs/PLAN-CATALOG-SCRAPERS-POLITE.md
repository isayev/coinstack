# Plan: Polite Catalog Scrapers (No-API Catalogs)

**Goal:** Define a reasonable, polite approach to fetching numismatic type data from catalogs that have an online presence but no public API—without aggressive scraping and with good practices.

**Status:** RPC Online scraper implemented (optional, enabled via `CATALOG_SCRAPER_RPC_ENABLED=true`). Other no-API catalogs can be added using the same pattern.

---

## 1. Scope: Which Catalogs?

| Catalog | Online presence | API | Scraper candidate |
|--------|------------------|-----|--------------------|
| **OCRE** (RIC) | numismatics.org/ocre | Yes (JSON-LD) | No—use API |
| **CRRO** (Crawford) | numismatics.org/crro | Yes (JSON-LD) | No—use API |
| **RPC Online** | rpc.ashmus.ox.ac.uk | No | Yes (primary target) |
| **Sear** (SCV) | — | No | Only if a stable public type-page exists |
| **BMCRE / BMCRR** | British Museum (partial) | No | Only if URLs and ToS allow |
| **SNG** | Various sylloge sites | No | Defer—many sources, rights vary |

**Initial focus:** RPC Online (Roman Provincial Coinage). Other no-API catalogs can be added later using the same pattern.

---

## 2. Politeness and Good Citizenship

### 2.1 Respect robots.txt

- **Cache:** Fetch and cache `robots.txt` per host with a TTL (e.g. 24 hours); reuse for all requests to that host within the window.
- **Parsing:** Use a standard parser (e.g. `urllib.robotparser.RobotFileParser` or equivalent) to decide `can_fetch(user_agent, url)` before each type-page request.
- **Behavior:** If the type-page URL is disallowed, return a result with status "disallowed" (or equivalent) and the URL only; do not fetch the page.
- **Crawl-delay:** If the host specifies Crawl-delay, use `max(parsed_delay, our_minimum)` (e.g. our minimum 8 s) so we never go faster than either policy.
- Implementers can place a small helper or class in the catalog-scraper layer; the plan does not prescribe a specific class name.

### 2.2 Rate limiting (conservative)

- **Per-host, per-session:** e.g. no more than 1 request every 5–10 seconds for catalog type pages.
- **Base delay:** Keep per-host base delay (e.g. 8–10 s for RPC). Reuse existing patterns: e.g. `SCRAPER_RATE_LIMITS` in config, with a dedicated key such as `catalog_rpc`.
- **No bulk crawl:** only fetch when the user (or a single reference) triggers a lookup (on-demand).
- **No site-wide indexing:** do not discover and scrape all type IDs; only resolve a specific reference (e.g. RPC I 4374 → one URL → one page).
- **Adaptive delay (optional):** If response time exceeds a threshold (e.g. 2 s), increase delay before the next request (e.g. by 1.5x) to reduce load when the site is slow.
- **Peak hours (optional):** Configurable option to apply a multiplier (e.g. 2x) during the host’s peak hours (e.g. UK working hours for RPC) to be extra conservative.
- **Circuit breaker:** After N consecutive failures (e.g. 3) for a host, stop sending requests for a cooldown period (e.g. 30 minutes), then allow one retry; document states as "open" / "half-open" / "closed" for clarity and for the status endpoint.

### 2.3 Identify the client

- Send a **clear, honest User-Agent**, e.g.  
  `CoinStack/1.0 (Numismatic collection manager; catalog lookup; +https://github.com/...)`
- Optionally add a short `X-Purpose` or comment in a header: “single-type lookup for personal collection.”
- Do not impersonate browsers beyond what’s needed for a simple GET (prefer minimal headers if the site works with them).

### 2.4 Cache aggressively

- Use the same cache layer as the rest of the app (e.g. in-memory or Redis keyed by `(system, external_id)`).
- Honor cache before making a new request.
- Cache 4xx/5xx or “page not found” for a shorter time (e.g. 24–48 h) to avoid hammering invalid URLs.

**Tiered data and cache TTL:** Treat data by stability and value so stable data is cached longer and volatile data refreshed when needed.

- **Tier 1 (critical):** catalog_id, authority, denomination, mint, date_range — cache long (e.g. 365 days), fetch priority high.
- **Tier 2 (descriptive):** obverse/reverse description and legend — cache medium (e.g. 90 days).
- **Tier 3 (supplementary):** bibliography, known specimens, die links, image URLs — cache shorter (e.g. 30 days).
- **Tier 4 (volatile):** auction appearances, prices — cache short (e.g. 7 days) or on-demand only.

Config can reference these tiers; suggested TTLs above are for the plan only.

### 2.5 Minimal request footprint

- Request only the **type page** (one URL per reference); no automatic following of “related” or “all types” links.
- Prefer HTTP GET; avoid POST unless the site requires it for a type lookup.
- Do not send unnecessary headers or cookies beyond what’s needed for a single page load.

---

## 3. Technical Practices

### 3.1 When to skip fetching (conditional fetch)

Decide whether to fetch based on cache and request context; avoid unnecessary requests.

- Do **not** fetch if cache exists and is not expired.
- Do **not** fetch if the request context is "URL only" (user only wants the link).
- Do **not** fetch if cache already has tier 1 complete and the user did not request a refresh.
- **Fetch** when there is no cache, or cache is expired, or critical data is missing.

Conceptually: `should_fetch_catalog_page(ref, cached, request_context) -> bool`; implementation location is not mandated.

### 3.2 On-demand only

- Trigger a catalog fetch only when:
  - The user requests lookup for a **specific** reference (e.g. “RPC I 4374”), or
  - A single coin is being enriched and needs one (or a few) catalog type(s).
- Do **not** run background jobs that crawl entire catalogs or large ID ranges.

### 3.3 Retries and backoff

- Use **exponential backoff** on 5xx and 429 (e.g. 1 retry after 10 s, then 30 s).
- After a small number of failures (e.g. 2–3), stop and return “deferred” (URL only) instead of retrying indefinitely.
- Log failures for debugging; do not retry in a tight loop.

### 3.4 Timeouts and errors

- Use a **reasonable timeout** (e.g. 15–20 s) per request so slow pages don’t tie up the app.
- On timeout or connection error: return “deferred” with the URL and a short message (“Catalog site slow or unavailable; use link to open in browser”).
- Do not treat timeouts as a reason to increase request rate.

### 3.5 Data extraction

- Parse only the **type page** HTML (or whatever the site serves) and map to the existing **CatalogPayload** (or equivalent) fields: authority, denomination, mint, date range, obverse/reverse description, legends, etc.
- Prefer **robust selectors** (e.g. semantic HTML, stable IDs/classes); avoid fragile layout-based scraping.
- **Selectors:** Each catalog (e.g. RPC) has a versioned set of selectors (in code or config) for authority, denomination, mint, obverse/reverse, etc., with fallback selectors where possible.
- **Structure change detection:** If, after parsing, fewer than a threshold (e.g. 50%) of expected selectors match, treat as a possible structure change: log a warning, return partial or url_only with a "parse_failure" or "structure_change" reason, and do not retry repeatedly. This allows maintainers to detect when a site’s HTML has changed and selectors need updating.
- If the page structure changes and parsing fails completely, return “deferred” (or partial) with the URL and optionally a “parse failed” note; do not retry repeatedly.

### 3.6 No API impersonation

- Do not try to reverse-engineer or call internal/undocumented “API-like” endpoints unless the host clearly documents them as public. Stick to the same URLs a human would open in a browser for one type.

### 3.7 Partial results and degradation

Extend beyond binary success/deferred so partial data is still returned when some fields parse.

- **Status values:** Include `full`, `partial`, `url_only`, `failed`, `disallowed`.
- **Partial:** When some but not all fields parse successfully, return status `partial` with the payload containing only the fields that were extracted; do not fail the whole request.
- **Metadata:** Include (in the result or payload) which fields were found and which were missing, plus an optional degradation reason (e.g. "selector_not_found", "timeout") and a short user-facing message (e.g. "Basic type data retrieved; descriptions unavailable").
- **Contract:** Extend the existing `CatalogResult` (or equivalent) so the API and UI can show partial data and the link when full data is unavailable.

### 3.8 Cross-references from type pages

Harvest references to other catalogs mentioned on the page without making extra requests.

- **Rule:** When fetching a type page (e.g. RPC I 4374), extract from the page text any mentions of other catalog references (e.g. "cf. RIC III 123", "BMC 456") using existing reference patterns/parser.
- **No extra requests:** Do not fetch those cross-referenced URLs; only parse and store the references for future use (suggestions, validation, or later on-demand fetch).
- **Scope:** Primary catalog for the page is known; skip self-references; only collect references to other supported catalogs (RIC, Crawford, RPC, etc.) with sufficient confidence (e.g. from existing `parse_catalog_reference`).
- **Storage:** Cross-refs are stored or exposed (e.g. on the catalog result or coin reference) for use by the app; storage format can be defined in implementation.

### 3.9 Images

- **Default:** Do not fetch image bytes (no bandwidth/storage spike, respect rights).
- **URLs only:** Allowed to store image URLs present on the type page, with attribution required in UI and in stored data.
- **Optional thumbnail cache:** If implemented, only for "user collection" references, small max size (e.g. 50 KB), and only when clearly within the site’s terms (e.g. educational use).
- **Rights:** Each source (RPC, Wildwinds, OCRE, etc.) must be checked for image terms; when in doubt, store URL + attribution only.

### 3.10 Request coalescing (batched delay)

- **Idea:** For a given host, if multiple type-page requests are triggered within a short window (e.g. 30 seconds)—e.g. user opens several coins with RPC refs—group them and process with a single inter-request delay between each fetch (e.g. 8–10 s), rather than spreading delays arbitrarily.
- **Constraints:** No increase in total request rate to the host; same per-request rate limit as without coalescing; coalescing only reduces the perceived delay for the user by ordering requests and applying one delay between consecutive requests.
- **Scope:** Optional for v1; document as a good practice so implementers can add a small coalescer (e.g. per-host queue + worker) when integrating the fetcher.

### 3.11 Optional pre-warm (opt-in only)

- **Default:** Disabled. Enable only via explicit config/opt-in.
- **Trigger:** Only references that already exist in the user’s collection (no bulk catalog crawl).
- **Rate:** Strict cap (e.g. 1 request per hour during off-peak, max 20 per day); "off-peak" can be configurable (e.g. 2–6 AM local).
- **Priority:** References that appear multiple times in the collection, or that are missing tier 1 data, can be prioritized.
- **Not bulk crawling:** This does not discover or crawl the whole catalog; it only pre-warms pages for references the user already owns.

---

## 4. Integration with Existing Catalog Layer

- **Keep the current contract:** e.g. `CatalogService.reconcile()` and `fetch_type_data()` (or equivalent). For RPC, today `reconcile()` returns “deferred” with a URL and `fetch_type_data()` returns None.
- **Optional scraper path:** When the service has “no API” but a scraper is configured:
  1. `reconcile()` still builds the type URL (as now).
  2. If a “catalog scraper” is enabled for that system (e.g. via config or feature flag), call a **single-page fetcher** for that URL, with rate limit and cache.
  3. If the fetcher returns HTML, parse it into `CatalogPayload` and return “success” with payload; otherwise keep “deferred” with URL.
- **Registry:** Reuse existing rate limiting and caching (e.g. `CatalogRegistry`); add a separate, stricter limit for “catalog scrapers” so they don’t share the same quota as light API calls.

---

## 5. Legal and Ethical Notes

- **Purpose:** Support personal/research numismatic use (e.g. linking a coin to a type and showing basic type data), not republishing or mirroring full catalogs.
- **Attribution:** Always attribute the source (e.g. “RPC Online, Ashmolean Museum”) in UI and in any stored payload or logs.
- **Terms of use:** Before implementing a scraper for a given site, check its terms of use and robots.txt; if unclear, prefer “deferred” (URL only) or contact the host.
- **Data minimization:** Store only what’s needed for display and attribution (e.g. authority, denomination, obverse/reverse text, date range); avoid storing full HTML or unrelated content.

---

## 6. Transparent status (optional endpoint)

- **Endpoint:** e.g. `GET /api/catalog/status` (or under existing catalog router) returning per-catalog status.
- **Fields (suggested):** catalog id, last_successful_fetch, last_failed_fetch, cache_hit_rate_24h, request_count_24h, average_response_time_ms, circuit_breaker_status (closed / open / half_open), robots_txt_allows.
- **Purpose:** So users and support can see why lookups are slow or failing without guessing. Implementation can be minimal (in-memory counters and timestamps) for v1.

---

## 7. Offline / no-cache fallback (future)

- **Idea:** When the app is offline or has no cache, optionally show minimal context for a reference using small bundled data (e.g. RIC volumes/emperors, Crawford basics, common denominations)—not full catalog, only enough to validate format and show basic context (e.g. "RIC I covers 31 BC – 69 AD").
- **Scope:** Defer to a later phase if needed; document as a desired direction so that bundled JSON size and format can be designed later without blocking the main scraper work.

---

## 8. Suggested Implementation Order

1. **Config and policy**
   - Add `CATALOG_SCRAPER_*` settings (enable/disable per system, rate limits, cache TTLs by tier if implemented, optional pre-warm/coalescing flags).
   - Document robots.txt and rate limits in this plan or in code comments.

2. **Robots.txt**
   - Implement fetch, parse, cache (24h), and can_fetch + Crawl-delay before any type fetch.

3. **RPC fetcher (single type page)**
   - One URL per reference; conditional fetch; tiered cache; map HTML to CatalogPayload with graceful degradation (full/partial/url_only); extract cross-references from page text; store image URLs only with attribution.

4. **HTML and errors**
   - Versioned selectors; structure-change detection; circuit breaker and optional adaptive/peak delay.

5. **Wire into RPCService**
   - Feature flag; call fetcher when scraper enabled; keep deferred+URL as default when disabled or on failure.

6. **Status and observability**
   - Logging; optional GET /api/catalog/status with the fields above.

7. **Optional enhancements**
   - Pre-warm (opt-in), request coalescing, offline bundled data as follow-ups.

8. **Other catalogs later**
   - Apply the same politeness and technical rules to any future no-API catalog (e.g. Sear, BMCRE) after checking their sites and ToS.

---

## 9. Summary

- **Polite:** robots.txt (cached, parsed), strict rate limits, on-demand only, honest User-Agent, aggressive tiered caching, circuit breaker, optional adaptive/peak delay.
- **Good practices:** Single-type lookups, conditional fetch, retries with backoff, timeouts, robust versioned selectors, structure-change detection, graceful degradation (full/partial/url_only), cross-reference harvesting from page text, image URLs only with attribution, optional coalescing and pre-warm (opt-in).
- **Reasonable scope:** Start with RPC Online; extend to other no-API catalogs only when their terms and structure are clear.

This keeps catalog scraping minimal, respectful, and aligned with fetching numismatic data for personal/research use without aggressive or bulk behavior.

### Priority additions (from critique)

| Addition | Impact | In plan |
|----------|--------|---------|
| Graceful degradation (partial data) | High | Yes |
| Cross-reference harvesting | High | Yes |
| Conditional fetch logic | Medium | Yes |
| Tiered data + cache TTL | Medium | Yes |
| Robots.txt cache + parse | Medium | Yes |
| HTML structure versioning | Medium | Yes |
| Request coalescing | Medium | Yes (optional) |
| Pre-warm (user collection) | Low | Yes (opt-in) |
| Image URL storage + attribution | Low | Yes |
| Adaptive rate + circuit breaker | Medium | Yes |
| Status endpoint | Low | Yes |
| Offline bundled data | Low | Yes (future) |
