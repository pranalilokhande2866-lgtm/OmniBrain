"""
The LangGraph state machine wiring together every agent node.

Graph shape:

    START -> supervisor --route="sql"----------------------> sql -----------> synthesize -> END
                  |
                  +---route="search" or "vision"--> search --route="search"--> grade --relevant-----> synthesize -> END
                                                        ^                        |
                                                        |                        +--irrelevant, retries
                                                        |                           left--> rewrite --+
                                                        |                                             |
                                                        +---------------------------------------------+
                                                        |
                                                        +--route="vision"------> vision -------------> synthesize -> END

Call build_graph() once (it's cheap - no I/O happens until invoke) and
reuse the compiled graph across requests.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.search_agent import search_node
from app.agents.self_rag import grade_node, rewrite_node, route_after_grade
from app.agents.sql_agent import sql_node
from app.agents.state import AgentState
from app.agents.supervisor import route_from_supervisor, supervisor_node
from app.agents.synthesize import synthesize_node
from app.agents.vision_agent import vision_node


def _route_after_search(state: AgentState) -> str:
    """After search, vision-routed queries go straight to the vision agent;
    everything else goes through the Self-RAG grading step."""
    return "vision" if state.get("route") == "vision" else "search"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("search", search_node)
    graph.add_node("sql", sql_node)
    graph.add_node("vision", vision_node)
    graph.add_node("grade", grade_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("synthesize", synthesize_node)

    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {"search": "search", "vision": "search", "sql": "sql"},
    )

    graph.add_conditional_edges(
        "search",
        _route_after_search,
        {"vision": "vision", "search": "grade"},
    )

    graph.add_conditional_edges(
        "grade",
        route_after_grade,
        {"retry": "rewrite", "synthesize": "synthesize"},
    )

    graph.add_edge("rewrite", "search")
    graph.add_edge("vision", "synthesize")
    graph.add_edge("sql", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


def run_query(
    query: str,
    doc_name: str | None = None,
    response_language: str = "English",
    callbacks: list | None = None,
) -> AgentState:
    app = build_graph()
    initial_state: AgentState = {
        "query": query,
        "doc_name": doc_name,
        "response_language": response_language,
        "rewrite_count": 0,
    }
    config = {"callbacks": callbacks} if callbacks else {}
    return app.invoke(initial_state, config=config)
