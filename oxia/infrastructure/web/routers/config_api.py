from __future__ import annotations

from fastapi import APIRouter

from models import UiModelsConfigResponse
from oxia.infrastructure.model_catalog import (
    build_reasoning_models_list,
    normalized_ollama_env_model,
    ollama_base_url,
)

router = APIRouter(tags=["config"])


@router.get("/config/models", response_model=UiModelsConfigResponse)
def config_models() -> UiModelsConfigResponse:
    """Public model list — fast, no auth."""
    return UiModelsConfigResponse(
        reasoning_models=build_reasoning_models_list(),
        default_ollama_vision=normalized_ollama_env_model(),
        ollama_base_url=ollama_base_url(),
    )
