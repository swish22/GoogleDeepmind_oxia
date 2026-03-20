"""Use case: ingredient list → NutritionMatchResponse (no HTTP)."""

from __future__ import annotations

from nutrition import nutrition_aggregates_from_matches
from models import NutritionMatchResponse
from oxia.application.ports import NutritionLookupPort


def build_nutrition_match_response(lookup: NutritionLookupPort, cleaned_ingredients: list[str]) -> NutritionMatchResponse:
    truth = lookup.lookup_ingredients(cleaned_ingredients)
    agg = nutrition_aggregates_from_matches(truth.get("dataset_matches") or [])
    return NutritionMatchResponse(
        source=truth.get("source") or "",
        dataset_matches=truth.get("dataset_matches") or [],
        aggregates=agg,
        sources_breakdown=truth.get("sources_breakdown") or {},
    )
