"""
Langfuse observability (Week 4 of the brief: "Integrate Langfuse to
track token usage, latency, and LLM execution traces").

Verified against langfuse==4.14.4's actual current API by importing
it directly - this version's LangChain integration lives at
`langfuse.langchain.CallbackHandler` (the older `langfuse.callback`
module from Langfuse v2 no longer exists in v4). If you're used to
older Langfuse tutorials referencing `langfuse.callback.CallbackHandler`,
that's why this looks different - v4 moved to an OpenTelemetry-based
architecture.

Everything here degrades gracefully when LANGFUSE_PUBLIC_KEY /
LANGFUSE_SECRET_KEY aren't set: get_langfuse_callbacks() returns an
empty list, and the LangGraph invocation in graph.py just runs with no
callbacks attached. Nothing breaks; you just don't get traces until
you add keys.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _get_handler():
    from langfuse.langchain import CallbackHandler

    # Reads LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST from
    # the environment automatically (langfuse's own Langfuse() client does
    # this under the hood) - settings.has_langfuse_keys is checked by the
    # caller before this is ever invoked.
    import os

    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)
    return CallbackHandler()


def get_langfuse_callbacks() -> list:
    """Returns [] when Langfuse isn't configured - safe to always call."""
    if not settings.has_langfuse_keys:
        return []
    try:
        return [_get_handler()]
    except Exception as e:
        print(f"[langfuse] could not initialize callback handler, tracing disabled: {e}")
        return []
