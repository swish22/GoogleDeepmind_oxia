from __future__ import annotations

import logging
import uuid
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from auth import get_current_user
from chat.context_builder import build_context_packet, detect_focus_metric
from chat.response_safety import ensure_three_suggestions
from models import ChatRequest, ChatResponse
from oxia.application.constants import CHAT_UNAVAILABLE
from oxia.infrastructure.web.deps import ContainerDep

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_req: ChatRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    container: ContainerDep,
) -> ChatResponse:
    provider, model_id = container.get_provider_and_model(chat_req.reasoning_model or "gemini-2.0-flash")
    if provider is container.gemini_provider and not container.gemini_provider.configured:
        raise HTTPException(status_code=500, detail="Gemini Client not configured. Check GEMINI_API_KEY.")

    meal_user_id = container.meal_persistence.get_meal_user_id(chat_req.meal_id)
    if meal_user_id is None:
        raise HTTPException(status_code=404, detail="Meal analysis not found for this meal_id.")
    if meal_user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized for this meal.")

    analysis = container.meal_persistence.get_analysis(chat_req.meal_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Meal analysis not found for this meal_id.")

    focus_metric = chat_req.focus_metric or detect_focus_metric(chat_req.question)
    history_analyses = (
        container.meal_persistence.get_recent_analyses(limit=10, user_id=current_user["id"])
        if chat_req.use_history
        else []
    )
    context_packet = build_context_packet(
        analysis=analysis,
        history_analyses=history_analyses,
        focus_metric=focus_metric,
    )

    try:
        resp = provider.chat(
            context_packet=context_packet,
            question=chat_req.question,
            reasoning_model=model_id,
        )
    except ValidationError as e:
        logger.warning("chat: schema/JSON validation failed model=%s: %s", chat_req.reasoning_model, e)
        raise HTTPException(status_code=503, detail=CHAT_UNAVAILABLE) from e
    except RuntimeError as e:
        msg = str(e)
        low = msg.lower()
        if "not configured" in low or "gemini_api_key" in low:
            raise HTTPException(status_code=500, detail=msg) from e
        logger.warning("chat: runtime error model=%s: %s", chat_req.reasoning_model, e)
        raise HTTPException(status_code=503, detail=CHAT_UNAVAILABLE) from e
    except requests.RequestException as e:
        logger.warning("chat: upstream request failed model=%s: %s", chat_req.reasoning_model, e)
        raise HTTPException(status_code=503, detail=CHAT_UNAVAILABLE) from e
    except Exception:
        logger.exception("chat: unexpected error model=%s", chat_req.reasoning_model)
        raise HTTPException(status_code=503, detail=CHAT_UNAVAILABLE)

    suggestions = ensure_three_suggestions(resp.suggested_questions, focus_metric)
    resp = ChatResponse(answer=resp.answer, suggested_questions=suggestions, focus_metric=focus_metric or "glucose")

    turn_id = uuid.uuid4().hex
    container.meal_persistence.store_chat_turn(
        turn_id=turn_id,
        meal_id=chat_req.meal_id,
        question=chat_req.question,
        answer=resp.answer,
        focus_metric=focus_metric,
    )
    return resp
