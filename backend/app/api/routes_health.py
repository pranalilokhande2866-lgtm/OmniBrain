from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthResponse
from app.vectorstore.qdrant_client import collection_stats, ensure_collections

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    ensure_collections()
    return HealthResponse(
        status="ok",
        llm_provider=settings.llm_provider,
        llm_configured=settings.has_any_llm_key,
        langfuse_configured=settings.has_langfuse_keys,
        collections=collection_stats(),
    )