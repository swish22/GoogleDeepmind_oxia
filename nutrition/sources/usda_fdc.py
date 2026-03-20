"""
USDA FoodData Central — free API key (or DEMO_KEY with strict rate limits).
https://fdc.nal.usda.gov/api-guide.html
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

DATA_SOURCE = "usda_fdc"
SOURCE_LABEL = "USDA FoodData Central"

SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
FOOD_URL = "https://api.nal.usda.gov/fdc/v1/food"


def _fdc_api_key() -> str | None:
    k = (os.getenv("USDA_FDC_API_KEY") or "").strip()
    if k:
        return k
    return (os.getenv("USDA_FDC_DEMO_KEY") or "DEMO_KEY").strip() or None


def _nutrient_entry_name_unit_value(fn: dict[str, Any]) -> tuple[str, str, float]:
    """Normalize FDC search vs. detail nutrient shapes."""
    if "nutrientName" in fn or fn.get("nutrient") is None:
        name = str(fn.get("nutrientName") or "")
        unit = str(fn.get("unitName") or "")
        try:
            val = float(fn.get("value") or 0)
        except (TypeError, ValueError):
            val = 0.0
        return name.lower(), unit.upper(), val
    nut = fn.get("nutrient") or {}
    name = str(nut.get("name") or "")
    unit = str(nut.get("unitName") or "")
    try:
        val = float(fn.get("amount") or 0)
    except (TypeError, ValueError):
        val = 0.0
    return name.lower(), unit.upper(), val


def _accumulate_from_nutrients(food_nutrients: list[dict[str, Any]] | None) -> dict[str, float]:
    out = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    if not food_nutrients:
        return out
    for fn in food_nutrients:
        name, unit, val = _nutrient_entry_name_unit_value(fn)
        if val <= 0:
            continue
        if "protein" in name:
            out["protein"] = max(out["protein"], val)
        elif "carbohydrate" in name and "fiber" not in name:
            out["carbs"] = max(out["carbs"], val)
        elif "total lipid" in name or "total fat" in name:
            out["fat"] = max(out["fat"], val)
        elif "energy" in name or "calorie" in name:
            if unit == "KJ":
                out["calories"] = max(out["calories"], val / 4.184)
            else:
                out["calories"] = max(out["calories"], val)
    return out


def _fetch_food_detail(fdc_id: int, api_key: str) -> dict[str, Any] | None:
    try:
        res = requests.get(f"{FOOD_URL}/{fdc_id}", params={"api_key": api_key}, timeout=12)
        if res.status_code != 200:
            return None
        return res.json()
    except Exception as e:
        logger.debug("USDA FDC detail fetch failed for %s: %s", fdc_id, e)
        return None


def lookup_ingredient_usda_fdc(ingredient: str, norm: str) -> dict[str, Any] | None:
    key = _fdc_api_key()
    if not key or not norm:
        return None
    try:
        res = requests.get(
            SEARCH_URL,
            params=[
                ("api_key", key),
                ("query", norm[:200]),
                ("pageSize", "1"),
                ("dataType", "Foundation"),
                ("dataType", "SR Legacy"),
                ("dataType", "Survey (FNDDS)"),
                ("dataType", "Branded"),
            ],
            timeout=10,
        )
        if res.status_code != 200:
            logger.debug("USDA FDC search HTTP %s", res.status_code)
            return None
        payload = res.json()
        foods = payload.get("foods") or []
        if not foods:
            return None
        f0 = foods[0]
        desc = (f0.get("description") or f0.get("lowercaseDescription") or ingredient).strip()
        nutrients = _accumulate_from_nutrients(f0.get("foodNutrients"))

        if (
            nutrients["calories"] <= 0
            and nutrients["protein"] <= 0
            and nutrients["carbs"] <= 0
            and nutrients["fat"] <= 0
        ):
            fdc_id = f0.get("fdcId")
            if isinstance(fdc_id, int):
                detail = _fetch_food_detail(fdc_id, key)
                if detail:
                    nutrients = _accumulate_from_nutrients(detail.get("foodNutrients"))

        if (
            nutrients["calories"] <= 0
            and nutrients["protein"] <= 0
            and nutrients["carbs"] <= 0
            and nutrients["fat"] <= 0
        ):
            return None

        return {
            "name": desc[:200],
            "calories": round(nutrients["calories"], 2),
            "protein": round(nutrients["protein"], 2),
            "carbs": round(nutrients["carbs"], 2),
            "fat": round(nutrients["fat"], 2),
            "grams": 100.0,
            "data_source": DATA_SOURCE,
            "data_source_label": SOURCE_LABEL,
            "portion_note": "USDA FDC (per 100 g / label basis — confirm entry in FDC)",
        }
    except Exception as e:
        logger.debug("USDA FDC lookup failed for %s: %s", ingredient, e)
        return None
