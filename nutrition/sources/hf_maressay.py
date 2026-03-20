"""HuggingFace Datasets Server — Maressay/food-nutrients-preparated (primary)."""

from __future__ import annotations

import logging
from typing import Any

import requests
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

DATA_SOURCE = "huggingface_maressay"
SOURCE_LABEL = "HuggingFace: Maressay/food-nutrients-preparated"

DATASET_SEARCH_URL = (
    "https://datasets-server.huggingface.co/search"
    "?dataset=Maressay/food-nutrients-preparated&config=default&split=train&query={query}"
)


def _row_to_match(ingredient_lower: str, recipe_ingredients: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not recipe_ingredients:
        return None
    match = next(
        (item for item in recipe_ingredients if ingredient_lower in (item.get("name") or "").lower()),
        None,
    )
    pick = match or recipe_ingredients[0]
    return {
        "name": pick.get("name"),
        "calories": round(float(pick.get("calories") or 0), 2),
        "protein": round(float(pick.get("protein") or 0), 2),
        "carbs": round(float(pick.get("carb") or 0), 2),
        "fat": round(float(pick.get("fat") or 0), 2),
        "grams": round(float(pick.get("grams") or 0), 2),
        "data_source": DATA_SOURCE,
        "data_source_label": SOURCE_LABEL,
    }


def lookup_ingredient_hf_maressay(ingredient: str, norm: str) -> dict[str, Any] | None:
    """Return a unified match dict or None if HF has no usable row."""
    if not norm:
        return None
    url = DATASET_SEARCH_URL.format(query=quote_plus(norm))
    try:
        res = None
        for _ in range(2):
            res = requests.get(url, timeout=6)
            if res.status_code == 200:
                break
        if res is None or res.status_code != 200:
            return None
        data = res.json()
        rows = data.get("rows") or []
        if not rows:
            return None
        metadata = rows[0].get("row", {}).get("metadata", {}) or {}
        recipe_ingredients = metadata.get("ingredients") or []
        if not recipe_ingredients:
            return None
        m = _row_to_match(ingredient.lower(), recipe_ingredients)
        return m
    except Exception as e:
        logger.debug("HF Maressay lookup failed for %s: %s", ingredient, e)
        return None
