# 🧬 Oxia: The Metabolic Digital Twin

Your body's operating system. See your future self — before you eat.

Oxia is an AI-powered app that acts as your personal **Metabolic Digital Twin**. Take a photo of your meal and Oxia predicts how your body will react — glucose response, inflammation risk, and cognitive impact — with actionable insights before you take a bite.

## 🌟 Key Features

*   **📷 Vision AI:** Google Gemini identifies meals, ingredients, and macros from photos
*   **⏱️ Your Next 3 Hours:** Predictive timeline — when you'll peak, when to schedule deep work
*   **🧬 Shadow Personas:** Glucose Architect, Inflammation Hunter, Performance Ghost — first-person insights
*   **✨ Make It Better:** Concrete meal swaps (e.g., "Cauliflower rice → -35% glycemic load")
*   **🔮 Your Twin Learns:** Personal trends based on your logged meals
*   **📊 Nutritional Truth:** HuggingFace-verified ingredient data
*   **📓 Track & Export:** Log meals, export CSV for your doctor or nutritionist
*   **📥 Shareable Report:** Download branded metabolic report cards (HTML)

## 🏗️ Architecture

| Layer | Tech |
|-------|------|
| Frontend | Streamlit, Altair charts |
| Backend | FastAPI, Google Gemini SDK |
| Data | HuggingFace `Maressay/food-nutrients-preparated` |

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### Setup

1. **Clone & install:**
   ```bash
   git clone <your-repo-url>
   cd Oxia-Core-Project
   cp .env.example .env   # Then add your GEMINI_API_KEY
   ```

2. **Install dependencies:**
   ```bash
   # Mac/Linux
   ./install.sh

   # Windows
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Run:**
   ```bash
   # Mac/Linux
   ./run.sh

   # Windows
   .\run.ps1
   ```

4. **Open** [http://localhost:8501](http://localhost:8501)

## 📁 Project Structure

```
.
├── app.py          # Streamlit frontend
├── backend.py      # FastAPI + Gemini
├── heuristics.py   # HuggingFace nutritional lookup
├── models.py       # Pydantic schemas
├── .env.example    # Template (copy to .env)
├── requirements.txt
└── run.ps1 / run.sh
```

## 🔒 Before Pushing

- `.env` is gitignored — never commit API keys
- `users_data.json` is gitignored — local meal history stays local
- Copy `.env.example` to `.env` and add your `GEMINI_API_KEY` for local use

## 📜 License

MIT
