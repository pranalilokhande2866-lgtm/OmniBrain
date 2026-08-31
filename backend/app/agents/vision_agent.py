"""
Vision agent node: reasons over chart/figure pages using GPT-4o's
vision input.

Design note: Qdrant only stores image *metadata* (doc_name, page,
width, height) in the payload, not the raw image bytes - keeping
binary blobs out of the vector DB is standard practice and keeps
collection size sane on a 500+ page report. So when the vision agent
needs actual pixels, it re-rasterizes the cited page on demand from
the original PDF (found via doc_name in the uploads directory). This
also means the image sent to the VLM is always the full page in
context, not just a cropped embedded image - which tends to help
GPT-4o read axis labels and legends correctly.
"""
from __future__ import annotations

import base64

from langchain_core.messages import HumanMessage

from app.agents.llm import extract_text, get_vision_llm
from app.agents.state import AgentState
from app.config import settings
from app.ingestion.pdf_parser import rasterize_page

MAX_PAGES_TO_INSPECT = 2

VISION_PROMPT = """You are analyzing a page from a financial report to answer a question.
Read any charts, graphs, or tables visible on the page carefully, including axis labels,
legends, and numeric values. Answer the question using ONLY what's visible on this page.
If the page doesn't contain relevant visual data, say so explicitly.

Question: {query}"""


def vision_node(state: AgentState) -> dict:
    query = state["query"]
    candidate_images = state.get("retrieved_images", [])[:MAX_PAGES_TO_INSPECT]

    if not candidate_images:
        return {"vision_analysis": "No chart or figure pages were found matching this query."}

    llm = get_vision_llm()
    findings = []

    for img_meta in candidate_images:
        doc_name = img_meta["doc_name"]
        page = img_meta["page"]
        pdf_path = settings.uploads_path / doc_name

        if not pdf_path.exists():
            findings.append(f"[page {page}] source PDF not found at {pdf_path}, skipped.")
            continue

        png_bytes = rasterize_page(pdf_path, page, dpi=150)
        b64 = base64.b64encode(png_bytes).decode()

        message = HumanMessage(
            content=[
                {"type": "text", "text": VISION_PROMPT.format(query=query)},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ]
        )
        response = llm.invoke([message])
        findings.append(f"[{doc_name}, page {page}]\n{extract_text(response)}")

    return {"vision_analysis": "\n\n".join(findings)}
