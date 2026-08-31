"""
FastAPI entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000
(from the backend/ directory, with your virtualenv activated)
"""

from app.api import routes_audio, routes_health, routes_query, routes_upload
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_health, routes_query, routes_upload
from app.db.init_db import build_database
from app.vectorstore.qdrant_client import ensure_collections


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: make sure the vector collections and the synthetic stock
    # DB exist before the first request arrives.
    ensure_collections()
    build_database(force=False)
    yield


app = FastAPI(
    title="OmniBrain API",
    description="Agentic Multi-Modal RAG Orchestrator - Axlero Solutions portfolio project",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before deploying anywhere public
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router, tags=["health"])
app.include_router(routes_upload.router, tags=["documents"])
app.include_router(routes_query.router, tags=["query"])
app.include_router(routes_audio.router, tags=["audio"])
