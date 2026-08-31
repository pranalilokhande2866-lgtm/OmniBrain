from fastapi import APIRouter, HTTPException

from app.agents.graph import run_query
from app.guardrails.guardrails_client import check_input_in_scope
from app.models.schemas import CitationOut, QueryRequest, QueryResponse
from app.observability.langfuse_client import get_langfuse_callbacks

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty.")

    allowed, refusal = check_input_in_scope(request.query)
    if not allowed:
        return QueryResponse(answer=refusal or "That's outside what I can help with.", blocked=True)

    try:
        result = run_query(
            request.query,
            doc_name=request.doc_name,
            response_language=request.response_language,
            callbacks=get_langfuse_callbacks(),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    citations = [CitationOut(**c) for c in result.get("citations", [])]

    return QueryResponse(
        answer=result.get("final_answer") or "No answer was generated.",
        route=result.get("route"),
        rewrite_count=result.get("rewrite_count", 0),
        citations=citations,
        blocked=False,
    )