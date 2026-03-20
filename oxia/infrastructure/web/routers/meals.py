from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any

import requests
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from auth import get_current_user
from oxia.application.constants import ANALYSIS_UNAVAILABLE
from oxia.domain.errors import UnsupportedVisionModelError
from oxia.infrastructure.model_catalog import default_gemini_vision_model
from oxia.infrastructure.services.meal_pipeline import decode_and_resize_image, run_meal_analysis_sync
from oxia.infrastructure.web.deps import ContainerDep

logger = logging.getLogger(__name__)
router = APIRouter(tags=["meals"])


@router.post("/analyze_meal")
async def analyze_meal(
    current_user: Annotated[dict, Depends(get_current_user)],
    container: ContainerDep,
    file: UploadFile = File(...),
    reasoning_model: str = Form(default=default_gemini_vision_model()),
) -> dict:
    """
    Multimodal meal analysis — latency dominated by LLM + nutrition I/O (seconds), not this route overhead.
    Heavy work runs in a thread pool to keep the event loop responsive.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    try:
        contents = await file.read()
        img = decode_and_resize_image(contents)
        result = await asyncio.to_thread(
            run_meal_analysis_sync,
            image=img,
            reasoning_model=reasoning_model,
            user_id=current_user["id"],
            container=container,
        )
        return result
    except HTTPException:
        raise
    except UnsupportedVisionModelError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValidationError as e:
        logger.warning("analyze_meal: schema/JSON validation failed model=%s: %s", reasoning_model, e)
        raise HTTPException(status_code=503, detail=ANALYSIS_UNAVAILABLE) from e
    except RuntimeError as e:
        msg = str(e)
        low = msg.lower()
        if "not configured" in low or "gemini_api_key" in low or "missing gemini" in low:
            raise HTTPException(status_code=500, detail=msg) from e
        logger.warning("analyze_meal: runtime error model=%s: %s", reasoning_model, e)
        raise HTTPException(status_code=503, detail=ANALYSIS_UNAVAILABLE) from e
    except requests.RequestException as e:
        logger.warning("analyze_meal: upstream request failed model=%s: %s", reasoning_model, e)
        raise HTTPException(status_code=503, detail=ANALYSIS_UNAVAILABLE) from e
    except Exception as e:
        logger.exception("analyze_meal: unexpected error model=%s", reasoning_model)
        raise HTTPException(status_code=503, detail=ANALYSIS_UNAVAILABLE) from e


@router.get("/meals/recent")
def recent_meals(
    current_user: Annotated[dict, Depends(get_current_user)],
    container: ContainerDep,
) -> list[dict[str, Any]]:
    """List recent saved meal analyses for the logged-in user."""
    return container.meal_persistence.get_recent_analyses(limit=10, user_id=current_user["id"])


@router.get("/meals/{meal_id}")
def get_meal(
    meal_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    container: ContainerDep,
) -> dict[str, Any]:
    owner_id = container.meal_persistence.get_meal_user_id(meal_id)
    if owner_id is None:
        raise HTTPException(status_code=404, detail="Meal not found.")
    if owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized for this meal.")
    analysis = container.meal_persistence.get_analysis(meal_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Meal analysis not found.")
    return analysis


@router.delete("/meals/{meal_id}")
def delete_meal(
    meal_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    container: ContainerDep,
) -> dict[str, Any]:
    owner_id = container.meal_persistence.get_meal_user_id(meal_id)
    if owner_id is None:
        raise HTTPException(status_code=404, detail="Meal not found.")
    if owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized for this meal.")
    ok = container.meal_persistence.delete_meal_analysis(meal_id, user_id=current_user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Meal not found.")
    return {"ok": True}


@router.post("/meals/{meal_id}/snapshot")
def save_meal_snapshot(
    meal_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    container: ContainerDep,
    analysis: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    """
    Persist an updated dashboard snapshot for a meal analysis.
    Used when the user refreshes ingredient evidence (nutrition truth) and wants it saved.
    """
    owner_id = container.meal_persistence.get_meal_user_id(meal_id)
    if owner_id is not None and owner_id != current_user["id"]:
        # If the meal exists but belongs to someone else, do not allow overwrite.
        raise HTTPException(status_code=403, detail="Not authorized for this meal.")

    # Ensure internal consistency.
    analysis = dict(analysis)
    analysis["meal_id"] = meal_id
    container.meal_persistence.store_meal_analysis(meal_id, analysis, user_id=current_user["id"])
    return {"ok": True}
