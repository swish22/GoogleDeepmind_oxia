"""
Backward-compatible entry points for meal nutrition lookup.

Implementation lives in `nutrition/` (multi-source: HF Maressay → Open Food Facts → USDA FDC).
"""

from nutrition import fetch_nutritional_truth, nutrition_aggregates_from_matches

__all__ = ["fetch_nutritional_truth", "nutrition_aggregates_from_matches"]
