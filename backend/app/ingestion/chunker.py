"""
Chunking for text blocks.

Splits page-level text into overlapping chunks small enough to embed
well, while keeping every chunk tagged with its source page so a
retrieved chunk can always be traced back to an exact page (and,
downstream, rendered as a clickable citation in the UI).

Tables are NOT chunked here — TableBlock.as_markdown() is embedded
whole, since splitting a table mid-row destroys its meaning.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.ingestion.pdf_parser import ParsedDocument


@dataclass
class Chunk:
    doc_name: str
    page: int
    chunk_index: int
    text: str
    kind: str  # "text" | "table"


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Simple word-based sliding window splitter."""
    words = text.split()
    if not words:
        return []
    if len(words) <= chunk_size:
        return [" ".join(words)]

    chunks = []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(words), step):
        piece = words[start : start + chunk_size]
        if not piece:
            break
        chunks.append(" ".join(piece))
        if start + chunk_size >= len(words):
            break
    return chunks


def chunk_document(
    doc: ParsedDocument,
    chunk_size: int = 220,
    overlap: int = 40,
) -> list[Chunk]:
    """
    chunk_size / overlap are in words, not tokens — good enough for a
    ~200-400 token target with typical English text and keeps this
    dependency-free (no tokenizer needed at ingestion time).
    """
    chunks: list[Chunk] = []

    for block in doc.text_blocks:
        pieces = _split_text(block.text, chunk_size, overlap)
        for idx, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    doc_name=block.doc_name,
                    page=block.page,
                    chunk_index=idx,
                    text=piece,
                    kind="text",
                )
            )

    for t_idx, table in enumerate(doc.table_blocks):
        md = table.as_markdown()
        if md.strip():
            chunks.append(
                Chunk(
                    doc_name=table.doc_name,
                    page=table.page,
                    chunk_index=t_idx,
                    text=md,
                    kind="table",
                )
            )

    return chunks
