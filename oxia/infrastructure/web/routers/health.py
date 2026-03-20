from __future__ import annotations

from fastapi import APIRouter

from oxia import __version__
from oxia.infrastructure.web.deps import ContainerDep

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(container: ContainerDep) -> dict[str, str | bool]:
    """Fast path — keep under ~50ms (no external I/O beyond attribute reads)."""
    return {
        "status": "ok",
        "gemini_configured": container.gemini_provider.configured,
        "version": __version__,
        "architecture": "oxia-clean-phase1",
    }
