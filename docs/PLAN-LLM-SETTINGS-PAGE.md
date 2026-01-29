# Plan: LLM Settings Page and Billing/Usage

**Purpose**: Add a dedicated LLM settings area so users can check status, see which API keys are configured, view usage/cost, change profile or models, and fix "All providers failed" (e.g. Anthropic credit balance) with clear guidance.

**Status**: Implemented (backend `provider_keys` on status, frontend LLM & AI card on Settings page, docs updated).

---

## 1. Current LLM Functionality Check

### 1.1 Backend

| Component | Location | Notes |
|-----------|----------|--------|
| **Config** | `backend/config/llm_config.yaml` | Profiles (development/production/offline), models, capabilities, primary/fallback per capability. |
| **Env keys** | `.env` / env vars | `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_HOST`. Keys are **never** stored in app; LiteLLM reads from env. |
| **Profile** | `LLM_PROFILE` or YAML `settings.active_profile` | Default `development`. Controls which primary/fallback models are used per capability. |
| **Service** | `backend/src/infrastructure/services/llm_service.py` | `LLMService` loads YAML, uses LiteLLM `acompletion()`, tries primary then fallbacks on failure. |
| **Router** | `backend/src/infrastructure/web/routers/llm.py` | All LLM endpoints under `/api/v2/llm`. |

**Existing admin endpoints**:

- **GET /api/v2/llm/status** — `StatusResponse`: `status`, `profile`, `monthly_cost_usd`, `monthly_budget_usd`, `budget_remaining_usd`, `capabilities_available`, `ollama_available`.
- **GET /api/v2/llm/cost-report?days=30** — `CostReportResponse`: `period_days`, `total_cost_usd`, `by_capability`, `by_model`.
- **GET /api/v2/llm/metrics?hours=24** — `MetricsSummaryResponse`: call counts, latencies, cache hit rate, errors.

### 1.2 Frontend

- **useLLM.ts** — `useLLMStatus()` (mutation), `useGenerateHistoricalContext()`, etc. Status is fetched on demand, not on a dedicated settings view.
- **CoinDetailPage** — "Generate historical context" uses `useGenerateHistoricalContext()`; on failure shows toast: `Failed to generate context: ${err.message}`.
- **SettingsPage** — Single page at `/settings` (Vocabulary, Database, Backup, Appearance, Data, About). **No LLM section yet.**

### 1.3 Capability That Is Failing

- **context_generate** (historical context for a coin):
  - **Production profile**: primary `claude-opus`, fallback `[deepseek-v3, claude-sonnet]`.
  - **Development profile**: primary `deepseek-v3`, fallback `[ollama-llama3.2]`.

Error seen:

```text
Failed to generate context: All providers failed: LLM call failed: litellm.BadRequestError: AnthropicException - {"type":"error","error":{"type":"invalid_request_error","message":"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."},"request_id":"..."} (tried: claude-opus, deepseek-v3, claude-sonnet)
```

So the stack tried **claude-opus** (Anthropic) → **deepseek-v3** (OpenRouter) → **claude-sonnet** (Anthropic). Anthropic failed due to low credits; if OpenRouter also failed, likely `OPENROUTER_API_KEY` is missing or OpenRouter credits are exhausted.

---

## 2. Root Cause and Immediate Fix

**Root cause**: Anthropic API requires prepaid credits. The account’s credit balance is too low, so all Anthropic models fail. Fallbacks (e.g. deepseek-v3 via OpenRouter) may also fail if the key is missing or OpenRouter has no credits.

**Immediate fixes** (user-facing):

1. **Anthropic**: Go to [Plans & Billing](https://console.anthropic.com/settings/billing) → purchase credits or enable auto-reload. Credits are prepaid; failed requests are not charged.
2. **Use a different profile**: Set `LLM_PROFILE=development` (e.g. in `.env`). Then **context_generate** uses **deepseek-v3** as primary (OpenRouter). Requires `OPENROUTER_API_KEY` and OpenRouter credits.
3. **Use local models**: Run Ollama and set **offline** profile so context_generate uses `ollama-llama3.2` (no cloud billing).

No code change is strictly required for the fix; the LLM Settings page will make these options visible and document the links.

---

## 3. LLM Billing and Usage (Lookup Summary)

### 3.1 Anthropic

- **Billing**: Prepaid usage credits via [Console → Settings → Billing](https://console.anthropic.com/settings/billing). "Buy credits" / auto-reload when balance is low.
- **Docs**: [Pricing and Billing](https://support.anthropic.com/en/collections/9811459-pricing-and-billing), [How do I pay for my Claude API usage?](https://support.anthropic.com/en/articles/8977456-how-do-i-pay-for-my-api-usage).
- **Pricing (indicative)**: Opus 4.5 ~$5 / $25 per million input/output tokens. Only successful calls are charged.
- **Balance**: Shown on the Billing page; not exposed via a public API for in-app display.

### 3.2 OpenRouter (used for deepseek-v3 and others)

- **Billing**: [OpenRouter Pricing](https://openrouter.ai/pricing). Free tier (limits) or pay-as-you-go credits.
- **Remaining credits**: `GET https://openrouter.ai/api/v1/credits` with bearer token returns usage/credits (can be used by backend to show "OpenRouter credits" status if we add a small server-side proxy for the key).
- **Usage**: Token counts and cost are in API responses; we already track cost in-app via `cost-report` and `llm_costs.sqlite`.

### 3.3 Google (Gemini)

- **Billing**: Google AI Studio / Cloud billing. Not required for context_generate in current config; needed for vision capabilities (e.g. image_identify, legend_transcribe).

### 3.4 In-App Usage

- **Cost tracking**: `LLMService` uses `CostTracker` (e.g. `data/llm_costs.sqlite`). **GET /api/v2/llm/cost-report** and **GET /api/v2/llm/metrics** already expose usage and cost by capability/model.

---

## 4. Plan: LLM Settings Page

### 4.1 Placement

- **Option A (recommended)**: Add an **"LLM & AI"** card to the existing **Settings** page (`/settings`), same layout as Vocabulary, Database, Backup, etc.
- **Option B**: New route `/settings/llm` and a link from Settings (e.g. "LLM & AI" → dedicated page). Use if the LLM section grows (e.g. model overrides, key health checks).

Start with **Option A**; refactor to Option B if the section becomes large.

### 4.2 Content (LLM Settings Card)

1. **Status**
   - Current **profile** (development / production / offline).
   - **Budget**: monthly cost, budget, remaining (from existing `GET /api/v2/llm/status`).
   - Short **health** line: e.g. "Operational" or "No API keys configured" (see backend below).

2. **Provider keys (masked)**
   - List: Anthropic, OpenRouter, Google, Ollama (optional).
   - For each: "Configured" (key set) or "Not set". **Never show key values.**  
   - Backend: new endpoint or extend status to return e.g. `provider_keys: { "anthropic": true, "openrouter": false, ... }` by checking `os.environ.get("ANTHROPIC_API_KEY")` etc. (presence only).

3. **Usage and cost**
   - Use existing **GET /api/v2/llm/cost-report?days=30**: show total cost and optionally a small breakdown (by capability or by model).
   - Link or short text: "Detailed usage is tracked in-app; for provider billing see links below."

4. **Billing links**
   - **Anthropic**: [Plans & Billing](https://console.anthropic.com/settings/billing) — "Top up credits or set auto-reload."
   - **OpenRouter**: [Pricing / Account](https://openrouter.ai/pricing) or dashboard — "Check credits and usage."
   - Optional: "If historical context fails with 'credit balance too low', top up Anthropic or switch to development profile to use OpenRouter (deepseek-v3)."

5. **Profile / model selection (optional for v1)**
   - **Read-only** display of current profile and which models are used for "Historical context" (context_generate) and optionally one or two other capabilities.
   - **Editable** profile: would require backend to accept e.g. `PATCH /api/v2/llm/settings` with `{ "profile": "development" }` and either (a) persist in a small settings table or (b) document "Set `LLM_PROFILE` in `.env` and restart backend." First version can be read-only + doc link.

6. **Troubleshooting**
   - One short line or expandable: "All providers failed" usually means Anthropic credits low or OpenRouter key missing/credits exhausted; top up or switch profile; see links above.

### 4.3 Backend Additions

| Addition | Purpose |
|----------|--------|
| **Provider key status** | Return which env keys are set (e.g. `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`) without values. Either extend **GET /api/v2/llm/status** with `provider_keys: Record<string, boolean>` or add **GET /api/v2/llm/settings**. |
| **Optional: OpenRouter credits** | If we want to show "OpenRouter credits: $X remaining", backend can call `GET https://openrouter.ai/api/v1/credits` with the server’s `OPENROUTER_API_KEY` and return a non-sensitive summary. Not required for v1. |

No new persistence is required for key status (env only). Profile could stay env/YAML-only with a note to "Set LLM_PROFILE and restart."

### 4.4 Frontend Additions

- **Settings page**: New card "LLM & AI" using:
  - `GET /api/v2/llm/status` (and new `provider_keys` if added).
  - `GET /api/v2/llm/cost-report?days=30`.
- **Hooks**: Reuse or add thin wrappers for status and cost-report (e.g. `useLLMStatus` already exists; add `useLLMCostReport(days)` if needed).
- **Copy**: Short descriptions and links for Anthropic and OpenRouter billing; one line for "credit balance too low" and profile switch.
- **CoinDetailPage**: Optional improvement: if `generateContext` fails with a message containing "credit balance" or "All providers failed", show a toast with a link to Settings (e.g. "Check LLM settings and billing") in addition to the error message.

### 4.5 Docs and Design

- **docs/ai-guide/07-API-REFERENCE.md**: Document any new or extended LLM endpoint (e.g. `provider_keys` on status or GET /api/v2/llm/settings).
- **design/**: No design spec exists for Settings yet; LLM card can follow the same pattern as existing Settings cards (CardTitle, CardDescription, CardContent with grid/buttons/links).

---

## 5. Implementation Order (Suggested)

1. **Backend**: Extend **GET /api/v2/llm/status** with `provider_keys: { anthropic: bool, openrouter: bool, google: bool }` (and optionally `ollama_available` already there). No new route required if this is enough.
2. **Frontend**: Add "LLM & AI" card to Settings page: status, profile, budget, provider key status, cost report summary, billing links, troubleshooting line.
3. **Docs**: Update 07-API-REFERENCE.md with the new status fields.
4. **Optional**: Improve CoinDetailPage error handling for "credit balance" / "All providers failed" with a link to Settings.

---

## 6. Summary

- **Current behaviour**: LLM enrichment (e.g. historical context) uses config in `llm_config.yaml` and env API keys; status and cost-report endpoints already exist.
- **Failure**: Anthropic credit balance too low; fallbacks (deepseek-v3, claude-sonnet) may also fail if keys/credits are missing.
- **Immediate fix**: Top up Anthropic or set `LLM_PROFILE=development` and ensure `OPENROUTER_API_KEY` is set.
- **Plan**: Add an LLM Settings section (preferably a card on `/settings`) to show status, provider key status, usage/cost, billing links, and optional profile/model display; extend status API with provider key presence; document billing/usage and troubleshooting.
