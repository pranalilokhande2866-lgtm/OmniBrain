"""
Shared LLM client construction. Every agent node imports get_chat_llm()
or get_vision_llm() from here rather than constructing a provider
client directly, so model choice / provider selection stays consistent
across every node and swapping providers means editing only this file.

Auto-detects which provider to use based on which API key is set:
  - GOOGLE_API_KEY set  -> Gemini (gemini-2.0-flash by default). Free
                           tier, no billing required - see
                           https://aistudio.google.com/apikey. Natively
                           multimodal, so the same model/client handles
                           both get_chat_llm() and get_vision_llm().
  - OPENAI_API_KEY set  -> GPT-4o (the brief's original spec).
  - Both set            -> Gemini is preferred (it's free); this has no
                           effect on output quality/correctness, only
                           on which paid/free service gets called.
  - Neither set         -> raises a clear RuntimeError telling you which
                           env var to set, rather than a cryptic
                           downstream provider error.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import settings

_NO_KEY_ERROR = (
    "No LLM API key is configured. Set GOOGLE_API_KEY in your .env for a free "
    "option (get one at https://aistudio.google.com/apikey, no billing needed), "
    "or OPENAI_API_KEY if you have OpenAI credits. See .env.example."
)


def extract_text(response) -> str:
    """
    Normalizes an AIMessage's .content into a plain string.

    OpenAI-style models return .content as a plain string. Gemini
    (via langchain_google_genai) can return .content as a LIST of
    content blocks instead - e.g. [{"type": "text", "text": "hello",
    "extras": {"signature": "..."}}] - when the model includes a
    "thinking" signature alongside its answer. Every agent node calls
    this instead of touching response.content directly, so a raw
    AttributeError ('list' object has no attribute 'strip'/'lower')
    never leaks out of a node - confirmed against a real Gemini
    response, not just the OpenAI-shaped case this code was
    originally written against.
    """
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content)


@lru_cache(maxsize=1)
def get_chat_llm():
    if settings.has_google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.google_chat_model, temperature=0, google_api_key=settings.google_api_key
        )
    if settings.has_openai_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.openai_chat_model, temperature=0, api_key=settings.openai_api_key)
    raise RuntimeError(_NO_KEY_ERROR)


@lru_cache(maxsize=1)
def get_vision_llm():
    if settings.has_google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.google_vision_model, temperature=0, google_api_key=settings.google_api_key
        )
    if settings.has_openai_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.openai_vision_model, temperature=0, api_key=settings.openai_api_key)
    raise RuntimeError(_NO_KEY_ERROR)
