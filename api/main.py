"""FastAPI entry point for the mac blue-team framework."""
from __future__ import annotations

from fastapi import FastAPI

from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Mac Blue-Team Framework")
    app.include_router(router)
    return app


app = create_app()
