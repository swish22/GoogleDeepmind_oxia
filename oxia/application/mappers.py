"""
Pure transformations: FlatMealAnalysisResult → nested API analysis dict.

No I/O — 100% unit-testable.
"""

from __future__ import annotations

from typing import Any

from models import FlatMealAnalysisResult


def flat_meal_to_analysis_dict(flat_result: FlatMealAnalysisResult) -> dict[str, Any]:
    """Map flat LLM schema to nested dashboard / client contract."""
    return {
        "meal_name": flat_result.meal_name,
        "ingredients": flat_result.ingredients,
        "estimated_glycemic_load": flat_result.estimated_glycemic_load,
        "micro_nutrient_density": flat_result.micro_nutrient_density,
        "macro_breakdown": {
            "carbs_g": flat_result.macro_carbs_g,
            "protein_g": flat_result.macro_protein_g,
            "fat_g": flat_result.macro_fat_g,
            "fiber_g": flat_result.macro_fiber_g,
            "fruits_veg_g": flat_result.macro_fruits_veg_g,
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
            "architect_insight": flat_result.ga_architect_insight,
        },
        "inflammation_hunter": {
            "stress_score": flat_result.ih_stress_score,
            "hidden_disruptors": flat_result.ih_hidden_disruptors,
            "disruptors_detected": flat_result.ih_disruptors_detected,
            "hunter_insight": flat_result.ih_hunter_insight,
        },
        "performance_ghost": {
            "brain_fog_risk": flat_result.pg_brain_fog_risk,
            "deep_work_window_mins": flat_result.pg_deep_work_window_mins,
            "ghost_insight": flat_result.pg_ghost_insight,
            "cognitive_state": {
                "state_label": flat_result.cs_state_label,
                "state_emoji": flat_result.cs_state_emoji,
                "duration_mins": flat_result.cs_duration_mins,
            },
        },
        "holistic_health_insight": flat_result.holistic_health_insight,
        "optimization_suggestions": getattr(flat_result, "optimization_suggestions", []) or [],
    }
