"""
Multi-modal PDF parsing.

Pulls three things out of a PDF, each tagged with page-level
provenance so downstream citations can point back to an exact page:

  1. Text     -> via pdfplumber (layout-aware)
  2. Tables   -> via pdfplumber's table detector
  3. Images   -> via PyMuPDF (fitz), which also catches vector-drawn
                 chart regions by rasterizing pages that contain
                 drawing operators, not just embedded raster images

Design note: pdfplumber and PyMuPDF are used together deliberately.
pdfplumber's text/table extraction is more accurate for layout; PyMuPDF
is faster and more reliable for image/figure extraction and page
rasterization. Using one library for everything is simpler but worse
at both jobs.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf as fitz  # PyMuPDF (modern import name; avoids deprecation warning)
import pdfplumber


@dataclass
class TextBlock:
    page: int
    text: str
    doc_name: str


@dataclass
class TableBlock:
    page: int
    rows: list[list[str | None]]
    doc_name: str

    def as_markdown(self) -> str:
        if not self.rows:
            return ""
        lines = []
        header = self.rows[0]
        lines.append("| " + " | ".join(str(c or "") for c in header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        for row in self.rows[1:]:
            lines.append("| " + " | ".join(str(c or "") for c in row) + " |")
        return "\n".join(lines)


@dataclass
class ImageBlock:
    page: int
    doc_name: str
    image_bytes: bytes
    ext: str
    width: int
    height: int
    caption_context: str = ""  # text immediately surrounding the image, if any


@dataclass
class ParsedDocument:
    doc_name: str
    num_pages: int
    text_blocks: list[TextBlock] = field(default_factory=list)
    table_blocks: list[TableBlock] = field(default_factory=list)
    image_blocks: list[ImageBlock] = field(default_factory=list)


MIN_IMAGE_DIM = 120   # skip tiny icons/decorative dots
MIN_IMAGE_BYTES = 3000  # skip masks/near-empty images


def parse_pdf(
    pdf_path: str | Path,
    page_start: int | None = None,
    page_end: int | None = None,
) -> ParsedDocument:
    """
    Parse a PDF into text/table/image blocks.

    page_start/page_end are 1-indexed and inclusive, letting you parse
    a subset of a large report (e.g. just the financial-statements
    section) instead of every page. Omit both to parse the whole file.
    """
    pdf_path = Path(pdf_path)
    doc_name = pdf_path.name

    doc = ParsedDocument(doc_name=doc_name, num_pages=0)

    # --- text + tables via pdfplumber ---
    with pdfplumber.open(pdf_path) as pdf:
        doc.num_pages = len(pdf.pages)
        lo = (page_start or 1) - 1
        hi = page_end or doc.num_pages
        for i in range(lo, hi):
            page = pdf.pages[i]
            page_num = i + 1

            text = page.extract_text() or ""
            if text.strip():
                doc.text_blocks.append(TextBlock(page=page_num, text=text, doc_name=doc_name))

            for table in page.extract_tables():
                # skip trivial 1x1 / empty tables (usually false positives)
                if table and len(table) > 1 and len(table[0]) > 1:
                    doc.table_blocks.append(
                        TableBlock(page=page_num, rows=table, doc_name=doc_name)
                    )

    # --- images via PyMuPDF ---
    fitz_doc = fitz.open(pdf_path)
    lo = (page_start or 1) - 1
    hi = page_end or len(fitz_doc)
    for page_index in range(lo, hi):
        page = fitz_doc[page_index]
        page_num = page_index + 1
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                base = fitz_doc.extract_image(xref)
            except Exception:
                continue
            img_bytes = base["image"]
            width, height = base.get("width", 0), base.get("height", 0)
            if width < MIN_IMAGE_DIM or height < MIN_IMAGE_DIM:
                continue
            if len(img_bytes) < MIN_IMAGE_BYTES:
                continue
            doc.image_blocks.append(
                ImageBlock(
                    page=page_num,
                    doc_name=doc_name,
                    image_bytes=img_bytes,
                    ext=base.get("ext", "png"),
                    width=width,
                    height=height,
                )
            )
    fitz_doc.close()

    return doc


def rasterize_page(pdf_path: str | Path, page_num: int, dpi: int = 150) -> bytes:
    """
    Render a full page to PNG bytes. Use this for vector-drawn charts
    (matplotlib/Excel-style graphs) that extract_image() can't see
    because they're drawing operators, not embedded raster images —
    the Vision agent falls back to this when a page is flagged as
    chart-heavy but pdfimages found nothing worth sending to the VLM.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Usage: python pdf_parser.py <path.pdf> [page_start] [page_end]")
        sys.exit(1)
    ps = int(sys.argv[2]) if len(sys.argv) > 2 else None
    pe = int(sys.argv[3]) if len(sys.argv) > 3 else None
    result = parse_pdf(path, ps, pe)
    print(f"doc={result.doc_name} pages={result.num_pages}")
    print(f"text_blocks={len(result.text_blocks)} table_blocks={len(result.table_blocks)} image_blocks={len(result.image_blocks)}")
    if result.table_blocks:
        print("\nFirst table found (page %d):" % result.table_blocks[0].page)
        print(result.table_blocks[0].as_markdown()[:500])
