from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Model-agnostic interface for Oxia's LLM capabilities."""

    # Whether the provider can consume an image during analysis.
    supports_vision: bool = False

    @abstractmethod
    def generate_meal_analysis(self, *, image: Any, reasoning_model: str) -> Any:
        """Return a validated structured analysis result."""
        raise NotImplementedError

    def chat(self, *, context_packet: dict[str, Any], question: str, reasoning_model: str) -> Any:
        """Optional: implemented by providers that support metric-aware chat."""
        raise NotImplementedError

