"""
Safe execution of LLM-generated SQL against the local stock database.

The LLM only ever generates the query text (see agents/sql_agent.py);
this module is the one place that actually touches sqlite3, and it
enforces two guardrails before running anything an LLM wrote:
  1. Only SELECT statements are allowed (blocks INSERT/UPDATE/DELETE/
     DROP/ATTACH/PRAGMA etc.)
  2. The connection is opened read-only via a URI, as defense in depth
     in case the statement-prefix check is ever bypassed.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from app.config import settings

_DISALLOWED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|ATTACH|DETACH|PRAGMA|VACUUM|REPLACE)\b",
    re.IGNORECASE,
)


@dataclass
class SqlResult:
    ok: bool
    columns: list[str]
    rows: list[tuple]
    error: str | None = None

    def as_markdown(self, max_rows: int = 25) -> str:
        if not self.ok:
            return f"(query failed: {self.error})"
        if not self.rows:
            return "(query returned no rows)"
        lines = ["| " + " | ".join(self.columns) + " |", "|" + "|".join(["---"] * len(self.columns)) + "|"]
        for row in self.rows[:max_rows]:
            lines.append("| " + " | ".join(str(v) for v in row) + " |")
        if len(self.rows) > max_rows:
            lines.append(f"... ({len(self.rows) - max_rows} more rows truncated)")
        return "\n".join(lines)


def run_readonly_query(sql: str, db_path: str | None = None, max_rows: int = 200) -> SqlResult:
    sql_stripped = sql.strip().rstrip(";")

    if not sql_stripped.upper().startswith("SELECT"):
        return SqlResult(ok=False, columns=[], rows=[], error="Only SELECT statements are permitted.")
    if _DISALLOWED.search(sql_stripped):
        return SqlResult(ok=False, columns=[], rows=[], error="Query contains a disallowed keyword.")

    path = db_path or str(settings.sqlite_path)
    uri = f"file:{path}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
        cur = conn.cursor()
        cur.execute(sql_stripped)
        rows = cur.fetchmany(max_rows)
        columns = [d[0] for d in cur.description] if cur.description else []
        conn.close()
        return SqlResult(ok=True, columns=columns, rows=rows)
    except sqlite3.Error as e:
        return SqlResult(ok=False, columns=[], rows=[], error=str(e))
