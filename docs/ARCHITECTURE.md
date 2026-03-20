# Oxia — Metabolic Intelligence OS Architecture

## Phase 1 (current): modular monolith + Clean-ish layering

| Layer | Path | Responsibility |
|--------|------|----------------|
| **Domain** | `oxia/domain/` | Errors and core concepts (no I/O, no FastAPI). |
| **Application** | `oxia/application/` | Ports (`Protocol`s), use cases (e.g. nutrition match), mappers, constants. |
| **Infrastructure** | `oxia/infrastructure/` | `AppContainer`, meal pipeline (I/O), FastAPI routers. |
| **Legacy shared** | `models.py`, `db.py`, `auth.py`, `llm/`, `nutrition/`, `chat/` | DTOs, SQLite, providers (to be wrapped behind ports in later phases). |

**HTTP entry:** `backend.py` → `oxia.infrastructure.web.app:app`  
**Routers:** `oxia/infrastructure/web/routers/` — one file per concern (`health`, `config`, `auth`, `providers`, `meals`, `nutrition`, `chat`).

### Latency expectations

- **`GET /health`**, **`GET /config/models`**: designed for **&lt; ~50 ms** (no network calls).
- **`POST /analyze_meal`**, **`POST /chat`**, **`POST /providers/*`**: dominated by **LLM / HF / Ollama** (seconds). Heavy vision work runs in **`asyncio.to_thread`** so the event loop stays responsive.

### Default vision model

- Env: **`OXIA_GEMINI_VISION_MODEL`** (default **`gemini-2.0-flash`**).
- UI catalog: `oxia/infrastructure/model_catalog.build_reasoning_models_list()`.

---

## Phase 2 (current): application ports + SQLite / nutrition adapters

- **`oxia/application/ports.py`**: `NutritionLookupPort`, `MealPersistencePort`, `UserPersistencePort`, `ProviderRegistryPort`.
- **Adapters**: `oxia/infrastructure/adapters/sqlite_persistence.py`, `nutrition_lookup_adapter.py` (wrap `db` + `nutrition.fetch_nutritional_truth`).
- **Wiring**: `AppContainer` holds port instances; `meal_pipeline`, `auth`, `chat`, and `nutrition` routers use the container (no direct `db` / raw HF in handlers).
- **Tests**: `tests/test_nutrition_match_use_case.py` (fake port); extend with adapter contract tests as needed.

---

## Phase 3 (planned): multi-agent “personas” orchestrator

- Coordinator agent + tool calls into existing `glucose_architect` / `inflammation_hunter` / `performance_ghost` structured outputs.
- **MetabolicMemory**: embeddings + vector store (**ChromaDB** local dev, **Pinecone** optional prod).
- Optional: **Mem0 / Zep** for long-term user memory (evaluate license & data residency).

---

## Phase 4 (planned): multimodal precision

- **MONAI**-based preprocessing / segmentation hooks (GPU, separate worker service).
- “Sauce / starch” heuristics as **downstream features** fused into prompts (not a medical device claim).

---

## Phase 5 (planned): wearable data fusion

- **MCP server** exposing Apple Health / Oura / Garmin via **Open Wearables** or vendor APIs where legal.
- **FHIR** export/import for EHR-aligned interoperability.
- Chat context packet extended with **last 24h HR / sleep** summaries (user-consented).

---

## Phase 6 (planned): UI

- Primary dashboard: **Next.js** (`frontend/`) — dynamic SVG glucose curve (real-time feel via client animation).
- **Streamlit** (`app.py`): optional demo / internal tools; not the main product shell.

---

## Compliance

See **`docs/COMPLIANCE.md`**. This repository is **not** HIPAA-certified; PHI requires BAA, encryption, audit controls, and legal review.
