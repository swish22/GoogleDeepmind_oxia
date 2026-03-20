# 🧬 Oxia: The Metabolic Digital Twin

Your body's operating system. See your future self — before you eat.

Oxia is an AI-powered app that acts as your personal **Metabolic Digital Twin**. Take a photo of your meal and Oxia predicts how your body will react — glucose response, inflammation risk, and cognitive impact — with actionable insights before you take a bite.

## 🌟 Key Features

*   **📷 Vision AI:** Google Gemini identifies meals, ingredients, and macros from photos
*   **⏱️ Your Next 3 Hours:** Predictive timeline — when you'll peak, when to schedule deep work
*   **🧬 Shadow Personas:** Glucose Architect, Inflammation Hunter, Performance Ghost — first-person insights
*   **✨ Make It Better:** Concrete meal swaps (e.g., "Cauliflower rice → -35% glycemic load")
*   **🔮 Your Twin Learns:** Personal trends based on your logged meals
*   **📊 Diet log & Nutritional Truth:** HuggingFace-verified ingredient matches, roll-up macros, `POST /nutrition/match` to refresh without re-analyzing the photo
*   **📓 Track & Export:** Save named metabolic tests to your account (DB-backed), export JSON / CSV / HTML (diet + full report)
*   **📥 Shareable Report:** Download branded metabolic report cards (HTML)

## 🏗️ Architecture

| Layer | Tech |
|-------|------|
| Dashboard UI | **Next.js** (`frontend/`) — primary product UI |
| Optional demo | Streamlit (`app.py`) |
| Backend | **FastAPI** — **Clean Architecture layout** under `oxia/` (`domain` / `application` / `infrastructure`). Entry: `backend.py` → `uvicorn backend:app` |
| LLM | Google Gemini (default vision: **`gemini-2.0-flash`** via `OXIA_GEMINI_VISION_MODEL`), Ollama, HuggingFace |
| Data | HF `Maressay/food-nutrients-preparated` (primary) · Open Food Facts · USDA FDC (optional `USDA_FDC_API_KEY`) |

## Account-backed saved metabolic tests
Saved dashboard snapshots are persisted in the local SQLite database (env: `OXIA_DB_PATH`) behind clean-architecture ports/adapters.

API endpoints:
- `GET /meals/recent`
- `GET /meals/{meal_id}`
- `POST /meals/{meal_id}/snapshot`
- `DELETE /meals/{meal_id}`

See **`docs/ARCHITECTURE.md`** (roadmap: agents, vector memory, MONAI, MCP, FHIR) and **`docs/COMPLIANCE.md`** (not HIPAA-certified by default).

## 🚀 Getting Started

### Prerequisites
- Git
- Python 3.10+
- Node.js 18+ (for Next.js dashboard)
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### Setup

1. **Clone & configure env**
   ```bash
   git clone <your-repo-url>
   cd Oxia-Core-Project
   cp .env.example .env
   ```

   Optional for **Ollama** (local): install [Ollama](https://ollama.com), then set `OXIA_OLLAMA_VISION_MODEL=llava:latest` in `.env` (same idea as `ollama run llava` / `ollama pull llava`). The dashboard may show a **download / warmup overlay** when you switch to an **Ollama** or **Hugging Face** model.

2. **Backend (FastAPI)**
   ```bash
   # Mac/Linux
   ./install.sh
   source .venv/bin/activate
   uvicorn backend:app --port 8000

   # Windows
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m uvicorn backend:app --port 8000
   ```
   Backend runs at: `http://localhost:8000`

3. **Frontend (Next.js dashboard)**
   ```bash
   cd frontend
   npm install
   npm run dev -- -p 3000
   ```
   Frontend runs at: `http://localhost:3000`

4. **Optional: Streamlit demo**
   ```bash
   # with venv active
   streamlit run app.py --server.port 8501
   ```
   Streamlit runs at: `http://localhost:8501`

## 📁 Project Structure

```
.
├── oxia/                 # Metabolic OS core (Clean Architecture)
│   ├── domain/
│   ├── application/      # pure mappers, constants
│   └── infrastructure/   # FastAPI routers, container, meal pipeline
├── backend.py            # ASGI shim → oxia.infrastructure.web.app:app
├── frontend/             # Next.js dashboard
├── app.py                # Streamlit (optional)
├── nutrition/            # Multi-source ingredient lookup
├── llm/                  # Providers (Gemini, Ollama, HF)
├── models.py             # Pydantic v2 DTOs
├── docs/ARCHITECTURE.md
└── ...
```

## 🔒 Before Pushing

- `.env` is gitignored — never commit API keys
- `oxia.sqlite3*` is gitignored — local dev DB
- `users_data.json` is gitignored — local-only dev user data
- Copy `.env.example` to `.env` and add your `GEMINI_API_KEY` for local use

## 📜 License

MIT
