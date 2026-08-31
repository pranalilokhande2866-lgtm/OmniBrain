"""
Search agent node: runs the user's (possibly rewritten) query against
both Qdrant collections - text chunks via MiniLM, images via CLIP's
text encoder - and stores whatever comes back on state.

Grading of whether these results are actually relevant happens
separately in self_rag.py, so this node stays a simple "go fetch"
step and the control-flow logic lives in one place.
"""
from __future__ import annotations

from app.agents.state import AgentState
from app.ingestion.image_embedder import embed_query_for_images
from app.ingestion.text_embedder import embed_query
from app.vectorstore.qdrant_client import search_images, search_text

TEXT_TOP_K = 5
IMAGE_TOP_K = 2


def search_node(state: AgentState) -> dict:
    query = state["query"]
    doc_name = state.get("doc_name")

    text_vector = embed_query(query)
    text_hits = search_text(text_vector, limit=TEXT_TOP_K, doc_name=doc_name)

    image_vector = embed_query_for_images(query)
    image_hits = search_images(image_vector, limit=IMAGE_TOP_K, doc_name=doc_name)

    return {"retrieved_chunks": text_hits, "retrieved_images": image_hits}
