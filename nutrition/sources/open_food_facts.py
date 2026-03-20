"""
Open Food Facts — free global database (no API key).
https://openfoodfacts.github.io/openfoodfacts-server/api/
Uses search with a descriptive User-Agent per project etiquette.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

DATA_SOURCE = "open_food_facts"
SOURCE_LABEL = "Open Food Facts (openfoodfacts.org)"

OFF_HEADERS = {
    "User-Agent": "OxiaMetabolicTwin/1.0 (https://github.com/oxia; nutrition-ingredient-lookup)",
    "Accept": "application/json",
}

SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"


def _num(nut: dict[str, Any], *keys: str) -> float:
    for k in keys:
        v = nut.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return 0.0


def lookup_ingredient_open_food_facts(ingredient: str, norm: str) -> dict[str, Any] | None:
    """Best-effort match from OFF search (per-100g nutriments when available)."""
    if not norm:
        return None
    try:
        params = {
            "search_terms": norm[:120],
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 1,
        }
        res = requests.get(SEARCH_URL, params=params, headers=OFF_HEADERS, timeout=8)
        if res.status_code != 200:
            return None
        data = res.json()
        products = data.get("products") or []
        if not products:
            return None
        p = products[0]
        name = (p.get("product_name") or ingredient or norm).strip() or norm
        nut = p.get("nutriments") or {}
        cal = _num(nut, "energy-kcal_100g", "energy-kcal", "energy_kcal_100g")
        # Some products only report kJ
        if cal <= 0:
            kj = _num(nut, "energy-kj_100g", "energy_kj_100g")
            if kj > 0:
                cal = round(kj / 4.184, 2)
        protein = _num(nut, "proteins_100g", "proteins")
        carbs = _num(nut, "carbohydrates_100g", "carbohydrates")
        fat = _num(nut, "fat_100g", "fat")
        if cal <= 0 and protein <= 0 and carbs <= 0 and fat <= 0:
            return None
        return {
            "name": name[:200],
            "calories": round(cal, 2) if cal > 0 else 0.0,
            "protein": round(protein, 2),
            "carbs": round(carbs, 2),
            "fat": round(fat, 2),
            "grams": 100.0,
            "data_source": DATA_SOURCE,
            "data_source_label": SOURCE_LABEL,
            "portion_note": "per 100 g (product average; OFF)",
        }
    except Exception as e:
        logger.debug("Open Food Facts lookup failed for %s: %s", ingredient, e)
        return None
