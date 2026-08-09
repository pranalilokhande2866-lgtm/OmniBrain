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
