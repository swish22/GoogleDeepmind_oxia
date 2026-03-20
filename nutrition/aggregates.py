"""Roll-up helpers for verified ingredient matches."""


def nutrition_aggregates_from_matches(matches: list[dict]) -> dict:
    """Sum per-ingredient macros from dataset_matches (best-effort)."""
    cal = 0.0
    p = 0.0
    c = 0.0
    f = 0.0
    g = 0.0
    for m in matches:
        try:
            cal += float(m.get("calories") or 0)
        except (TypeError, ValueError):
            pass
        try:
            p += float(m.get("protein") or 0)
        except (TypeError, ValueError):
            pass
        try:
            c += float(m.get("carbs") or 0)
        except (TypeError, ValueError):
            pass
        try:
            f += float(m.get("fat") or 0)
        except (TypeError, ValueError):
            pass
        try:
            g += float(m.get("grams") or 0)
        except (TypeError, ValueError):
            pass
    return {
        "total_calories": round(cal, 1),
        "total_protein_g": round(p, 2),
        "total_carbs_g": round(c, 2),
        "total_fat_g": round(f, 2),
        "total_grams": round(g, 1),
        "match_count": len(matches),
    }
