"""
Application ports (Protocols) — infrastructure implements these; use cases depend on abstractions only.
"""

from __future__ import annotations

from typing import Any, Protocol


class NutritionLookupPort(Protocol):
    """Multi-source ingredient nutrition (HF, OFF, USDA, etc.)."""

    def lookup_ingredients(self, ingredients: list[str]) -> dict[str, Any]:
        """Return nutritional_truth-shaped dict: dataset_matches, source, sources_breakdown, …"""
        ...


class MealPersistencePort(Protocol):
    """Persist meal analyses and chat turns; enforce meal ownership checks."""

    def store_meal_analysis(self, meal_id: str, analysis: dict[str, Any], user_id: str | None) -> None: ...

    def get_analysis(self, meal_id: str) -> dict[str, Any] | None: ...

    def get_meal_user_id(self, meal_id: str) -> str | None: ...

    def get_recent_analyses(self, limit: int, user_id: str | None) -> list[dict[str, Any]]: ...

    def delete_meal_analysis(self, meal_id: str, user_id: str) -> bool: ...

    def store_chat_turn(
        self,
        turn_id: str,
        meal_id: str,
        question: str,
        answer: str,
        focus_metric: str | None,
    ) -> None: ...


class UserPersistencePort(Protocol):
    """User accounts for JWT auth."""

    def get_user_by_username(self, username: str) -> dict[str, Any] | None: ...

    def store_user(self, *, user_id: str, username: str, password_hash: str) -> None: ...


class ProviderRegistryPort(Protocol):
    """Resolve reasoning_model string → (LLM provider, provider-specific model id)."""

    def get_provider_and_model(self, reasoning_model: str) -> tuple[Any, str]: ...
