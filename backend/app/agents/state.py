"""
Shared state passed between every node in the LangGraph graph.

TypedDict (not a Pydantic model) because that's what LangGraph's
StateGraph expects for the state schema - each node returns a partial
dict of the keys it updates, and LangGraph merges it into the running
state.
"""
from __future__ import annotations

from typing import Literal, TypedDict


class Citation(TypedDict):
    doc_name: str
    page: int
    kind: str  # "text" | "table" | "image"
    snippet: str


class AgentState(TypedDict, total=False):
    # --- input ---
    query: str
    doc_name: str | None  # restrict retrieval to one ingested document, if set

    # --- supervisor routing ---
    route: Literal["search", "sql", "vision", "end"]

    # --- search agent output ---
    retrieved_chunks: list[dict]
    retrieved_images: list[dict]

    response_language: str

    # --- sql agent output ---
    sql_query: str | None
    sql_result_markdown: str | None

    # --- vision agent output ---
    vision_analysis: str | None

    # --- self-rag loop ---
    grade: Literal["relevant", "irrelevant"] | None
    rewrite_count: int
    original_query: str | None  # kept so we can show what the query was rewritten from

    # --- guardrails ---
    in_scope: bool

    # --- output ---
    final_answer: str | None
    citations: list[Citation]
