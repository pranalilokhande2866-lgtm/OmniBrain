"""
Orchestrates the full Week 1 ingestion pipeline: parse -> chunk ->
embed -> store. This is the single function the FastAPI upload route
calls; each individual step lives in its own module (pdf_parser,
chunker, text_embedder, image_embedder, vectorstore) so they can be
tested/swapped independently, as verified in tests/.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.ingestion.chunker import chunk_document
from app.ingestion.image_embedder import embed_images
from app.ingestion.pdf_parser import parse_pdf
from app.ingestion.text_embedder import embed_texts
from app.vectorstore.qdrant_client import ensure_collections, upsert_images, upsert_text_chunks


@dataclass
class IngestionSummary:
    doc_name: str
    num_pages: int
    text_chunks_stored: int
    images_stored: int


def ingest_pdf(
    pdf_path: str | Path,
    page_start: int | None = None,
    page_end: int | None = None,
) -> IngestionSummary:
    ensure_collections()

    parsed = parse_pdf(pdf_path, page_start=page_start, page_end=page_end)
    chunks = chunk_document(parsed)

    text_stored = 0
    if chunks:
        vectors = embed_texts([c.text for c in chunks])
        text_stored = upsert_text_chunks(list(zip(chunks, vectors)))

    images_stored = 0
    if parsed.image_blocks:
        image_vectors = embed_images([img.image_bytes for img in parsed.image_blocks])
        images_stored = upsert_images(list(zip(parsed.image_blocks, image_vectors)))

    return IngestionSummary(
        doc_name=parsed.doc_name,
        num_pages=parsed.num_pages,
        text_chunks_stored=text_stored,
        images_stored=images_stored,
    )
