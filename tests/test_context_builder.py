from chat.context_builder import build_context_packet, detect_focus_metric


def _sample_analysis():
    return {
        "meal_name": "Test Meal",
        "estimated_glycemic_load": 55.5,
        "micro_nutrient_density": "High",
        "macro_breakdown": {
            "carbs_g": 60,
            "protein_g": 25,
            "fat_g": 10,
            "fiber_g": 8,
            "fruits_veg_g": 5,
        },
        "glucose_architect": {
            "peak_glucose": 150,
            "spike_time_mins": 30,
            "glucose_curve": [
                {"time_mins": t, "glucose_mg_dl": (90 + t * 0.5) if t < 30 else (150 - (t - 30) * 0.2)}
                for t in [0, 15, 30, 45, 60, 90, 120, 150, 180]
            ],
            "architect_insight": "I will peak quickly.",
        },
        "inflammation_hunter": {
            "stress_score": 6,
            "hidden_disruptors": ["refined_sugar"],
            "disruptors_detected": True,
            "hunter_insight": "I detect a disruptor.",
        },
        "performance_ghost": {
            "brain_fog_risk": "Medium",
            "deep_work_window_mins": 60,
            "ghost_insight": "Focus window opens soon.",
            "cognitive_state": {
                "state_label": "Steady Focus",
                "state_emoji": "🧠",
                "duration_mins": 70,
            },
        },
        "holistic_health_insight": "Balanced with a glucose spike.",
        "optimization_suggestions": ["Swap X with Y → -35% glycemic load"],
        "nutritional_truth": {
            "source": "hf",
            "dataset_matches": [
                {"name": "Chicken", "calories": 200, "protein": 30, "carbs": 0, "fat": 5, "grams": 100}
            ],
        },
    }


def test_detect_focus_metric_keywords():
    assert detect_focus_metric("When will my blood sugar peak?") == "glucose"
    assert detect_focus_metric("Inflammation and stress score for this meal") == "inflammation"
    assert detect_focus_metric("Deep work window and brain fog risk") == "performance"
    assert detect_focus_metric("Protein and carb breakdown") == "nutrition"
    assert detect_focus_metric("Any swaps to optimize this meal?") == "optimization"


def test_build_context_packet_focus_keys():
    analysis = _sample_analysis()
    packet = build_context_packet(analysis=analysis, history_analyses=[], focus_metric="glucose")
    assert "glucose" in packet
    assert "inflammation" not in packet

    packet2 = build_context_packet(analysis=analysis, history_analyses=[], focus_metric="inflammation")
    assert "inflammation" in packet2
    assert packet2["inflammation"]["stress_score"] == 6

    packet3 = build_context_packet(analysis=analysis, history_analyses=[], focus_metric="performance")
    assert "performance" in packet3
    assert packet3["performance"]["brain_fog_risk"] == "Medium"

    packet4 = build_context_packet(analysis=analysis, history_analyses=[], focus_metric="nutrition")
    assert "nutrition" in packet4
    assert packet4["nutrition"]["macro_breakdown_g"]["carbs"] == 60

    packet5 = build_context_packet(analysis=analysis, history_analyses=[], focus_metric="optimization")
    assert "optimization" in packet5
    assert len(packet5["optimization"]["optimization_suggestions_top"]) == 1

