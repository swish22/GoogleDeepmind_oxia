from __future__ import annotations

from typing import Any


def detect_focus_metric(question: str) -> str:
    q = (question or "").lower()

    if any(k in q for k in ["swap", "optimize", "improve", "replace", "better", "tweak"]):
        return "optimization"
    if any(k in q for k in ["brain", "fog", "focus", "deep work", "cognitive", "work window"]):
        return "performance"
    if any(k in q for k in ["protein", "carb", "carbs", "fat", "calorie", "fiber", "nutrition", "macro"]):
        return "nutrition"
    if any(k in q for k in ["glucose", "blood sugar", "spike", "peak", "glycemic"]):
        return "glucose"
    if any(k in q for k in ["inflammation", "stress", "disruptor", "seed oil", "sugar", "additive"]):
        return "inflammation"

    # Default to glucose context (most users ask about glucose).
    return "glucose"


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def build_context_packet(
    *,
    analysis: dict[str, Any],
    history_analyses: list[dict[str, Any]],
    focus_metric: str,
) -> dict[str, Any]:
    focus_metric = focus_metric or "glucose"

    ga = analysis.get("glucose_architect", {}) or {}
    ih = analysis.get("inflammation_hunter", {}) or {}
    pg = analysis.get("performance_ghost", {}) or {}
    cs = (pg.get("cognitive_state", {}) or {}) if isinstance(pg, dict) else {}
    mb = analysis.get("macro_breakdown", {}) or {}
    truth = analysis.get("nutritional_truth", {}) or {}
    matches = truth.get("dataset_matches", []) or []
    opts = analysis.get("optimization_suggestions", []) or []

    # Keep curve sparse to limit prompt size.
    curve = ga.get("glucose_curve", []) or []
    sparse_curve = []
    for t in [0, 15, 30, 45, 60, 90, 120, 180]:
        for pt in curve:
            if pt.get("time_mins") == t:
                sparse_curve.append({"t": t, "g": pt.get("glucose_mg_dl")})
                break

    history_summary: dict[str, Any] = {}
    if history_analyses:
        # Numeric stability: just compute averages and counts.
        stress_vals = [
            (h.get("inflammation_hunter", {}) or {}).get("stress_score", 0)
            for h in history_analyses
            if isinstance(h, dict)
        ]
        stress_vals = [v for v in stress_vals if isinstance(v, (int, float))]
        avg_stress = sum(stress_vals) / len(stress_vals) if stress_vals else None

        bf_risks = []
        for h in history_analyses:
            bf = ((h.get("performance_ghost", {}) or {}) or {}).get("brain_fog_risk")
            if isinstance(bf, str):
                bf_risks.append(bf)

        history_summary = {
            "avg_stress_score": avg_stress,
            "brain_fog_risk_counts": {
                "Low": bf_risks.count("Low"),
                "Medium": bf_risks.count("Medium"),
                "High": bf_risks.count("High"),
            },
            "meals_in_history": len(history_analyses),
        }

    packet: dict[str, Any] = {
        "focus_metric": focus_metric,
        "meal": {
            "meal_name": analysis.get("meal_name"),
        },
    }

    if focus_metric == "glucose":
        packet["glucose"] = {
            "estimated_glycemic_load": _safe_float(analysis.get("estimated_glycemic_load")),
            "peak_glucose": ga.get("peak_glucose"),
            "spike_time_mins": ga.get("spike_time_mins"),
            "curve_sparse": sparse_curve,
            "architect_insight": ga.get("architect_insight"),
        }
    elif focus_metric == "inflammation":
        packet["inflammation"] = {
            "stress_score": ih.get("stress_score"),
            "disruptors_detected": ih.get("disruptors_detected"),
            "hidden_disruptors_top": (ih.get("hidden_disruptors") or [])[:4],
            "hunter_insight": ih.get("hunter_insight"),
        }
    elif focus_metric == "performance":
        packet["performance"] = {
            "brain_fog_risk": pg.get("brain_fog_risk"),
            "deep_work_window_mins": pg.get("deep_work_window_mins"),
            "state_label": cs.get("state_label"),
            "state_duration_mins": cs.get("duration_mins"),
            "ghost_insight": pg.get("ghost_insight"),
        }
    elif focus_metric == "nutrition":
        packet["nutrition"] = {
            "macro_breakdown_g": {
                "carbs": mb.get("carbs_g"),
                "protein": mb.get("protein_g"),
                "fat": mb.get("fat_g"),
                "fiber": mb.get("fiber_g"),
                "fruits_veg": mb.get("fruits_veg_g"),
            },
            "top_nutritional_matches": [
                {
                    "name": m.get("name"),
                    "calories": m.get("calories"),
                    "protein": m.get("protein"),
                    "carbs": m.get("carbs"),
                    "fat": m.get("fat"),
                    "grams": m.get("grams"),
                    "data_source": m.get("data_source"),
                }
                for m in matches[:4]
            ],
        }
    elif focus_metric == "optimization":
        packet["optimization"] = {
            "optimization_suggestions_top": opts[:3],
            "holistic_health_insight": analysis.get("holistic_health_insight"),
        }
    else:
        packet["glucose"] = {
            "estimated_glycemic_load": _safe_float(analysis.get("estimated_glycemic_load")),
            "peak_glucose": ga.get("peak_glucose"),
            "spike_time_mins": ga.get("spike_time_mins"),
            "curve_sparse": sparse_curve,
        }
        packet["inflammation"] = {"stress_score": ih.get("stress_score")}
        packet["performance"] = {
            "brain_fog_risk": pg.get("brain_fog_risk"),
            "deep_work_window_mins": pg.get("deep_work_window_mins"),
        }

    if history_summary:
        packet["history_summary"] = history_summary

    return packet

