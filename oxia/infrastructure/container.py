"""Application composition root (dependency injection without a heavy framework)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from llm.providers.gemini import GeminiProvider
from llm.providers.hf import HFProvider
from llm.providers.ollama import OllamaProvider
from oxia.application.ports import MealPersistencePort, NutritionLookupPort, ProviderRegistryPort, UserPersistencePort
from oxia.infrastructure.adapters.nutrition_lookup_adapter import NutritionLookupAdapter
from oxia.infrastructure.adapters.sqlite_persistence import SqliteMealPersistenceAdapter, SqliteUserPersistenceAdapter


@dataclass(frozen=True, slots=True)
class AppContainer(ProviderRegistryPort):
    gemini_provider: GeminiProvider
    ollama_provider: OllamaProvider
    hf_provider: HFProvider
    meal_persistence: MealPersistencePort
    user_persistence: UserPersistencePort
    nutrition_lookup: NutritionLookupPort

    @staticmethod
    def build() -> AppContainer:
        return AppContainer(
            gemini_provider=GeminiProvider(api_key=os.getenv("GEMINI_API_KEY")),
            ollama_provider=OllamaProvider(base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")),
            hf_provider=HFProvider(hf_token=os.getenv("HF_TOKEN")),
            meal_persistence=SqliteMealPersistenceAdapter(),
            user_persistence=SqliteUserPersistenceAdapter(),
            nutrition_lookup=NutritionLookupAdapter(),
        )

    def get_provider_and_model(self, reasoning_model: str) -> tuple[Any, str]:
        rm = (reasoning_model or "").strip()
        if rm.startswith("ollama:"):
            return self.ollama_provider, rm.split(":", 1)[1]
        if rm.startswith("hf:"):
            return self.hf_provider, rm.split(":", 1)[1]
        return self.gemini_provider, rm
