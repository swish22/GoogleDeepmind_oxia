"""Nutrition multi-source lookup (delegates to `nutrition` package)."""

from __future__ import annotations

from typing import Any

from nutrition import fetch_nutritional_truth
from oxia.application.ports import NutritionLookupPort


class NutritionLookupAdapter(NutritionLookupPort):
    def lookup_ingredients(self, ingredients: list[str]) -> dict[str, Any]:
        return fetch_nutritional_truth(ingredients)
