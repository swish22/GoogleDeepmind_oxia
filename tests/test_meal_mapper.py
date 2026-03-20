"""Pure application-layer mapper (no HTTP)."""

from models import FlatMealAnalysisResult
from oxia.application.mappers import flat_meal_to_analysis_dict


def _minimal_flat() -> FlatMealAnalysisResult:
    return FlatMealAnalysisResult(
        meal_name="Test Bowl",
        ingredients=["rice", "egg"],
        estimated_glycemic_load=42.0,
        micro_nutrient_density="Moderate",
        macro_carbs_g=50,
        macro_protein_g=20,
        macro_fat_g=10,
        macro_fiber_g=3,
        macro_fruits_veg_g=5,
        ga_peak_glucose=140,
        ga_spike_time_mins=45,
        ga_glucose_0=90,
        ga_glucose_15=100,
        ga_glucose_30=120,
        ga_glucose_45=135,
        ga_glucose_60=130,
        ga_glucose_90=110,
        ga_glucose_120=95,
        ga_glucose_150=90,
        ga_glucose_180=88,
        ga_architect_insight="Architect",
        ih_stress_score=3,
        ih_hidden_disruptors=[],
        ih_disruptors_detected=False,
        ih_hunter_insight="Hunter",
        pg_brain_fog_risk="Low",
        pg_deep_work_window_mins=90,
        pg_ghost_insight="Ghost",
        cs_state_label="Focus",
        cs_state_emoji="🎯",
        cs_duration_mins=60,
        holistic_health_insight="OK",
        optimization_suggestions=["Swap A → B"],
    )


def test_mapper_nested_keys():
    d = flat_meal_to_analysis_dict(_minimal_flat())
    assert d["meal_name"] == "Test Bowl"
    assert d["macro_breakdown"]["carbs_g"] == 50
    assert len(d["glucose_architect"]["glucose_curve"]) == 9
    assert d["glucose_architect"]["glucose_curve"][0]["time_mins"] == 0
    assert d["optimization_suggestions"] == ["Swap A → B"]


def test_mapper_empty_optimization_default():
    flat = _minimal_flat()
    flat = flat.model_copy(update={"optimization_suggestions": []})
    d = flat_meal_to_analysis_dict(flat)
    assert d["optimization_suggestions"] == []
