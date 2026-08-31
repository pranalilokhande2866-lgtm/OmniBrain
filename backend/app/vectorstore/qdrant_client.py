"""
Qdrant wrapper for the two multi-modal collections: text chunks and
images. Each stored point carries enough payload metadata to render a
citation (doc name + page number) without a second lookup.

Local vs. server mode is picked automatically from settings:
  - QDRANT_URL unset  -> embedded/local mode, data written to
                          data/qdrant_storage/ on disk. Zero setup,
                          perfect for development.
  - QDRANT_URL set     -> connects to a real Qdrant server (see
                          docker-compose.yml for a one-command server).

Tested against qdrant-client==1.19.0's current API: `query_points`
(not the older, now-secondary `search` method), `models.PointStruct`,
`models.VectorParams`.
"""
from __future__ import annotations

import hashlib
import uuid
from functools import lru_cache

from qdrant_client import QdrantClient, models

from app.config import settings
from app.ingestion.image_embedder import IMAGE_EMBEDDING_DIM
from app.ingestion.text_embedder import TEXT_EMBEDDING_DIM

TEXT_COLLECTION = "text_chunks"
IMAGE_COLLECTION = "image_chunks"


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    # Embedded local mode - no server process required.
    return QdrantClient(path=str(settings.qdrant_storage_path))


def ensure_collections() -> None:
    client = get_client()
    existing = {c.name for c in client.get_collections().collections}

    if TEXT_COLLECTION not in existing:
        client.create_collection(
            collection_name=TEXT_COLLECTION,
            vectors_config=models.VectorParams(
                size=TEXT_EMBEDDING_DIM, distance=models.Distance.COSINE
            ),
        )
    if IMAGE_COLLECTION not in existing:
        client.create_collection(
            collection_name=IMAGE_COLLECTION,
            vectors_config=models.VectorParams(
                size=IMAGE_EMBEDDING_DIM, distance=models.Distance.COSINE
            ),
        )


def _stable_id(*parts: str) -> str:
    """Deterministic point ID so re-ingesting the same doc/page/chunk upserts in place."""
    key = "|".join(parts)
    return str(uuid.UUID(hashlib.md5(key.encode()).hexdigest()))


def upsert_text_chunks(chunks_with_vectors: list[tuple], ) -> int:
    """
    chunks_with_vectors: list of (Chunk, vector) tuples.
    Returns the number of points upserted.
    """
    client = get_client()
    points = []
    for chunk, vector in chunks_with_vectors:
        point_id = _stable_id(chunk.doc_name, str(chunk.page), chunk.kind, str(chunk.chunk_index))
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "doc_name": chunk.doc_name,
                    "page": chunk.page,
                    "kind": chunk.kind,
                    "text": chunk.text,
                },
            )
        )
    if points:
        client.upsert(collection_name=TEXT_COLLECTION, points=points)
    return len(points)


def upsert_images(images_with_vectors: list[tuple]) -> int:
    """images_with_vectors: list of (ImageBlock, vector) tuples."""
    client = get_client()
    points = []
    for img, vector in images_with_vectors:
        point_id = _stable_id(img.doc_name, str(img.page), "img", str(len(points)))
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "doc_name": img.doc_name,
                    "page": img.page,
                    "width": img.width,
                    "height": img.height,
                    "ext": img.ext,
                },
            )
        )
    if points:
        client.upsert(collection_name=IMAGE_COLLECTION, points=points)
    return len(points)


def search_text(vector: list[float], limit: int = 5, doc_name: str | None = None) -> list[dict]:
    client = get_client()
    query_filter = None
    if doc_name:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="doc_name", match=models.MatchValue(value=doc_name))]
        )
    result = client.query_points(
        collection_name=TEXT_COLLECTION,
        query=vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )
    return [{"score": p.score, **p.payload} for p in result.points]


def search_images(vector: list[float], limit: int = 3, doc_name: str | None = None) -> list[dict]:
    client = get_client()
    query_filter = None
    if doc_name:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="doc_name", match=models.MatchValue(value=doc_name))]
        )
    result = client.query_points(
        collection_name=IMAGE_COLLECTION,
        query=vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )
    return [{"score": p.score, **p.payload} for p in result.points]


def collection_stats() -> dict:
    client = get_client()
    out = {}
    for name in (TEXT_COLLECTION, IMAGE_COLLECTION):
        try:
            info = client.get_collection(name)
            out[name] = info.points_count
        except Exception:
            out[name] = 0
    return out
