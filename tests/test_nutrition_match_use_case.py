"""Application-layer nutrition match (port + aggregates → NutritionMatchResponse)."""

from __future__ import annotations

from typing import Any

from oxia.application.nutrition_match import build_nutrition_match_response


class _FakeNutritionLookup:
    def lookup_ingredients(self, ingredients: list[str]) -> dict[str, Any]:
        return {
            "source": "stub",
            "dataset_matches": [
                {
                    "query": ingredients[0],
                    "calories": 100.0,
                    "protein": 5.0,
                    "carbs": 15.0,
                    "fat": 2.0,
                    "grams": 100.0,
                }
            ],
            "sources_breakdown": {"stub": 1},
        }


def test_build_nutrition_match_response_uses_port_and_aggregates():
    out = build_nutrition_match_response(_FakeNutritionLookup(), ["oats"])
    assert out.source == "stub"
    assert len(out.dataset_matches) == 1
    assert out.sources_breakdown == {"stub": 1}
    assert out.aggregates["total_calories"] == 100.0
    assert out.aggregates["match_count"] == 1


def test_build_nutrition_match_response_defaults_missing_keys():
    class EmptyLookup:
        def lookup_ingredients(self, ingredients: list[str]) -> dict[str, Any]:
            return {}

    out = build_nutrition_match_response(EmptyLookup(), ["x"])
    assert out.source == ""
    assert out.dataset_matches == []
    assert out.sources_breakdown == {}
    assert out.aggregates["match_count"] == 0
