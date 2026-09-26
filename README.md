# OmniBrain — Agentic Multi-Modal RAG Orchestrator

An agentic RAG system for querying complex financial PDFs (narrative text,
tables, charts) with multi-step reasoning, self-correction, and grounded
citations. Built for the Axlero Solutions ML portfolio brief — Project 1.

A LangGraph supervisor routes each query to whichever sub-agent can answer
it: a **Search** agent over a multi-modal Qdrant index, a **Text-to-SQL**
agent over historical stock/financial data, or a **Vision** agent that reads
charts directly off the PDF page using GPT-4o. A **Self-RAG** loop grades
retrieval quality and rewrites the query on a miss. **NeMo Guardrails**
blocks out-of-scope questions before the pipeline runs. **Langfuse** traces
every run.

## How this was built

This scaffold wasn't written from memory and left untested. Every piece that
doesn't require a paid API key was actually run during development, most of
it against a real 582-page corporate annual report:

| Component | How it was verified |
|---|---|
| PDF parsing (text/tables/images) | Ran against a real 582-page annual report — found real financial tables (e.g. a 15×3 table on page 281) and 100+ images across the document |
| Chunking | Unit-level checks on the word-window splitter |
| Qdrant vector store | Real local-mode upsert + cosine search + metadata filtering, round-tripped and checked for correct nearest-neighbor ordering |
| Synthetic stock DB | Seeded and queried via real SQLite |
| SQL safety guardrail | Confirmed it blocks `DROP`/`DELETE`/chained-injection attempts and only allows `SELECT` |
| **LangGraph control flow** | All 5 paths (search-hit, search-miss→retry→hit, retries-exhausted, SQL route, vision route) run end-to-end with a fake deterministic LLM standing in for GPT-4o, including a real PDF page rasterized and fed through the vision path |
| NeMo Guardrails config | Loaded and constructed against the **actual installed library's own shipped example** (not written from memory) — the block-detection logic was written by reading the library's source for how `self check input` actually signals a refusal |
| FastAPI app | `/health` and `/documents/upload` hit over real HTTP via `TestClient`, including the full parse→chunk→store pipeline against a real PDF slice |
| Streamlit frontend | Actually booted headless and confirmed serving HTTP 200 |

Two things could **not** be exercised inside the sandbox this was built in,
purely due to its network allowlist (not a code issue):
- **Embedding models** (`sentence-transformers`) download weights from
  `huggingface.co` on first use, which wasn't reachable from the build
  sandbox — so embedding calls were mocked with fixed-size dummy vectors
  in tests, while everything around them (chunking, storage, retrieval,
  filtering) was tested for real. This will download automatically the
  first time you run it, given normal internet access.
- **GPT-4o reasoning calls** need your own `OPENAI_API_KEY` and were stood
  in for with a fake LLM during testing (see the LangGraph row above) —
  the *control flow* is proven correct; the *quality* of GPT-4o's actual
  routing/grading/answers is naturally only testable with a real key.

One real bug was caught and fixed this way: the guardrails wrapper
originally only caught errors from constructing the rails object, not from
the actual check call — a transient network/API issue would have crashed
`/query` instead of failing open as intended. Testing surfaced it; it's
fixed in `guardrails_client.py`.

# 🧠 OmniBrain — Agentic Multi-Modal RAG Orchestrator

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> An agentic RAG orchestrator that goes beyond plain-text retrieval — parsing financial
> PDFs with embedded tables and charts, and routing multi-step queries across specialized
> AI agents to produce accurate, cited, hallucination-checked answers.

## 📌 Overview

Standard RAG pipelines break down on real-world financial documents: they can't read
tables, can't interpret charts, and can't reason across multiple data sources in one
query. **OmniBrain** solves this with an agentic architecture — a LangGraph supervisor
dynamically routes each query to the right specialist:

- 🔍 **Search Agent** — semantic retrieval over document text (Qdrant vector DB)
- 📊 **Vision Agent** — reads charts and tables using a Vision-Language Model (GPT-4o)
- 🗄️ **SQL Agent** — queries structured historical stock data via Text-to-SQL

The agents' findings are synthesized into a single, cited investment memo — with a
guardrails layer (Langfuse + grounding checks) to catch hallucinations before they
reach the user.

**Example use case:** A quant analyst uploads a 500-page 10-K filing and asks
*"Summarize Q3 revenue trends and compare to 5-year stock performance."* OmniBrain
pulls the relevant chart, reads it, queries historical price data, retrieves supporting
text, and returns one grounded answer — with sources.

## ⚙️ Tech Stack

| Layer | Tools |
|---|---|
| Orchestration | LangGraph, LangChain |
| Retrieval | Qdrant, CLIP embeddings |
| Vision | GPT-4o |
| Structured data | SQLite, Text-to-SQL |
| Evaluation | Langfuse, custom grounding guardrails |
| Interface | Streamlit |

## Project Structure

```
omnibrain/
├── ingestion/       # PDF parsing, chunking, embedding (Vineet)
│   └── __init__.py
├── agents/           # Search Agent, SQL Agent, Vision Agent (Sanskriti)
│   └── __init__.py
├── orchestrator/     # LangGraph supervisor, state, routing (Sanskriti)
│   └── __init__.py
├── eval/             # Langfuse tracing, guardrails, test query set (Pranali)
│   └── __init__.py
├── app/               # Streamlit demo UI (Pranali)
│   └── __init__.py
├── data/
│   ├── raw/           # source PDFs (not committed)
│   └── processed/      # extracted chunks, SQLite db (not committed)
├── requirements.txt
├── .env.example
└── README.md
```


## Setup

```bash

bash scripts/setup.sh        # creates venv, installs deps, seeds the stock DB
# edit .env and add your OPENAI_API_KEY
bash scripts/run_dev.sh      # starts FastAPI (:8000) + Streamlit (:8501)
```

Or manually:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then add OPENAI_API_KEY
cd backend && python -m app.db.init_db && cd ..
(cd backend && uvicorn app.main:app --reload) &
(cd frontend && streamlit run streamlit_app.py)
```

Then open the Streamlit UI, upload a PDF (a slice of pages is fine for fast
iteration — e.g. pages 1–50), and ask it questions.

**Nothing else needs installing or configuring to get started.** Qdrant runs
in embedded/local mode by default (writes to `data/qdrant_storage/`, no
server process). `docker-compose.yml` is there for when you want a real
Qdrant server instead — optional, not required.

## Architecture

```
                              ┌─────────────┐
                    ┌────────▶│  Supervisor │◀── classifies the query
                    │         └──────┬──────┘
                    │        route:  │  sql
             search/vision           │
                    │                ▼
                    ▼           ┌─────────┐
              ┌───────────┐     │   SQL   │── reads stock_data.db (synthetic)
              │  Search   │     └────┬────┘
              │ (Qdrant:  │          │
              │ text+CLIP)│          │
              └─────┬─────┘          │
           route:   │                │
      ┌─────vision──┼──search────┐   │
      ▼             │            ▼   │
 ┌─────────┐         │      ┌────────┐│
 │ Vision  │         │      │ Grade  ││   Self-RAG loop:
 │ (GPT-4o)│         │      └───┬────┘│   irrelevant + retries left
 └────┬────┘         │    relevant│irrelevant
      │               │          │    │
      │               │          │    ▼
      │               │          │ ┌────────┐
      │               │          │ │Rewrite │──▶ back to Search
      │               │          │ └────────┘
      │               ▼          ▼
      └──────────▶ ┌─────────────────┐
                    │   Synthesize    │──▶ final answer + citations
                    └─────────────────┘
```

Guardrails (`self check input`) sits in front of all of this, in
`routes_query.py` — an out-of-scope question never reaches the graph.

### Why two embedding collections, not one

Text chunks use `all-MiniLM-L6-v2` (384-dim); images use CLIP
`clip-ViT-B-32` (512-dim), both local via `sentence-transformers` — no API
cost to ingest a 500-page report. They're kept in **separate** Qdrant
collections because the dimensions differ and because CLIP's own text
encoder caps out at 77 tokens (too short for a real text chunk) — CLIP is
used only to embed the user's *query* for cross-modal image search, not to
embed the chunks themselves.

### Why the vision agent re-rasterizes pages on demand

Qdrant only stores image *metadata* (doc name, page, dimensions), not raw
bytes — keeping binary blobs out of the vector DB is standard practice and
keeps the collection size sane on a 500+ page report. When the vision agent
actually needs pixels for GPT-4o, it re-renders that exact page from the
source PDF at query time. This also means GPT-4o sees the full page in
context (axis labels, legends, surrounding text) rather than a tightly
cropped embedded image.

### Why the SQL agent never lets the LLM touch the database

`sql_agent.py` only asks the LLM for query *text*. `db/query_executor.py` is
the sole place that opens a `sqlite3` connection, and it independently
re-validates the statement (SELECT-only, keyword blocklist, read-only
connection URI) regardless of what the LLM wrote — tested against actual
`DROP`/`DELETE`/chained-injection attempts.

## ⚠️ The stock data is synthetic

`data/stock_data.db` is a **seeded random walk**, not real Tata Steel
numbers — it exists purely so the Text-to-SQL agent has something real to
query out of the box. Don't present numbers pulled from it as real
financial data (portfolio write-up, interview, demo narration) without
saying so — or swap in a real feed (NSE/BSE historical data, yfinance,
Alpha Vantage) before relying on it for anything beyond exercising the
pipeline. See the docstring in `backend/app/db/init_db.py`.

## Project layout

```
backend/app/
  ingestion/     PDF parsing, chunking, text + image embedders, pipeline
  vectorstore/   Qdrant wrapper (2 collections: text_chunks, image_chunks)
  db/            Synthetic stock DB + safe read-only query executor
  agents/        LangGraph state, each node, and the compiled graph
  guardrails/    NeMo Guardrails config + Python wrapper
  observability/ Langfuse callback wiring (optional)
  api/           FastAPI routes (health, upload, query)
  main.py        FastAPI app entrypoint
frontend/
  streamlit_app.py   Chat UI: upload, ask, see routing + citations
backend/tests/
  test_graph_flow.py   LangGraph control-flow tests (fake LLM)
  test_api.py          FastAPI integration tests (real PDF, mocked embeddings)
scripts/
  setup.sh, run_dev.sh
```

## Week-by-week (matches the brief)

- **Week 1** — `ingestion/`, `vectorstore/`, `api/routes_upload.py`. Ingest
  and inspect: `curl -F file=@report.pdf "localhost:8000/documents/upload?page_end=50"`
- **Week 2** — `agents/graph.py`'s supervisor + routing, `frontend/`. Mid-review
  check: ask a stock-price question vs. a narrative question and watch the
  `route` field/badge differ.
- **Week 3** — `agents/self_rag.py` (rewrite loop), `guardrails/`. Try a query
  that's genuinely off-topic to see the guardrail fire.
- **Week 4** — `observability/langfuse_client.py` (add keys to `.env` to turn
  on tracing), citations already thread through from retrieval to the UI.

## Known limitations / next steps

- The Self-RAG grader and query rewriter are single LLM calls with no
  few-shot examples — works, but a portfolio write-up could show
  before/after examples of what gets rewritten and why.
- No conversation memory across turns yet (each query is independent) —
  LangGraph's checkpointer (`langgraph.checkpoint.memory.MemorySaver`,
  already a dependency) is the natural way to add it.
- No re-ranking step after retrieval — top-k cosine similarity only.
- `nemoguardrails`'s Colang 1.0 dialect is used here since it's what the
  installed version's own examples ship with; NVIDIA's newer Colang 2.0
  syntax is a possible upgrade if you want to showcase that instead.

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your keys
```

You'll also need Qdrant running locally:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

## Team Roles (Week 1)

| Person | Owns | Week 1 Goal |
|---|---|---|
| A | `ingestion/` | Parse 1 sample PDF into text chunks + table/chart images |
| B | `orchestrator/`, `agents/` | LangGraph skeleton with dummy agent responses |
| C | `eval/`, `app/` | Langfuse account + stock data in SQLite |

## Status
🚧 Week 1 — foundations in progress

