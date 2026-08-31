"""
Integration test for the FastAPI app using TestClient - covers what
doesn't need an OpenAI key: app startup, /health, and /documents/upload
(the full parse->chunk->embed->store pipeline against a real PDF).

Note: embed_texts/embed_images are mocked here ONLY because this
sandbox's network allowlist doesn't include huggingface.co, so the
sentence-transformers model weights can't be downloaded in this
environment. On your machine (normal internet access), remove the
patches below - the real models download automatically on first call.
Parsing, chunking, Qdrant storage, and retrieval are all real and
unmocked here.

/query is exercised separately in test_graph_flow.py with a fake LLM,
since the real route needs OPENAI_API_KEY to do anything meaningful.
"""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, ".")
os.environ["DATA_DIR"] = "/tmp/omnibrain_api_test"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _fake_embed_texts(texts):
    return [[0.1] * 384 for _ in texts]


def _fake_embed_images(images):
    return [[0.1] * 512 for _ in images]


def test_health():
    r = client.get("/health")
    print("GET /health ->", r.status_code, r.json())
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "text_chunks" in body["collections"]
    print("PASS: /health")


def test_upload_real_pdf():
    pdf_path = "/tmp/omnibrain_api_test_fixture.pdf"
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader("/mnt/user-data/uploads/1786499413735_tatasteel-iar-2025-26.pdf")
    writer = PdfWriter()
    for i in range(5):
        writer.add_page(reader.pages[i])
    with open(pdf_path, "wb") as f:
        writer.write(f)

    with patch("app.ingestion.pipeline.embed_texts", side_effect=_fake_embed_texts), \
         patch("app.ingestion.pipeline.embed_images", side_effect=_fake_embed_images):
        with open(pdf_path, "rb") as f:
            r = client.post(
                "/documents/upload",
                files={"file": ("tatasteel-sample.pdf", f, "application/pdf")},
            )
    print("POST /documents/upload ->", r.status_code, r.json())
    assert r.status_code == 200
    body = r.json()
    assert body["doc_name"] == "tatasteel-sample.pdf"
    assert body["num_pages"] == 5
    assert body["text_chunks_stored"] > 0
    print("PASS: /documents/upload (real PDF parsing+chunking+Qdrant storage, embedding mocked - see module docstring)")

    # confirm health now reports non-zero collection counts
    r2 = client.get("/health")
    print("collections after upload:", r2.json()["collections"])
    assert r2.json()["collections"]["text_chunks"] > 0


def test_query_without_openai_key_returns_503():
    r = client.post("/query", json={"query": "What is the revenue?"})
    print("POST /query (no key) ->", r.status_code, r.json())
    assert r.status_code == 503
    print("PASS: /query fails clearly (503) without OPENAI_API_KEY, not a crash")


if __name__ == "__main__":
    test_health()
    test_upload_real_pdf()
    test_query_without_openai_key_returns_503()
    print("\nALL API TESTS PASSED")
