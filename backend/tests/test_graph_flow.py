"""
Tests the graph's CONTROL FLOW (routing, Self-RAG retry loop, vision
path) using langchain_core's FakeListChatModel in place of real
OpenAI calls, and dummy vectors in place of real embeddings.

This deliberately does NOT test whether the LLM's classification or
grading judgment is *correct* (that needs a real model) - it tests
that the graph *wires those decisions through correctly*: does an
"irrelevant" grade actually trigger a rewrite-and-retry, does a "sql"
route actually skip the search node, etc. Run with a real
OPENAI_API_KEY for an end-to-end semantic test.
"""
import sys

sys.path.insert(0, ".")

from unittest.mock import patch

from langchain_core.language_models.fake_chat_models import FakeListChatModel


def _seed_dummy_vector_data():
    from app.vectorstore import qdrant_client as qc
    from app.ingestion.chunker import Chunk
    from app.ingestion.pdf_parser import ImageBlock

    qc.ensure_collections()
    chunks = [Chunk(doc_name="test-doc.pdf", page=3, chunk_index=0, text="dummy chunk", kind="text")]
    qc.upsert_text_chunks([(c, [0.1] * 384) for c in chunks])
    img = ImageBlock(doc_name="test-doc.pdf", page=3, image_bytes=b"x", ext="png", width=800, height=600)
    qc.upsert_images([(img, [0.1] * 512)])


def _dummy_embed_query(q):
    return [0.1] * 384


def _dummy_embed_query_images(q):
    return [0.1] * 512


def run_scenario(name, responses, expected_route, expect_rewrite=False):
    print(f"\n=== Scenario: {name} ===")
    fake_llm = FakeListChatModel(responses=responses)

    # Each agent module did `from app.agents.llm import get_chat_llm`, which
    # binds its OWN name to the original function object at import time -
    # patching app.agents.llm.get_chat_llm alone would not affect those
    # already-bound references, so every call site needs patching too.
    with patch("app.agents.supervisor.get_chat_llm", return_value=fake_llm), \
         patch("app.agents.self_rag.get_chat_llm", return_value=fake_llm), \
         patch("app.agents.sql_agent.get_chat_llm", return_value=fake_llm), \
         patch("app.agents.synthesize.get_chat_llm", return_value=fake_llm), \
         patch("app.agents.vision_agent.get_vision_llm", return_value=fake_llm), \
         patch("app.agents.search_agent.embed_query", side_effect=_dummy_embed_query), \
         patch("app.agents.search_agent.embed_query_for_images", side_effect=_dummy_embed_query_images):

        from app.agents.graph import run_query
        result = run_query("What was the EBITDA in Q3?", doc_name="test-doc.pdf")

    print("route:", result.get("route"))
    print("rewrite_count:", result.get("rewrite_count"))
    print("sql_query:", result.get("sql_query"))
    print("final_answer:", (result.get("final_answer") or "")[:150])
    print("citations:", len(result.get("citations", [])))

    assert result.get("route") == expected_route, f"expected route={expected_route}, got {result.get('route')}"
    if expect_rewrite:
        assert result.get("rewrite_count", 0) >= 1, "expected at least one rewrite"
    assert result.get("final_answer"), "expected a final answer"
    print(f"PASS: {name}")


if __name__ == "__main__":
    import os

    os.environ["DATA_DIR"] = "/tmp/omnibrain_graph_test"
    os.environ["OPENAI_API_KEY"] = "sk-test-not-real-but-llm-is-mocked-anyway"

    _seed_dummy_vector_data()

    # --- Scenario 1: search route, first grade relevant -> straight through ---
    run_scenario(
        "search, relevant on first try",
        responses=["search", "relevant", "Final answer using retrieved context (p. 3)."],
        expected_route="search",
    )

    # --- Scenario 2: search route, irrelevant then relevant -> exercises the Self-RAG loop ---
    run_scenario(
        "search, irrelevant then relevant (self-rag retry)",
        responses=[
            "search",                        # supervisor
            "irrelevant",                    # grade #1
            "EBITDA margin quarterly trend",  # rewrite
            "relevant",                       # grade #2 (after re-search)
            "Final answer after one retry (p. 3).",
        ],
        expected_route="search",
        expect_rewrite=True,
    )

    # --- Scenario 3: search route, always irrelevant -> hits max retries, still answers ---
    run_scenario(
        "search, always irrelevant (exhausts retries, still synthesizes)",
        responses=[
            "search", "irrelevant", "rewritten query 1",
            "irrelevant", "rewritten query 2",
            "irrelevant",  # 3rd grade - rewrite_count(2) >= max_retries(2) -> synthesize anyway
            "Best-effort answer despite low-confidence context.",
        ],
        expected_route="search",
        expect_rewrite=True,
    )

    # --- Scenario 4: sql route bypasses search/grade entirely ---
    run_scenario(
        "sql route",
        responses=["sql", "SELECT quarter, ebitda_cr FROM quarterly_financials LIMIT 3", "Final SQL-grounded answer."],
        expected_route="sql",
    )

    # --- Scenario 5: vision route goes through search then vision_node (real page rasterization) ---
    run_scenario(
        "vision route (real PDF page rasterized + sent to fake VLM)",
        responses=["vision", "The chart on page 3 shows...", "Final answer combining vision analysis."],
        expected_route="vision",
    )

    print("\nALL SCENARIOS PASSED")
