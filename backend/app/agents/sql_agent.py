"""
Text-to-SQL agent node. The LLM only ever produces query TEXT - it
never touches the database directly. app.db.query_executor is the one
place that actually opens a sqlite3 connection, and it re-validates
the statement (SELECT-only, keyword blocklist, read-only connection
URI) regardless of what the LLM wrote. Treat the LLM's SQL the same
way you'd treat SQL from an untrusted user, because in effect it is.
"""
from __future__ import annotations

from app.agents.llm import extract_text, get_chat_llm
from app.agents.state import AgentState
from app.db.init_db import SCHEMA_DESCRIPTION
from app.db.query_executor import run_readonly_query

SQL_PROMPT = """You write SQLite SELECT queries. Given the schema below and a user question, \
output ONLY the SQL query - no explanation, no markdown fences, no trailing semicolon commentary.
If the question cannot be answered with these tables, output exactly: NONE

Schema:
{schema}

Question: {query}

SQL:"""


def sql_node(state: AgentState) -> dict:
    query = state["query"]
    llm = get_chat_llm()
    response = llm.invoke(SQL_PROMPT.format(schema=SCHEMA_DESCRIPTION, query=query))
    sql = extract_text(response).strip().strip("`").strip()
    if sql.lower().startswith("sql"):
        sql = sql[3:].strip()

    if sql.upper() == "NONE" or not sql:
        return {
            "sql_query": None,
            "sql_result_markdown": "The question doesn't map to the available stock/financials tables.",
        }

    result = run_readonly_query(sql)
    return {"sql_query": sql, "sql_result_markdown": result.as_markdown()}
