import os
from typing import Any

import requests
import streamlit as st


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

LANGUAGES = [
    "English", "Hindi", "Spanish", "French", "German", "Portuguese",
    "Arabic", "Mandarin Chinese", "Japanese", "Bengali", "Tamil", "Telugu",
]

st.set_page_config(
    page_title="OmniBrain",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap');

        :root {
            --bg: #0d0f12;
            --panel: #14171c;
            --panel-hover: #191d23;
            --panel-raised: #1b1f26;
            --border: #2a3039;
            --border-soft: #20252d;
            --text: #edf0f4;
            --text-secondary: #a7b0bd;
            --text-muted: #727d8d;
            --accent: #d8a85c;
            --accent-hover: #e6bb72;
            --accent-soft: rgba(216, 168, 92, 0.12);
            --green: #73c69d;
            --red: #e88080;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
            font-family: "DM Sans", sans-serif;
        }

        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            max-width: 1060px;
            padding: 2.4rem 3rem 2rem;
        }

        section[data-testid="stSidebar"] {
            width: 315px !important;
            min-width: 315px !important;
            background: #101318;
            border-right: 1px solid var(--border-soft);
        }

        section[data-testid="stSidebar"] > div:first-child {
            padding: 1.5rem 1rem;
        }

        /* Brand */
        .brand-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 0.3rem;
        }

        .brand-icon {
            width: 29px;
            height: 29px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #5f4b2d;
            border-radius: 7px;
            background: var(--accent-soft);
            color: var(--accent);
            font-size: 1rem;
        }

        .brand-name {
            color: var(--text);
            font-family: "Libre Baskerville", serif;
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: -0.04em;
        }

        .brand-subtitle {
            margin: 0 0 2rem 39px;
            color: var(--text-muted);
            font-family: "DM Mono", monospace;
            font-size: 0.66rem;
            letter-spacing: 0.07em;
            text-transform: uppercase;
        }

        /* Main header */
        .workspace-label {
            color: var(--accent);
            font-family: "DM Mono", monospace;
            font-size: 0.69rem;
            font-weight: 500;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.85rem;
        }

        .workspace-title {
            margin: 0;
            color: var(--text);
            font-family: "Libre Baskerville", serif;
            font-size: 2.15rem;
            font-weight: 400;
            letter-spacing: -0.055em;
            line-height: 1.2;
        }

        .workspace-description {
            color: var(--text-secondary);
            font-size: 0.93rem;
            line-height: 1.55;
            margin: 0.75rem 0 1.7rem;
        }

        .context-bar {
            display: flex;
            align-items: center;
            gap: 9px;
            width: fit-content;
            padding: 0.55rem 0.75rem;
            margin-bottom: 1.6rem;
            color: var(--text-secondary);
            background: var(--panel);
            border: 1px solid var(--border-soft);
            border-radius: 7px;
            font-size: 0.8rem;
        }

        .context-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent);
        }

        /* Sidebar */
        .section-label {
            margin: 1.5rem 0 0.6rem;
            color: var(--text-muted);
            font-family: "DM Mono", monospace;
            font-size: 0.68rem;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .document-card {
            padding: 0.75rem 0.8rem;
            background: var(--accent-soft);
            border: 1px solid rgba(216, 168, 92, 0.25);
            border-radius: 7px;
            color: #e6d6b7;
            font-size: 0.82rem;
            line-height: 1.45;
            overflow-wrap: anywhere;
        }

        .document-card small {
            display: block;
            margin-top: 0.28rem;
            color: #aa9573;
            font-size: 0.73rem;
        }

        .empty-state {
            padding: 0.75rem 0;
            color: var(--text-muted);
            font-size: 0.82rem;
            line-height: 1.5;
        }

        .health-card {
            margin-top: 1.7rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-soft);
            color: var(--text-muted);
            font-family: "DM Mono", monospace;
            font-size: 0.68rem;
            line-height: 1.85;
        }

        .health-online {
            color: var(--green);
        }

        /* Chat */
        [data-testid="stChatMessage"] {
            padding: 1.15rem 0.15rem;
            background: transparent;
            border-bottom: 1px solid var(--border-soft);
        }

        [data-testid="stChatMessageContent"] {
            color: var(--text);
            font-size: 0.94rem;
            line-height: 1.7;
        }

        [data-testid="stChatMessageAvatarUser"] {
            background: #3c4656;
        }

        [data-testid="stChatMessageAvatarAssistant"] {
            background: #4a3922;
        }

        [data-testid="stChatInput"] {
            margin-top: 1.3rem;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 9px;
        }

        [data-testid="stChatInput"]:focus-within {
            border-color: #6e572f;
            box-shadow: 0 0 0 3px rgba(216, 168, 92, 0.08);
        }

        [data-testid="stChatInput"] textarea {
            color: var(--text) !important;
            font-family: "DM Sans", sans-serif;
            font-size: 0.9rem;
        }

        /* Citation panel */
        [data-testid="stExpander"] {
            margin-top: 0.8rem;
            background: var(--panel);
            border: 1px solid var(--border-soft);
            border-radius: 7px;
        }

        [data-testid="stExpander"] summary {
            color: var(--text-secondary);
            font-size: 0.79rem;
        }

        .citation {
            padding: 0.7rem 0;
            border-bottom: 1px solid var(--border-soft);
        }

        .citation:last-child {
            border-bottom: none;
        }

        .citation-title {
            color: #e3c68f;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .citation-meta {
            margin-top: 0.2rem;
            color: var(--text-muted);
            font-family: "DM Mono", monospace;
            font-size: 0.67rem;
        }

        .citation-snippet {
            margin-top: 0.42rem;
            color: var(--text-secondary);
            font-size: 0.78rem;
            line-height: 1.45;
        }

        .method-line {
            margin-top: 0.75rem;
            color: var(--text-muted);
            font-family: "DM Mono", monospace;
            font-size: 0.67rem;
        }

        .method-line strong {
            color: #bdc7d5;
            font-weight: 500;
        }

        /* Controls */
        .stButton > button,
        .stFormSubmitButton > button {
            min-height: 2.3rem;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--panel-raised);
            color: var(--text-secondary);
            box-shadow: none;
            font-family: "DM Sans", sans-serif;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .stButton > button:hover {
            border-color: #5e6876;
            color: var(--text);
            background: var(--panel-hover);
        }

        .stButton > button[kind="primary"] {
            border-color: var(--accent);
            background: var(--accent);
            color: #17120a;
        }

        .stButton > button[kind="primary"]:hover {
            border-color: var(--accent-hover);
            background: var(--accent-hover);
            color: #17120a;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: var(--panel);
            border: 1px dashed #3c4551;
            border-radius: 7px;
        }

        [data-testid="stFileUploaderDropzone"] * {
            color: var(--text-secondary) !important;
        }

        div[data-baseweb="select"] > div,
        div[data-testid="stNumberInput"] input {
            background: var(--panel) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
            border-radius: 6px !important;
        }

        label, [data-testid="stWidgetLabel"] p {
            color: var(--text-secondary) !important;
            font-size: 0.78rem !important;
        }

        .starter-card {
            padding: 1rem 1.1rem;
            background: var(--panel);
            border: 1px solid var(--border-soft);
            border-radius: 8px;
            color: var(--text-secondary);
            font-size: 0.86rem;
            line-height: 1.55;
        }

        .starter-card strong {
            color: var(--text);
        }

        .stAlert {
            border-radius: 7px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state():
    defaults = {
        "messages": [],
        "doc_name": None,
        "response_language": "English",
        "pending_query": None,
        "last_audio_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def request_error(error):
    try:
        if error.response is not None:
            return error.response.json().get("detail", str(error))
    except Exception:
        pass
    return str(error)


def get_health() -> dict[str, Any] | None:
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def render_citations(citations):
    if not citations:
        return

    with st.expander(f"View sources ({len(citations)})", expanded=False):
        for citation in citations:
            doc_name = citation.get("doc_name", "Source document")
            page = citation.get("page", "—")
            kind = citation.get("kind", "text").capitalize()
            snippet = citation.get("snippet", "")

            st.markdown(
                f"""
                <div class="citation">
                    <div class="citation-title">{doc_name}</div>
                    <div class="citation-meta">PAGE {page} · {kind}</div>
                    {f'<div class="citation-snippet">{snippet}</div>' if snippet else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_metadata(route, rewrite_count, citations):
    route_names = {
        "search": "Document retrieval",
        "sql": "Structured data",
        "vision": "Visual analysis",
    }

    if route:
        detail = f" · query refined {rewrite_count}×" if rewrite_count else ""
        st.markdown(
            f'<div class="method-line">ANALYSIS METHOD · '
            f'<strong>{route_names.get(route, route.title())}</strong>{detail}</div>',
            unsafe_allow_html=True,
        )

    render_citations(citations)


init_state()
health = get_health()

with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-icon">◈</div>
            <div class="brand-name">OmniBrain</div>
        </div>
        <div class="brand-subtitle">Document intelligence</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">Add document</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    with col1:
        page_start = st.number_input("Start page", min_value=1, value=1, step=1)
    with col2:
        page_end = st.number_input("End page", min_value=0, value=0, step=1)

    if uploaded and st.button("Index document", type="primary", use_container_width=True):
        params = {"page_start": page_start}
        if page_end > 0:
            params["page_end"] = page_end

        try:
            with st.spinner("Indexing document..."):
                response = requests.post(
                    f"{BACKEND_URL}/documents/upload",
                    files={
                        "file": (
                            uploaded.name,
                            uploaded.getvalue(),
                            "application/pdf",
                        )
                    },
                    params=params,
                    timeout=600,
                )
                response.raise_for_status()
                data = response.json()

            st.session_state.doc_name = data["doc_name"]
            st.success(f"Indexed {data['num_pages']} pages.")
        except requests.exceptions.RequestException as error:
            st.error(request_error(error))

    st.markdown('<div class="section-label">Research scope</div>', unsafe_allow_html=True)

    if st.session_state.doc_name:
        st.markdown(
            f"""
            <div class="document-card">
                {st.session_state.doc_name}
                <small>Answers restricted to this document</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Clear document scope", use_container_width=True):
            st.session_state.doc_name = None
            st.rerun()
    else:
        st.markdown(
            '<div class="empty-state">No document selected. Searches include your entire indexed library.</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">Answer language</div>', unsafe_allow_html=True)
    st.session_state.response_language = st.selectbox(
        "Answer language",
        LANGUAGES,
        index=LANGUAGES.index(st.session_state.response_language),
        label_visibility="collapsed",
    )

    collections = health.get("collections", {}) if health else {}
    provider = health.get("llm_provider", "none") if health else "none"
    provider_label = {"gemini": "Gemini", "openai": "OpenAI"}.get(provider, "Unavailable")

    if health:
        st.markdown(
            f"""
            <div class="health-card">
                <span class="health-online">● SYSTEM ONLINE</span><br>
                MODEL · {provider_label.upper()}<br>
                TEXT INDEX · {collections.get("text_chunks", 0):,}<br>
                IMAGE INDEX · {collections.get("image_chunks", 0):,}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="health-card">
                <span style="color: var(--red);">● BACKEND OFFLINE</span><br>
                {BACKEND_URL}
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="workspace-label">Research workspace</div>', unsafe_allow_html=True)
st.markdown(
    '<h1 class="workspace-title">Ask better questions of your documents.</h1>',
    unsafe_allow_html=True,
)

if st.session_state.doc_name:
    context_text = f"Focused on: {st.session_state.doc_name}"
else:
    context_text = "Searching across all indexed documents"

st.markdown(
    f"""
    <div class="workspace-description">
        Evidence-based answers with page-level references. Upload a report,
        select a scope, and investigate the details that matter.
    </div>
    <div class="context-bar">
        <span class="context-dot"></span>
        {context_text}
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        """
        <div class="starter-card">
            <strong>Begin with an investigation.</strong><br>
            Ask about key risks, performance trends, financial figures, strategic decisions,
            or specific claims made in a document.
        </div>
        """,
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            render_metadata(
                message.get("route"),
                message.get("rewrite_count", 0),
                message.get("citations", []),
            )

audio_value = st.audio_input("Ask by voice")

if audio_value is not None:
    audio_id = hash(audio_value.getvalue())

    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id

        try:
            with st.spinner("Transcribing..."):
                response = requests.post(
                    f"{BACKEND_URL}/audio/transcribe",
                    files={
                        "file": (
                            "recording.wav",
                            audio_value.getvalue(),
                            "audio/wav",
                        )
                    },
                    timeout=60,
                )
                response.raise_for_status()
                st.session_state.pending_query = response.json()["text"]
        except requests.exceptions.RequestException as error:
            st.error(f"Transcription failed: {request_error(error)}")

typed_prompt = st.chat_input("Ask a question about your documents...")
prompt = typed_prompt or st.session_state.pending_query

if prompt:
    st.session_state.pending_query = None
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Reviewing indexed evidence...")

        try:
            response = requests.post(
                f"{BACKEND_URL}/query",
                json={
                    "query": prompt,
                    "doc_name": st.session_state.doc_name,
                    "response_language": st.session_state.response_language,
                },
                timeout=180,
            )
            response.raise_for_status()
            data = response.json()

            answer = data.get("answer", "No answer was returned.")
            placeholder.markdown(answer)

            if data.get("blocked"):
                st.warning("This question is outside the currently allowed scope.")
            else:
                render_metadata(
                    data.get("route"),
                    data.get("rewrite_count", 0),
                    data.get("citations", []),
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "route": data.get("route"),
                    "rewrite_count": data.get("rewrite_count", 0),
                    "citations": data.get("citations", []),
                }
            )

        except requests.exceptions.RequestException as error:
            message = request_error(error)
            placeholder.error(message)
            st.session_state.messages.append(
                {"role": "assistant", "content": f"⚠ {message}"}
            )
