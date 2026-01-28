# CoinStack LLM Functionality and Models – Comparative Reference

**Source**: `backend/config/llm_config.yaml`, `backend/config/prompts/capabilities.yaml`, `backend/src/domain/llm.py`, `backend/src/infrastructure/web/routers/llm.py`, `backend/src/infrastructure/services/llm_service.py`  
**Profiles**: `development` (default), `production`, `offline` — set via `LLM_PROFILE` or `active_profile` in config.

---

## 1. Configured models

| Model name | Provider | Model ID | Vision | JSON mode | Cost (input/output per 1K) | Local |
|------------|----------|----------|--------|-----------|----------------------------|-------|
| **claude-sonnet** | Anthropic | claude-sonnet-4-5-20250929 | No | Yes | $0.003 / $0.015 | No |
| **claude-haiku** | Anthropic | claude-haiku-4-5-20251001 | No | Yes | $0.0008 / $0.004 | No |
| **gemini-2.5-pro** | Google | gemini-2.5-pro | Yes | Yes | $0.00125 / $0.005 | No |
| **gemini-2.5-flash** | Google | gemini-2.5-flash | Yes | Yes | $0.000075 / $0.0003 | No |
| **k2** | OpenRouter | openrouter/k2 | No | Yes | $0.0001 / $0.0003 | No |
| **deepseek-v3** | OpenRouter | deepseek/deepseek-chat | No | Yes | $0.00014 / $0.00028 | No |
| **ollama-llama3.2** | Ollama | llama3.2:latest | No | Yes | $0 / $0 | Yes |
| **ollama-phi3** | Ollama | phi3:latest | No | Yes | $0 / $0 | Yes |
| **ollama-llama3.2-vision** | Ollama | llama3.2-vision:latest | Yes | No | $0 / $0 | Yes |

**Requirements for “functional”**:

- **Anthropic**: `ANTHROPIC_API_KEY`
- **Google**: `GOOGLE_API_KEY`
- **OpenRouter**: `OPENROUTER_API_KEY`
- **Ollama**: `OLLAMA_HOST` (default `http://localhost:11434`); corresponding models (e.g. `llama3.2:latest`, `phi3:latest`, `llama3.2-vision:latest`) must be pulled/available.

---

## 2. Capabilities vs API, vision, and models by profile

| Capability | Tier | API endpoint(s) | Requires vision? | Production primary → fallback | Development primary → fallback | Offline primary → fallback |
|------------|------|------------------|------------------|-------------------------------|--------------------------------|-----------------------------|
| **vocab_normalize** | P0 | `POST /api/v2/llm/vocab/normalize` | No | k2 → deepseek-v3, claude-haiku | ollama-phi3 → ollama-llama3.2, k2 | ollama-phi3 → (none) |
| **legend_expand** | P0 | `POST /api/v2/llm/legend/expand` | No | deepseek-v3 → k2, claude-haiku | ollama-llama3.2 → ollama-phi3 | ollama-llama3.2 → ollama-phi3 |
| **auction_parse** | P0 | `POST /api/v2/llm/auction/parse` | No | claude-haiku → k2, deepseek-v3 | ollama-llama3.2 → ollama-phi3 | ollama-llama3.2 → ollama-phi3 |
| **provenance_parse** | P0 | `POST /api/v2/llm/provenance/parse` | No | claude-haiku → k2 | ollama-llama3.2 → ollama-phi3 | ollama-llama3.2 → ollama-phi3 |
| **image_identify** | P1 | `POST /api/v2/llm/identify`, `POST /api/v2/llm/identify/coin/{coin_id}` | Yes | gemini-2.5-pro → gemini-2.5-flash | ollama-llama3.2-vision → gemini-2.5-flash | ollama-llama3.2-vision → (none) |
| **reference_validate** | P1 | `POST /api/v2/llm/reference/validate` | No | claude-haiku → k2 | ollama-llama3.2 → ollama-phi3 | ollama-llama3.2 → ollama-phi3 |
| **context_generate** | P1 | `POST /api/v2/llm/context/generate` | No | deepseek-v3 → claude-sonnet | deepseek-v3 → ollama-llama3.2 | ollama-llama3.2 → ollama-phi3 |
| **attribution_assist** | P2 | `POST /api/v2/llm/attribution/assist` | No | claude-sonnet → deepseek-v3 | ollama-llama3.2 → (none) | ollama-llama3.2 → (none) |
| **legend_transcribe** | P2 | `POST /api/v2/llm/legend/transcribe`, `POST /api/v2/llm/legend/transcribe/coin/{coin_id}` | Yes | gemini-2.5-pro → gemini-2.5-flash | ollama-llama3.2-vision → gemini-2.5-flash | ollama-llama3.2-vision → (none) |
| **catalog_parse** | P2 | `POST /api/v2/llm/catalog/parse` | No | k2 → claude-haiku | ollama-phi3 → ollama-llama3.2 | ollama-phi3 → (none) |
| **condition_observations** | P2 | `POST /api/v2/llm/condition/observe` | Yes | gemini-2.5-pro → gemini-2.5-flash | ollama-llama3.2-vision → gemini-2.5-flash | ollama-llama3.2-vision → (none) |

**P3 (deferred)** — no model routing in config; not wired to live models:

- `search_assist`, `collection_insights`, `description_generate`, `die_study`

---

## 3. Which models are used where (by profile)

| Profile | Text-only capabilities (typical models) | Vision capabilities (typical models) |
|---------|----------------------------------------|--------------------------------------|
| **production** | k2, deepseek-v3, claude-haiku, claude-sonnet | gemini-2.5-pro, gemini-2.5-flash |
| **development** | ollama-phi3, ollama-llama3.2, k2, deepseek-v3 | ollama-llama3.2-vision, gemini-2.5-flash |
| **offline** | ollama-phi3, ollama-llama3.2 | ollama-llama3.2-vision |

---

## 4. Functional checklist (per profile)

| Requirement | Production | Development | Offline |
|-------------|------------|-------------|---------|
| **P0 (vocab, legend, auction, provenance)** | OpenRouter and/or Anthropic keys | Ollama + optional OpenRouter | Ollama (llama3.2, phi3) |
| **P1 image_identify** | Google key | Ollama vision or Google | Ollama (llama3.2-vision) |
| **P1 reference_validate** | Anthropic or OpenRouter | Ollama | Ollama |
| **P1 context_generate** | OpenRouter (deepseek) or Anthropic (claude-sonnet) | OpenRouter or Ollama | Ollama |
| **P2 attribution_assist** | Anthropic or OpenRouter | Ollama | Ollama |
| **P2 legend_transcribe** | Google | Ollama vision or Google | Ollama vision |
| **P2 catalog_parse** | OpenRouter or Anthropic | Ollama | Ollama |
| **P2 condition_observations** | Google | Ollama vision or Google | Ollama vision |

---

## 5. Admin and review endpoints (no model routing)

- **Status**: `GET /api/v2/llm/status` — lists availability of P0+P1 capabilities (MVP) for current profile.
- **Cost report**: `GET /api/v2/llm/cost-report?days=30` — cost by capability and by model.
- **Metrics**: `GET /api/v2/llm/metrics` — call counts by capability and model.
- **Feedback**: `POST /api/v2/llm/feedback` — submit accuracy feedback (capability, model_used).
- **LLM review queue**: `GET /api/v2/llm/review`, `POST /api/v2/llm/review/{coin_id}/dismiss`, `POST /api/v2/llm/review/{coin_id}/approve` — use coin data and suggestions produced by image_identify, legend_transcribe, context_generate; no direct model calls in these endpoints.

---

## 6. Prompt and config locations

- **Model and capability routing**: `backend/config/llm_config.yaml` (providers, models, capabilities with per-profile primary/fallback).
- **Prompt templates**: `backend/config/prompts/capabilities.yaml` (system/user templates and parameters per capability).
- **Domain capabilities enum**: `backend/src/domain/llm.py` (`LLMCapability`).
- **Router**: `backend/src/infrastructure/web/routers/llm.py`.
- **Service**: `backend/src/infrastructure/services/llm_service.py` (LiteLLM completion, cache, cost tracking, model selection from config).
