from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import io
import os

from models import FlatMealAnalysisResult
from heuristics import fetch_nutritional_truth

load_dotenv(dotenv_path="../.env")

app = FastAPI(title="Oxia Metabolic Digital Twin Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Warning: Failed to initialize Gemini client. Ensure GEMINI_API_KEY is set: {e}")
    client = None

SYSTEM_PROMPT = """
Act as the 'Medical Archetype' intelligence engine for Oxia: The Metabolic Digital Twin.
Analyze the provided food image with clinical precision.

Your output must include:

1. Meal Identification
   - Identify the meal by name (meal_name).
   - List the identifiable ingredients.

2. Macro Breakdown
   - Estimate macro_carbs_g, macro_protein_g, macro_fat_g, macro_fiber_g, and macro_fruits_veg_g.

3. Glycemic Analysis (The Glucose Architect)
   - Estimate estimated_glycemic_load (0-100 scale).
   - Predict a 180-minute blood glucose curve with readings at: 0, 15, 30, 45, 60, 90, 120, 150, 180 minutes.
   - Normal fasting is ~85 mg/dL. Model realistic spike and recovery.
   - Provide ga_peak_glucose, ga_spike_time_mins, and a one-sentence ga_architect_insight.

4. Inflammation Analysis (The Inflammation Hunter)
   - Identify ACTUAL metabolic disruptors present in the ingredients (e.g. refined sugars, seed oils, trans fats, artificial additives).
   - Set ih_disruptors_detected to true ONLY if real disruptors are found in the listed ingredients.
   - Give an ih_stress_score (1-10) and a one-sentence ih_hunter_insight.

5. Cognitive Performance (The Performance Ghost)
   - Based on the macro ratios, compute a cognitive state with a cs_state_label, cs_state_emoji, and cs_duration_mins.
   - Labels should be one of: 'Peak Flow', 'Steady Focus', 'Post-Meal Dip', 'Brain Fog Alert'.
   - Estimate pg_deep_work_window_mins and pg_brain_fog_risk ('Low', 'Medium', 'High').
   - Provide a one-sentence pg_ghost_insight.

6. Holistic Health Insight
   - Write a 2-3 sentence medically-grounded synthesis of the overall meal (holistic_health_insight).

Return ONLY a JSON object matching the requested flat schema. Be precise, medically rigorous, and data-driven.
"""

# Ordered fallback chain — first available model wins
FALLBACK_CHAIN = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]

@app.post("/analyze_meal")
async def analyze_meal(file: UploadFile = File(...), model_name: str = Form("gemini-2.5-flash")):
    """Analyze a meal photo using Google Gemini and return structured metabolic data."""
    if client is None:
        raise HTTPException(status_code=500, detail="Gemini Client not configured. Check GEMINI_API_KEY.")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        # Build ordered list: chosen model first, then fallbacks
        candidates = [model_name] + [m for m in FALLBACK_CHAIN if m != model_name]
        actual_model = candidates[0]
        last_err = None
        for candidate in candidates:
            try:
                response = client.models.generate_content(
                    model=candidate,
                    contents=[SYSTEM_PROMPT, img],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=FlatMealAnalysisResult,
                        temperature=0.15,
                    ),
                )
                
                flat_result = FlatMealAnalysisResult.model_validate_json(response.text)
                
                # Repackage into nested structure
                result_dict = {
                    "meal_name": flat_result.meal_name,
                    "ingredients": flat_result.ingredients,
                    "estimated_glycemic_load": flat_result.estimated_glycemic_load,
                    "micro_nutrient_density": flat_result.micro_nutrient_density,
                    "macro_breakdown": {
                        "carbs_g": flat_result.macro_carbs_g,
                        "protein_g": flat_result.macro_protein_g,
                        "fat_g": flat_result.macro_fat_g,
                        "fiber_g": flat_result.macro_fiber_g,
                        "fruits_veg_g": flat_result.macro_fruits_veg_g
                    },
                    "glucose_architect": {
                        "peak_glucose": flat_result.ga_peak_glucose,
                        "spike_time_mins": flat_result.ga_spike_time_mins,
                        "glucose_curve": [
                            {"time_mins": 0, "glucose_mg_dl": flat_result.ga_glucose_0},
                            {"time_mins": 15, "glucose_mg_dl": flat_result.ga_glucose_15},
                            {"time_mins": 30, "glucose_mg_dl": flat_result.ga_glucose_30},
                            {"time_mins": 45, "glucose_mg_dl": flat_result.ga_glucose_45},
                            {"time_mins": 60, "glucose_mg_dl": flat_result.ga_glucose_60},
                            {"time_mins": 90, "glucose_mg_dl": flat_result.ga_glucose_90},
                            {"time_mins": 120, "glucose_mg_dl": flat_result.ga_glucose_120},
                            {"time_mins": 150, "glucose_mg_dl": flat_result.ga_glucose_150},
                            {"time_mins": 180, "glucose_mg_dl": flat_result.ga_glucose_180},
                        ],
                        "architect_insight": flat_result.ga_architect_insight
                    },
                    "inflammation_hunter": {
                        "stress_score": flat_result.ih_stress_score,
                        "hidden_disruptors": flat_result.ih_hidden_disruptors,
                        "disruptors_detected": flat_result.ih_disruptors_detected,
                        "hunter_insight": flat_result.ih_hunter_insight
                    },
                    "performance_ghost": {
                        "brain_fog_risk": flat_result.pg_brain_fog_risk,
                        "deep_work_window_mins": flat_result.pg_deep_work_window_mins,
                        "ghost_insight": flat_result.pg_ghost_insight,
                        "cognitive_state": {
                            "state_label": flat_result.cs_state_label,
                            "state_emoji": flat_result.cs_state_emoji,
                            "duration_mins": flat_result.cs_duration_mins
                        }
                    },
                    "holistic_health_insight": flat_result.holistic_health_insight
                }
                
                # Fetch nutritional truth based on ingredients
                truth = fetch_nutritional_truth(flat_result.ingredients)
                
                # Append to the final payload
                result_dict["nutritional_truth"] = truth
                
                return result_dict
            except Exception as e:
                print(f"Model {candidate} generated error: {e}")
                if "404" in str(e) or "NOT_FOUND" in str(e):
                    last_err = e
                    continue
                raise
        raise last_err
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
