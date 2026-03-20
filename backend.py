"""
ASGI entrypoint for `uvicorn backend:app`.

Implementation: Clean Architecture layout under `oxia/` (domain / application / infrastructure).
"""

from oxia.infrastructure.web.app import app

__all__ = ["app"]
