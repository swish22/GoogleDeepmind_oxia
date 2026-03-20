"""Decode image → LLM → map → nutrition fuse → persist."""

from __future__ import annotations

import io
import logging
import uuid
from typing import Any

from PIL import Image

from nutrition import nutrition_aggregates_from_matches
from models import FlatMealAnalysisResult
from oxia.application.mappers import flat_meal_to_analysis_dict
from oxia.domain.errors import UnsupportedVisionModelError
from oxia.infrastructure.container import AppContainer

logger = logging.getLogger(__name__)

MAX_IMAGE_DIM = 1024


def decode_and_resize_image(contents: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(contents)).convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_IMAGE_DIM:
        ratio = MAX_IMAGE_DIM / max(w, h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    return img


def run_meal_analysis_sync(
    *,
    image: Image.Image,
    reasoning_model: str,
    user_id: str,
    container: AppContainer,
) -> dict[str, Any]:
    """
    Synchronous vision + nutrition pipeline (CPU-bound + blocking HTTP).
    Called from async route via threadpool in router if needed.
    """
    provider, model_id = container.get_provider_and_model(reasoning_model)
    if provider is container.gemini_provider and not container.gemini_provider.configured:
        raise RuntimeError("Gemini Client not configured. Check GEMINI_API_KEY.")
    if not provider.supports_vision:
        raise UnsupportedVisionModelError(
            "Selected model is chat-only. Use Gemini or Ollama for meal photo analysis."
        )

    flat_result: FlatMealAnalysisResult = provider.generate_meal_analysis(
        image=image,
        reasoning_model=model_id,
    )
    result_dict = flat_meal_to_analysis_dict(flat_result)
    truth = container.nutrition_lookup.lookup_ingredients(flat_result.ingredients)
    truth["aggregates"] = nutrition_aggregates_from_matches(truth.get("dataset_matches") or [])
    result_dict["nutritional_truth"] = truth
    meal_id = uuid.uuid4().hex
    container.meal_persistence.store_meal_analysis(meal_id, result_dict, user_id=user_id)
    result_dict["meal_id"] = meal_id
    return result_dict
