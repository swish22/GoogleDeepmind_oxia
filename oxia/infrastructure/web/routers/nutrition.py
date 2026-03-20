from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from models import NutritionMatchRequest, NutritionMatchResponse
from oxia.application.nutrition_match import build_nutrition_match_response
from oxia.infrastructure.web.deps import ContainerDep

router = APIRouter(tags=["nutrition"])


@router.post("/nutrition/match", response_model=NutritionMatchResponse)
def nutrition_match(
    body: NutritionMatchRequest,
    _user: Annotated[dict, Depends(get_current_user)],
    container: ContainerDep,
) -> NutritionMatchResponse:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in body.ingredients:
        s = (raw or "").strip()
        if not s or len(s) > 240:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        cleaned.append(s)
        if len(cleaned) >= 40:
            break
    if not cleaned:
        raise HTTPException(status_code=400, detail="Provide at least one non-empty ingredient.")
    return build_nutrition_match_response(container.nutrition_lookup, cleaned)
