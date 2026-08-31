"""
Text embeddings via a local sentence-transformers model.

Deliberately NOT using OpenAI embeddings here: embedding is called far
more often than generation (every chunk, every query), so keeping it
local/free means ingesting a 500-page report doesn't cost API credits,
and the whole ingestion pipeline (Week 1) can be developed and tested
with zero API keys. GPT-4o is reserved for the parts that actually
need real reasoning (agents/).

Model is loaded once and cached at module level — SentenceTransformer
construction loads weights from disk/HF hub, which you do not want to
repeat on every request.
"""
from __future__ import annotations

from functools import lru_cache

TEXT_MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim, fast, strong general-purpose retrieval model
TEXT_EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(TEXT_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of strings. Returns one vector per input string."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string (same model/space as embed_texts)."""
    return embed_texts([query])[0]
