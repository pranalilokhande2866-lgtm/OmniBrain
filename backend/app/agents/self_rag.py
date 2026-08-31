"""
Self-RAG self-correction loop (Week 3 of the brief).

grade_node acts as an LLM-as-judge: does the retrieved context
actually address the query? If not, rewrite_node asks the LLM to
rewrite the search query (e.g. expanding an acronym, adding a
synonym) and the graph loops back to search_node - up to
SELF_RAG_MAX_RETRIES times, after which it gives up and lets
synthesize_node answer with whatever it has (explicitly flagged as
low-confidence) rather than looping forever.
"""
from __future__ import annotations

from app.agents.llm import extract_text, get_chat_llm
from app.agents.state import AgentState
from app.config import settings

GRADE_PROMPT = """You are grading whether retrieved context is relevant to a question.

Question: {query}

Retrieved context:
{context}

Does this context contain information that helps answer the question?
Reply with ONLY one word: "relevant" or "irrelevant"."""

REWRITE_PROMPT = """The following search query returned irrelevant results from a document search index.
Rewrite it to be more likely to retrieve relevant passages - consider expanding abbreviations,
adding synonyms, or rephrasing as a more literal keyword-style query. Reply with ONLY the rewritten
query, nothing else.

Original query: {query}"""


def _format_context(state: AgentState) -> str:
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return "(nothing retrieved)"
    return "\n---\n".join(f"[page {c['page']}] {c['text'][:300]}" for c in chunks)


def grade_node(state: AgentState) -> dict:
    query = state["query"]
    context = _format_context(state)
    llm = get_chat_llm()
    response = llm.invoke(GRADE_PROMPT.format(query=query, context=context))
    text = extract_text(response).strip().lower()
    grade = "relevant" if "relevant" in text and "irrelevant" not in text else "irrelevant"
    return {"grade": grade}


def rewrite_node(state: AgentState) -> dict:
    original_query = state.get("original_query") or state["query"]
    llm = get_chat_llm()
    response = llm.invoke(REWRITE_PROMPT.format(query=state["query"]))
    new_query = extract_text(response).strip()
    return {
        "query": new_query,
        "original_query": original_query,
        "rewrite_count": state.get("rewrite_count", 0) + 1,
    }


def route_after_grade(state: AgentState) -> str:
    """
    Conditional-edge path function.
    -> "retry"     if irrelevant and we haven't hit the retry cap
    -> "synthesize" otherwise (either relevant, or we've given up)
    """
    if state.get("grade") == "irrelevant" and state.get("rewrite_count", 0) < settings.self_rag_max_retries:
        return "retry"
    return "synthesize"
