from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app.ingestion.pipeline import ingest_pdf
from app.models.schemas import IngestResponse

router = APIRouter()


@router.post("/documents/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile,
    page_start: int | None = None,
    page_end: int | None = None,
) -> IngestResponse:
    """
    Upload a PDF and ingest it (parse -> chunk -> embed -> store).
    page_start/page_end (1-indexed, inclusive) let you ingest a subset
    of a large report for faster iteration during development.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    dest = settings.uploads_path / file.filename
    contents = await file.read()
    dest.write_bytes(contents)

    try:
        summary = ingest_pdf(dest, page_start=page_start, page_end=page_end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}") from e

    return IngestResponse(
        doc_name=summary.doc_name,
        num_pages=summary.num_pages,
        text_chunks_stored=summary.text_chunks_stored,
        images_stored=summary.images_stored,
    )
