"""Application entry point and FastAPI app factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from operational_semantics.config import settings
from operational_semantics.persistence.database import init_db, teardown_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager."""
    await init_db()
    yield
    await teardown_db()


app = FastAPI(
    title="Operational Semantics Lab",
    description="A governed knowledge layer for enterprise agents — ontology, policy, approval, provenance",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}
