from __future__ import annotations


class OxiaDomainError(Exception):
    """Base for domain-level failures (no HTTP semantics)."""


class MealAnalysisError(OxiaDomainError):
    """Meal vision / parsing could not produce a valid structured result."""


class UnsupportedVisionModelError(OxiaDomainError):
    """Selected reasoning model cannot analyze images."""
