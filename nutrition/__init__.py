"""Multi-source ingredient nutrition lookup (HF Maressay primary; open fallbacks)."""

from nutrition.aggregates import nutrition_aggregates_from_matches
from nutrition.lookup import fetch_nutritional_truth

__all__ = ["fetch_nutritional_truth", "nutrition_aggregates_from_matches"]
