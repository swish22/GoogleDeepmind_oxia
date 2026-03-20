"""
Coerce messy LLM JSON (Ollama, etc.) into a dict that satisfies FlatMealAnalysisResult.

- Drops unknown keys (e.g. haptic_input).
- Forward-fills missing ga_glucose_* points from the last known value (starts at 85 mg/dL).
- Synthesizes holistic_health_insight when omitted.
"""

from __future__ import annotations

import json
from typing import Any

from models import FlatMealAnalysisResult

# Field order for the 180-minute curve
_GA_CURVE_KEYS = [
    "ga_glucose_0",
    "ga_glucose_15",
    "ga_glucose_30",
    "ga_glucose_45",
    "ga_glucose_60",
    "ga_glucose_90",
    "ga_glucose_120",
    "ga_glucose_150",
    "ga_glucose_180",
]

_ALLOWED = frozenset(FlatMealAnalysisResult.model_fields.keys())


def _to_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ensure_str(v: Any, fallback: str) -> str:
    if v is None:
        return fallback
    s = str(v).strip()
    return s if s else fallback


def coerce_flat_meal_dict(raw: dict[str, Any]) -> dict[str, Any]:
    """Whitelist keys, fix glucose series, fill holistic insight; returns a new dict."""
    out: dict[str, Any] = {k: v for k, v in raw.items() if k in _ALLOWED}

    # --- Glucose curve: forward-fill missing points (common Ollama omission: ga_glucose_180) ---
    fasting = _to_int(out.get("ga_glucose_0")) or 85
    series_present: list[int | None] = []
    for key in _GA_CURVE_KEYS:
        series_present.append(_to_int(out.get(key)))

    prev = fasting
    filled: list[int] = []
    for v in series_present:
        if v is not None:
            prev = v
        filled.append(prev)

    for i, key in enumerate(_GA_CURVE_KEYS):
        if series_present[i] is None:
            out[key] = filled[i]
        else:
            out[key] = series_present[i]

    # --- holistic_health_insight ---
    hi = out.get("holistic_health_insight")
    if hi is None or not str(hi).strip():
        meal = _ensure_str(out.get("meal_name"), "This meal")
        eg = _to_float(out.get("estimated_glycemic_load"))
        eg_s = f"{eg:.1f}" if eg is not None else "n/a"
        chunks = [
            str(out.get("ga_architect_insight") or "").strip(),
            str(out.get("ih_hunter_insight") or "").strip(),
            str(out.get("pg_ghost_insight") or "").strip(),
        ]
        chunks = [c for c in chunks if c]
        if chunks:
            out["holistic_health_insight"] = (
                " ".join(chunks)
                + f" Summary: {meal} — align activity and portions with glycemic load ~{eg_s}; use the swaps below if you want a calmer curve."
            )
        else:
            out["holistic_health_insight"] = (
                f"{meal}: review peak glucose timing and stress score on the dashboard; "
                f"one practical lever is pairing carbs with protein/fiber to blunt the curve (glycemic load ~{eg_s})."
            )

    # --- Light defaults for other common partial outputs ---
    out["meal_name"] = _ensure_str(out.get("meal_name"), "Unnamed meal")
    if not out.get("ingredients") or not isinstance(out.get("ingredients"), list):
        out["ingredients"] = ["unidentified"]
    else:
        out["ingredients"] = [str(x).strip() for x in out["ingredients"] if str(x).strip()]
        if not out["ingredients"]:
            out["ingredients"] = ["unidentified"]

    if _to_float(out.get("estimated_glycemic_load")) is None:
        out["estimated_glycemic_load"] = 40.0
    else:
        out["estimated_glycemic_load"] = float(_to_float(out.get("estimated_glycemic_load")))

    out["micro_nutrient_density"] = _ensure_str(out.get("micro_nutrient_density"), "Moderate")

    for mk in ("macro_carbs_g", "macro_protein_g", "macro_fat_g", "macro_fiber_g", "macro_fruits_veg_g"):
        fv = _to_float(out.get(mk))
        out[mk] = 0.0 if fv is None else float(fv)

    for gk in ("ga_peak_glucose", "ga_spike_time_mins"):
        iv = _to_int(out.get(gk))
        if iv is None:
            out[gk] = 120 if gk == "ga_peak_glucose" else 45
        else:
            out[gk] = iv

    out["ga_architect_insight"] = _ensure_str(
        out.get("ga_architect_insight"),
        "I'm the Glucose Architect. This meal will move glucose in line with the curve shown.",
    )

    iv = _to_int(out.get("ih_stress_score"))
    out["ih_stress_score"] = 5 if iv is None else max(1, min(10, iv))

    hd = out.get("ih_hidden_disruptors")
    if not isinstance(hd, list):
        out["ih_hidden_disruptors"] = []
    else:
        out["ih_hidden_disruptors"] = [str(x).strip() for x in hd if str(x).strip()]

    if out.get("ih_disruptors_detected") is None:
        out["ih_disruptors_detected"] = len(out["ih_hidden_disruptors"]) > 0
    else:
        out["ih_disruptors_detected"] = bool(out["ih_disruptors_detected"])

    out["ih_hunter_insight"] = _ensure_str(
        out.get("ih_hunter_insight"),
        "I'm the Inflammation Hunter. No major disruptors flagged from the listed ingredients.",
    )

    risk = str(out.get("pg_brain_fog_risk") or "").strip()
    if risk not in ("Low", "Medium", "High"):
        out["pg_brain_fog_risk"] = "Medium"
    else:
        out["pg_brain_fog_risk"] = risk

    dw = _to_int(out.get("pg_deep_work_window_mins"))
    out["pg_deep_work_window_mins"] = 45 if dw is None else max(0, dw)

    out["pg_ghost_insight"] = _ensure_str(
        out.get("pg_ghost_insight"),
        "I'm the Performance Ghost. Schedule focused work after the post-meal stabilization window.",
    )

    out["cs_state_label"] = _ensure_str(out.get("cs_state_label"), "Steady Focus")
    out["cs_state_emoji"] = _ensure_str(out.get("cs_state_emoji"), "🧠")
    cd = _to_int(out.get("cs_duration_mins"))
    out["cs_duration_mins"] = 60 if cd is None else max(1, cd)

    osug = out.get("optimization_suggestions")
    if not isinstance(osug, list):
        out["optimization_suggestions"] = []
    else:
        out["optimization_suggestions"] = [str(x).strip() for x in osug if str(x).strip()]

    return out


def flat_meal_from_llm_json_string(json_str: str) -> FlatMealAnalysisResult:
    data = json.loads(json_str)
    if not isinstance(data, dict):
        raise TypeError("LLM JSON root must be an object")
    coerced = coerce_flat_meal_dict(data)
    return FlatMealAnalysisResult.model_validate(coerced)
