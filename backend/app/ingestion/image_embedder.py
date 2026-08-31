"""
Image embeddings via a local CLIP model (sentence-transformers'
clip-ViT-B-32 wrapper).

CLIP is used specifically because it embeds images AND text into the
*same* 512-dim space — so a user's text query ("show me the EBITDA
trend chart") can be embedded with embed_query_for_images() and
compared directly against stored chart/image vectors, without needing
a separate image-captioning step. This is the "Multi-Modal Retrieval
... using CLIP" module from the project brief.

Note this is a different model/space than text_embedder.py's MiniLM,
which is why images and text chunks live in two separate Qdrant
collections (see vectorstore/qdrant_client.py) rather than one.
CLIP's own text encoder is capped at 77 tokens, which is too short for
embedding full text chunks — MiniLM handles that job instead.
"""
from __future__ import annotations

import io
from functools import lru_cache

IMAGE_MODEL_NAME = "clip-ViT-B-32"
IMAGE_EMBEDDING_DIM = 512


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(IMAGE_MODEL_NAME)


def embed_images(image_bytes_list: list[bytes]) -> list[list[float]]:
    """Batch-embed raw image bytes (PNG/JPEG). Returns one 512-dim vector per image."""
    if not image_bytes_list:
        return []
    from PIL import Image

    model = _get_model()
    pil_images = [Image.open(io.BytesIO(b)).convert("RGB") for b in image_bytes_list]
    vectors = model.encode(pil_images, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query_for_images(query: str) -> list[float]:
    """
    Embed a text query into the SAME space as embed_images(), so it can
    be used to search the image collection directly (text -> image
    cross-modal retrieval).
    """
    model = _get_model()
    vector = model.encode([query], normalize_embeddings=True, show_progress_bar=False)
    return vector.tolist()[0]
