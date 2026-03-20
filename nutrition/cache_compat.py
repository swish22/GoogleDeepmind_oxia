"""SQLite cache for resolved ingredient rows (supports legacy bare-dict / [] entries)."""

from __future__ import annotations

from typing import Any

from db import get_nutritional_cache, set_nutritional_cache

CACHE_V2 = 2


def _legacy_is_hit(row: Any) -> bool:
    return isinstance(row, dict) and "calories" in row and row.get("v") != CACHE_V2


def get_resolved_ingredient(norm: str) -> Any | None:
    """
    Returns:
        dict  — cached match (legacy or v2 record)
        "__MISS__" — v2 confirmed miss (all sources failed previously)
        None — not cached (caller should resolve)
    """
    raw = get_nutritional_cache(norm)
    if raw is None:
        return None
    if raw == []:
        # Legacy: HF-only empty; allow re-resolution with new fallbacks.
        return None
    if isinstance(raw, dict) and raw.get("v") == CACHE_V2:
        if raw.get("miss"):
            return "__MISS__"
        rec = raw.get("record")
        return rec if isinstance(rec, dict) else None
    if _legacy_is_hit(raw):
        return raw
    return None


def set_resolved_hit(norm: str, record: dict[str, Any]) -> None:
    set_nutritional_cache(norm, {"v": CACHE_V2, "record": record})


def set_resolved_miss(norm: str) -> None:
    set_nutritional_cache(norm, {"v": CACHE_V2, "miss": True})
