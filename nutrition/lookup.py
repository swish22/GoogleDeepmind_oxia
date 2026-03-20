"""
Resolve ingredient nutrition from multiple free/open sources (source-agnostic API).

Order per ingredient:
  1) HuggingFace — Maressay/food-nutrients-preparated (primary)
  2) Open Food Facts (no key)
  3) USDA FoodData Central (optional USDA_FDC_API_KEY; DEMO_KEY is rate-limited)
"""

from __future__ import annotations

import logging
from typing import Any

from nutrition.cache_compat import get_resolved_ingredient, set_resolved_hit, set_resolved_miss
from nutrition.sources.hf_maressay import SOURCE_LABEL as HF_LABEL, lookup_ingredient_hf_maressay
from nutrition.sources.open_food_facts import SOURCE_LABEL as OFF_LABEL
from nutrition.sources.open_food_facts import lookup_ingredient_open_food_facts
from nutrition.sources.usda_fdc import SOURCE_LABEL as USDA_LABEL
from nutrition.sources.usda_fdc import lookup_ingredient_usda_fdc

logger = logging.getLogger(__name__)

MAX_MATCHES = 5

BANNER_PRIMARY = "Primary: HuggingFace Maressay/food-nutrients-preparated"
BANNER_FALLBACKS = "Fallbacks (no extra keys): Open Food Facts · USDA FoodData Central (set USDA_FDC_API_KEY for best quota)"


def _normalize_ingredient(ingredient: str) -> str:
    if not ingredient:
        return ""
    s = ingredient.strip().lower()
    s = s.replace(".", " ").replace(",", " ")
    s = " ".join(s.split())
    return s


def _ensure_source_tags(m: dict[str, Any]) -> dict[str, Any]:
    out = dict(m)
    if not out.get("data_source"):
        out["data_source"] = "huggingface_maressay"
        out["data_source_label"] = HF_LABEL
    return out


def _resolve_one(ingredient: str, norm: str) -> dict[str, Any] | None:
    """Resolve a single ingredient (uses cache + source chain)."""
    cached = get_resolved_ingredient(norm)
    if cached == "__MISS__":
        return None
    if isinstance(cached, dict):
        return _ensure_source_tags(cached)

    for fn, label in (
        (lookup_ingredient_hf_maressay, HF_LABEL),
        (lookup_ingredient_open_food_facts, OFF_LABEL),
        (lookup_ingredient_usda_fdc, USDA_LABEL),
    ):
        try:
            got = fn(ingredient, norm)
        except Exception as e:
            logger.debug("%s raised for %s: %s", label, ingredient, e)
            got = None
        if got:
            rec = _ensure_source_tags(got)
            set_resolved_hit(norm, rec)
            return rec

    set_resolved_miss(norm)
    return None


def _sources_breakdown(matches: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for m in matches:
        key = str(m.get("data_source") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _human_source_line(breakdown: dict[str, int]) -> str:
    if not breakdown:
        return f"{BANNER_PRIMARY}. {BANNER_FALLBACKS} — no matches for this meal."
    parts = []
    label_by_id = {
        "huggingface_maressay": HF_LABEL,
        "open_food_facts": OFF_LABEL,
        "usda_fdc": USDA_LABEL,
    }
    for sid, n in sorted(breakdown.items(), key=lambda x: -x[1]):
        lab = label_by_id.get(sid, sid)
        parts.append(f"{lab} ({n})")
    return f"{BANNER_PRIMARY}. {BANNER_FALLBACKS}. This meal: " + " · ".join(parts)


def fetch_nutritional_truth(ingredients: list[str]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for ingredient in ingredients:
        if len(results) >= MAX_MATCHES:
            break
        norm = _normalize_ingredient(ingredient)
        if not norm:
            continue
        m = _resolve_one(ingredient, norm)
        if m:
            results.append(m)

    # Retry with first token only (e.g. "cherry tomato" → "cherry") when still empty
    if not results and ingredients:
        for ingredient in ingredients[:3]:
            if len(results) >= MAX_MATCHES:
                break
            simplified = (ingredient.split()[0] if ingredient else "").strip()
            snorm = _normalize_ingredient(simplified)
            if not snorm:
                continue
            m = _resolve_one(ingredient, snorm)
            if m:
                results.append(m)

    bd = _sources_breakdown(results)
    return {
        "dataset_matches": results,
        "source": _human_source_line(bd),
        "sources_breakdown": bd,
    }
