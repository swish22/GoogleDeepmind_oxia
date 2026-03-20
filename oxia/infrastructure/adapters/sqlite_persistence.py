"""SQLite-backed meal + user persistence (wraps legacy `db` module)."""

from __future__ import annotations

from typing import Any

import db as db_module
from oxia.application.ports import MealPersistencePort, UserPersistencePort


class SqliteMealPersistenceAdapter(MealPersistencePort):
    def store_meal_analysis(self, meal_id: str, analysis: dict[str, Any], user_id: str | None) -> None:
        db_module.store_analysis(meal_id, analysis, user_id=user_id)

    def get_analysis(self, meal_id: str) -> dict[str, Any] | None:
        return db_module.get_analysis(meal_id)

    def get_meal_user_id(self, meal_id: str) -> str | None:
        return db_module.get_meal_user_id(meal_id)

    def get_recent_analyses(self, limit: int, user_id: str | None) -> list[dict[str, Any]]:
        return db_module.get_recent_analyses(limit=limit, user_id=user_id)

    def delete_meal_analysis(self, meal_id: str, user_id: str) -> bool:
        return db_module.delete_meal(meal_id, user_id=user_id)

    def store_chat_turn(
        self,
        turn_id: str,
        meal_id: str,
        question: str,
        answer: str,
        focus_metric: str | None,
    ) -> None:
        db_module.store_chat_turn(turn_id, meal_id, question, answer, focus_metric)


class SqliteUserPersistenceAdapter(UserPersistencePort):
    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        return db_module.get_user_by_username(username)

    def store_user(self, *, user_id: str, username: str, password_hash: str) -> None:
        db_module.store_user(user_id=user_id, username=username, password_hash=password_hash)
