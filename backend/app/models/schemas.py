"""Pydantic request/response schemas for the API layer."""
from __future__ import annotations

from pydantic import BaseModel


class IngestResponse(BaseModel):
    doc_name: str
    num_pages: int
    text_chunks_stored: int
    images_stored: int


class QueryRequest(BaseModel):
    query: str
    doc_name: str | None = None
    response_language: str = "English"


class CitationOut(BaseModel):
    doc_name: str
    page: int
    kind: str
    snippet: str = ""


class QueryResponse(BaseModel):
    answer: str
    route: str | None = None
    rewrite_count: int = 0
    citations: list[CitationOut] = []
    blocked: bool = False


class TranscribeResponse(BaseModel):
    text: str
    detected_language: str | None = None


class HealthResponse(BaseModel):
    status: str
    llm_provider: str | None = None
    llm_configured: bool
    langfuse_configured: bool
    collections: dict[str, int]