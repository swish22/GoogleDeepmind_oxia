"""Nutrition roll-ups used by analyze_meal / diet log."""

from nutrition.aggregates import nutrition_aggregates_from_matches


def test_aggregates_empty():
    assert nutrition_aggregates_from_matches([]) == {
        "total_calories": 0.0,
        "total_protein_g": 0.0,
        "total_carbs_g": 0.0,
        "total_fat_g": 0.0,
        "total_grams": 0.0,
        "match_count": 0,
    }


def test_aggregates_sums_and_rounding():
    matches = [
        {"calories": 100.556, "protein": 10.2, "carbs": 5, "fat": 2.25, "grams": 100},
        {"calories": 50, "protein": 1, "carbs": 0, "fat": 0, "grams": 50},
    ]
    out = nutrition_aggregates_from_matches(matches)
    assert out["total_calories"] == 150.6
    assert out["total_protein_g"] == 11.2
    assert out["total_carbs_g"] == 5.0
    assert out["total_fat_g"] == 2.25
    assert out["total_grams"] == 150.0
    assert out["match_count"] == 2


def test_aggregates_ignores_bad_cells():
    matches = [
        {"calories": "x", "protein": None, "carbs": 3, "fat": 1, "grams": 10},
    ]
    out = nutrition_aggregates_from_matches(matches)
    assert out["total_calories"] == 0.0
    assert out["total_protein_g"] == 0.0
    assert out["total_carbs_g"] == 3.0
    assert out["match_count"] == 1
