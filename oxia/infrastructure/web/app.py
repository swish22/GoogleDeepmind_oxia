from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from oxia.infrastructure.container import AppContainer
from oxia.infrastructure.web.routers import auth as auth_router
from oxia.infrastructure.web.routers import chat as chat_router
from oxia.infrastructure.web.routers import config_api
from oxia.infrastructure.web.routers import health as health_router
from oxia.infrastructure.web.routers import meals as meals_router
from oxia.infrastructure.web.routers import nutrition as nutrition_router
from oxia.infrastructure.web.routers import providers as providers_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    load_dotenv()
    init_db()
    app.state.container = AppContainer.build()
    logger.info("Oxia API container initialized.")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Oxia Metabolic Intelligence OS",
        lifespan=lifespan,
        version="2.0-phase1",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router.router)
    app.include_router(config_api.router)
    app.include_router(auth_router.router)
    app.include_router(providers_router.router)
    app.include_router(meals_router.router)
    app.include_router(nutrition_router.router)
    app.include_router(chat_router.router)
    return app


# ASGI entry — `uvicorn backend:app`
app = create_app()
