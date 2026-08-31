"""
Synthesis node: the last stop before END. Takes whatever the graph
gathered and asks the LLM to write one grounded answer in the
requested language, only using the supplied context.
"""
from __future__ import annotations

from app.agents.llm import extract_text, get_chat_llm
from app.agents.state import AgentState, Citation

SYNTHESIS_PROMPT = """Answer the user's question using ONLY the context provided below. \
If the context doesn't fully answer the question, say what's missing rather than guessing. \
Cite pages inline like (p. 12) when you use something from a specific page. Be concise.

IMPORTANT: Write your entire answer in {language}, regardless of what language the question \
or the source document is in. Page citations like (p. 12) stay in that same numeric format.

Question: {query}

--- Retrieved document context ---
{text_context}

--- SQL query result ---
{sql_context}

--- Vision/chart analysis ---
{vision_context}

Answer (in {language}):"""


def synthesize_node(state: AgentState) -> dict:
    query = state.get("original_query") or state["query"]
    language = state.get("response_language") or "English"

    text_context = "(none)"
    chunks = state.get("retrieved_chunks", [])
    if chunks:
        text_context = "\n---\n".join(f"[page {c['page']}, {c['kind']}] {c['text']}" for c in chunks)

    sql_context = state.get("sql_result_markdown") or "(no SQL query was run)"
    vision_context = state.get("vision_analysis") or "(no chart analysis was run)"

    llm = get_chat_llm()
    response = llm.invoke(
        SYNTHESIS_PROMPT.format(
            query=query, text_context=text_context, sql_context=sql_context,
            vision_context=vision_context, language=language,
        )
    )

    citations: list[Citation] = []
    for c in chunks:
        citations.append(Citation(doc_name=c["doc_name"], page=c["page"], kind=c["kind"], snippet=c["text"][:200]))
    for img in state.get("retrieved_images", []):
        citations.append(Citation(doc_name=img["doc_name"], page=img["page"], kind="image", snippet=""))

    return {"final_answer": extract_text(response), "citations": citations}