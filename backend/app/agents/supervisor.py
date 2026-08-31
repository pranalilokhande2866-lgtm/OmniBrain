"""
Supervisor node: the entry point of the graph. Classifies the user's
query and decides which sub-agent should handle it first.

  "search" -> semantic question about narrative/table content
              (default - most queries land here)
  "sql"    -> asks about historical stock prices / quarterly financials
              ("what was the close on...", "EBITDA margin in Q3 FY25")
  "vision" -> explicitly asks about a chart/graph/figure's visual content
              ("what does the bar chart on page 12 show")

This is the node the brief's Week 2 mid-review checkpoint targets:
"Prove the LangGraph supervisor can correctly decide between searching
the vector database vs. executing a SQL query based on the prompt."
"""
from __future__ import annotations

from app.agents.llm import extract_text, get_chat_llm
from app.agents.state import AgentState

ROUTING_PROMPT = """You are a routing supervisor for a document question-answering system.
Classify the user's query into exactly one category. Reply with ONLY the category word.

Categories:
- sql: the query asks about historical stock prices (open/high/low/close/volume) or \
quarterly financial figures (revenue, EBITDA, net profit) that would live in a structured database
- vision: the query explicitly asks what a chart, graph, figure, or image shows visually
- search: anything else - narrative content, general questions about tables, definitions, summaries

Query: {query}

Category:"""


def supervisor_node(state: AgentState) -> dict:
    query = state["query"]
    llm = get_chat_llm()
    response = llm.invoke(ROUTING_PROMPT.format(query=query))
    raw = extract_text(response).strip().lower()

    if "sql" in raw:
        route = "sql"
    elif "vision" in raw:
        route = "vision"
    else:
        route = "search"

    return {"route": route, "rewrite_count": state.get("rewrite_count", 0)}


def route_from_supervisor(state: AgentState) -> str:
    """Conditional-edge path function - reads the route the supervisor just set."""
    return state["route"]
