"""
Thin wrapper around NeMo Guardrails, called once at the top of the
query API route - before the LangGraph pipeline runs at all - to
block out-of-scope questions early (see config/ for the actual rails).

Detection logic verified by reading the installed library's own
source (nemoguardrails/library/self_check/input_check/{actions.py,
flows.v1.co}): when `self_check_input` judges a message unsafe, the
`self check input` flow calls the exact bot message
`bot refuse to respond` and then `stop`s - it never reaches any other
flow. config/rails/document_scope.co overrides that message's text to
a known, distinctive string (user-defined message IDs take precedence
over library defaults), so a block is detected by exact string match
rather than by guessing at free-form LLM output.

Import of nemoguardrails is lazy (inside the function, not at module
top) so the rest of the app can start up and be tested even before
`pip install nemoguardrails` has been run.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"

# Must match config/rails/document_scope.co's `define bot refuse to respond` text exactly.
REFUSAL_MESSAGE = (
    "OmniBrain only answers questions about the uploaded report and its related "
    "financial data - that question is outside its scope."
)


@lru_cache(maxsize=1)
def _get_rails():
    from nemoguardrails import LLMRails, RailsConfig

    config = RailsConfig.from_path(str(CONFIG_DIR))
    return LLMRails(config)


def check_input_in_scope(user_message: str) -> tuple[bool, str | None]:
    """
    Returns (allowed, refusal_message).
      allowed=True  -> proceed to the LangGraph pipeline as normal.
      allowed=False -> refusal_message is what the API should return
                        directly, WITHOUT calling the graph - the
                        content Guardrails generated in this case is
                        just its own refusal, not a document answer.
    """
    try:
        rails = _get_rails()
        response = rails.generate(messages=[{"role": "user", "content": user_message}])
    except Exception as e:
        # Fail OPEN with a clear log line rather than hard-crashing the
        # whole API if guardrails config/deps/network aren't set up -
        # an optional safety layer having a problem shouldn't 500 a
        # portfolio demo. The downstream LangGraph pipeline has its own
        # error handling (see routes_query.py) if the real issue is a
        # missing/invalid OPENAI_API_KEY. Flip this to fail-CLOSED
        # (return False, "...") once you've verified your own config
        # end to end with a real key.
        print(f"[guardrails] check failed, allowing query through: {e}")
        return True, None

    content = response.get("content", "") if isinstance(response, dict) else str(response)

    if content.strip() == REFUSAL_MESSAGE:
        return False, content
    return True, None
