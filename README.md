# 🧬 Oxia: The Metabolic Digital Twin

Oxia is an AI-powered MVP that acts as your personal "Metabolic Digital Twin." By taking a photo of your meal, Oxia predicts how your body will react biologically, giving you actionable insights before you take a bite.

## 🌟 Key Features

*   **📷 Vision AI Analysis:** Uses Google's Gemini SDK (Gemini 2.5 Flash / 2.0 Flash) to identify meals, ingredients, portion sizes, and macronutrients directly from photos.
*   **🧬 Shadow Personas:** The heuristic engine translates your meal into acting archetypes:
    *   **🏗️ The Glucose Architect:** Simulates a 180-minute blood glucose curve, identifying peak spikes and crashes.
    *   **🔥 The Inflammation Hunter:** Scans ingredients for hidden metabolic disruptors (e.g., seed oils, refined sugars) to calculate a systemic stress score.
    *   **👻 The Performance Ghost:** Maps your macronutrient ratios to predict your resulting cognitive state (e.g., *Brain Fog Risk*, *Deep Work Window*).
    *   **⚖️ The Balanced Diet:** Visualizes your macro distribution in an interactive Donut chart.
*   **📊 Nutritional Truth:** Supplements AI estimations by actively querying the HuggingFace `Maressay/food-nutrients-preparated` dataset for scientifically verified nutritional values of your meal's ingredients.
*   **📓 Track & Export:** Includes a local user authentication system to individually track and save your meal history, with a 1-click CSV export ready for your doctor or nutritionist.
*   **🎨 Cyberpunk UI:** A fast, responsive frontend built with Streamlit and styled with custom CSS and interactive Altair charts.

## 🏗️ Architecture

*   **Frontend:** Streamlit (`app.py`) for the UI, state management, and charting (Altair).
*   **Backend:** FastAPI (`backend.py`) for receiving images, orchestrating the multi-model Gemini LLM fallback chain, and parsing Pydantic-structured outputs.
*   **Heuristics API:** Uses Python `requests` to occasionally query HuggingFace dataset APIs for factual ingredient supplementation.

## 🚀 Getting Started

### Prerequisites

You will need a [Google Gemini API Key](https://aistudio.google.com/app/apikey).

Create a `.env` file in the main directory (or parent directory) and add your key:

```env
GEMINI_API_KEY="your_api_key_here"
```

### Installation & Running (Mac/Linux)

Oxia includes automation scripts for easy setup and execution.

1.  **Install Dependencies & Virtual Environment:**
    Run the setup script to initialize a local Python `.venv` and install all required packages.

    ```bash
    ./install.sh
    ```

2.  **Start the Engines:**
    Run the startup script to concurrently launch the FastAPI backend (port `8000`) and the Streamlit frontend (port `8501`).

    ```bash
    ./run.sh
    ```

3.  **Open the App:**
    Navigate to [http://localhost:8501](http://localhost:8501) in your browser.
