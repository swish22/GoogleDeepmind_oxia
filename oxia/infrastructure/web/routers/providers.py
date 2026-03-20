from __future__ import annotations

import json
import logging
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from auth import get_current_user
from models import HFWarmupRequest, OllamaPullRequest
from oxia.infrastructure.model_catalog import ollama_base_url
from oxia.infrastructure.web.deps import ContainerDep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/ollama/pull")
def ollama_pull_stream(
    body: OllamaPullRequest,
    _user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    base = ollama_base_url()
    name = body.name.strip()

    def gen() -> str:
        try:
            with requests.post(
                f"{base}/api/pull",
                json={"name": name},
                stream=True,
                timeout=None,
            ) as r:
                if not r.ok:
                    yield json.dumps({"status": "error", "error": (r.text or r.reason)[:800]}) + "\n"
                    return
                for line in r.iter_lines(decode_unicode=True):
                    if line:
                        yield line + "\n"
        except Exception as e:
            logger.exception("Ollama pull stream failed for %s", name)
            yield json.dumps({"status": "error", "error": str(e)}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@router.post("/hf/warmup")
def hf_warmup(
    body: HFWarmupRequest,
    _user: Annotated[dict, Depends(get_current_user)],
    container: ContainerDep,
) -> dict[str, bool]:
    mid = body.hf_model.strip()
    hf = container.hf_provider
    base = hf.base_url.rstrip("/")
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if hf.hf_token:
        headers["Authorization"] = f"Bearer {hf.hf_token}"
    try:
        r = requests.post(
            f"{base}/{mid}",
            headers=headers,
            json={"inputs": "ok", "options": {"wait_for_model": True}},
            timeout=300,
        )
        if r.status_code in (401, 403):
            raise HTTPException(
                status_code=400,
                detail="HuggingFace rejected the request. Set HF_TOKEN in .env if the model requires it.",
            )
        if not r.ok:
            raise HTTPException(
                status_code=503,
                detail=f"HuggingFace warmup failed: {(r.text or r.reason)[:400]}",
            )
    except HTTPException:
        raise
    except requests.RequestException as e:
        logger.warning("HF warmup failed: %s", e)
        raise HTTPException(status_code=503, detail="Could not reach HuggingFace Inference API.") from e
    return {"ok": True}
