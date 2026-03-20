import json

from llm.flat_meal_coerce import coerce_flat_meal_dict, flat_meal_from_llm_json_string
from models import FlatMealAnalysisResult


def test_coerce_fills_missing_ga_glucose_180_and_holistic():
    raw = {
        "meal_name": "Coconut milk",
        "ingredients": ["coconut"],
        "estimated_glycemic_load": 30.0,
        "micro_nutrient_density": "Moderate",
        "macro_carbs_g": 10,
        "macro_protein_g": 2,
        "macro_fat_g": 14,
        "macro_fiber_g": 1,
        "macro_fruits_veg_g": 0,
        "ga_peak_glucose": 120,
        "ga_spike_time_mins": 30,
        "ga_glucose_0": 85,
        "ga_glucose_15": 95,
        "ga_glucose_30": 120,
        "ga_glucose_45": 115,
        "ga_glucose_60": 105,
        "ga_glucose_90": 98,
        "ga_glucose_120": 92,
        "ga_glucose_150": 88,
        # ga_glucose_180 missing
        "ga_architect_insight": "I'm the Glucose Architect. Curve completes by 3h.",
        "ih_stress_score": 4,
        "ih_hidden_disruptors": [],
        "ih_disruptors_detected": False,
        "ih_hunter_insight": "I'm the Inflammation Hunter. Clean.",
        "pg_brain_fog_risk": "Low",
        "pg_deep_work_window_mins": 60,
        "pg_ghost_insight": "I'm the Performance Ghost. Steady focus.",
        "cs_state_label": "Steady Focus",
        "cs_state_emoji": "🧠",
        "cs_duration_mins": 55,
        # holistic_health_insight missing
        "optimization_suggestions": ["Swap A with B → -10% GL"],
        "haptic_input": None,
    }
    coerced = coerce_flat_meal_dict(raw)
    assert "haptic_input" not in coerced
    assert coerced["ga_glucose_180"] == 88  # forward-filled from 150
    assert "holistic_health_insight" in coerced
    assert len(coerced["holistic_health_insight"]) > 20

    FlatMealAnalysisResult.model_validate(coerced)


def test_flat_meal_from_llm_json_string_roundtrip():
    raw = {
        "meal_name": "X",
        "ingredients": ["y"],
        "estimated_glycemic_load": 50,
        "micro_nutrient_density": "High",
        "macro_carbs_g": 1,
        "macro_protein_g": 1,
        "macro_fat_g": 1,
        "macro_fiber_g": 1,
        "macro_fruits_veg_g": 1,
        "ga_peak_glucose": 130,
        "ga_spike_time_mins": 45,
        "ga_glucose_0": 85,
        "ga_glucose_15": 85,
        "ga_glucose_30": 85,
        "ga_glucose_45": 85,
        "ga_glucose_60": 85,
        "ga_glucose_90": 85,
        "ga_glucose_120": 85,
        "ga_glucose_150": 85,
        "ga_glucose_180": 85,
        "ga_architect_insight": "I'm the Glucose Architect. Test.",
        "ih_stress_score": 5,
        "ih_hidden_disruptors": [],
        "ih_disruptors_detected": False,
        "ih_hunter_insight": "I'm the Inflammation Hunter. Test.",
        "pg_brain_fog_risk": "Low",
        "pg_deep_work_window_mins": 30,
        "pg_ghost_insight": "I'm the Performance Ghost. Test.",
        "cs_state_label": "A",
        "cs_state_emoji": "🙂",
        "cs_duration_mins": 30,
        "holistic_health_insight": "One two three.",
        "optimization_suggestions": [],
    }
    s = json.dumps(raw)
    m = flat_meal_from_llm_json_string(s)
    assert m.meal_name == "X"
    assert m.ga_glucose_180 == 85
