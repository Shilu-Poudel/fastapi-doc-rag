# Modular RAG Backend

A FastAPI backend with two REST APIs: a document ingestion pipeline and an
agentic Retrieval-Augmented Generation (RAG) service with conversational memory
and interview booking.

## Features

- Document ingestion: upload PDF/TXT, extract text, chunk, embed, and store
  vectors in Qdrant with metadata in a relational database.
- Agentic RAG: a LangGraph agent that reasons through tools (document retrieval
  and interview booking) instead of a fixed RetrievalQA chain.
- Conversational memory: per-user chat history in Redis.
- Interview booking: the agent captures full name, email, date and time, stores
  the booking, and sends an SMTP confirmation email.
- Local embeddings: a sentence-transformers model runs on-device, so no
  embedding API key or billing is required.

## Architecture

```
app/
  core/        configuration (pydantic-settings) and logging
  db/          SQLAlchemy models and session (chunk metadata, bookings)
  schemas/     Pydantic request/response models
  services/    text extraction, chunking, embeddings, vector store,
               memory, email, booking, and the LangGraph agent
  api/v1/routers/   ingestion and chat endpoints
  main.py      application factory
benchmarks/    retrieval benchmark harness and corpus
reports/       FINDINGS.md (chunking, embedding and similarity comparisons)
tests/         pytest suite
```

## Tech stack

| Concern        | Choice                                              |
|----------------|-----------------------------------------------------|
| Web framework  | FastAPI + Uvicorn                                   |
| Agent          | LangGraph (tool-calling ReAct agent)               |
| LLM            | Groq (OpenAI-compatible API)                        |
| Embeddings     | sentence-transformers/all-MiniLM-L6-v2 (local, 384d)|
| Vector store   | Qdrant                                              |
| Memory         | Redis                                               |
| Database       | SQLAlchemy (SQLite by default)                      |
| PDF parsing    | PyMuPDF                                             |

## Quick start

1. Start Qdrant and Redis:
   ```bash
   docker compose up -d
   ```
2. Create the environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Configure secrets: copy `.env.example` to `.env` and set `GROQ_API_KEY`
   (and the `SMTP_*` values if you want confirmation emails to send).
4. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```
5. Open the interactive docs at `http://localhost:8001/docs`.

## API

### POST /api/v1/ingest

Upload a PDF or TXT document.

- `file` (multipart): the document.
- `chunking_strategy` (query): `recursive` (default), `sentence`, or `fixed`.

```bash
curl -X POST "http://localhost:8001/api/v1/ingest?chunking_strategy=recursive" \
  -F "file=@sample_content.txt;type=text/plain"
```

Response:
```json
{
  "file_name": "sample_content.txt",
  "chunking_strategy": "recursive",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "chunks_ingested": 3
}
```

### POST /api/v1/chat

Ask a grounded question or book an interview. Reuse the same `user_id` for
multi-turn context.

```bash
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","query":"What is deep learning?"}'

curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","query":"Book an interview. Name Jane Doe, email jane@example.com, date 2026-06-25, time 10:00"}'
```

Response:
```json
{ "user_id": "u1", "response": "..." }
```

## Configuration

All settings load from `.env` (see `.env.example`). Key variables:

- `GROQ_API_KEY`, `GROQ_BASE_URL`, `LLM_MODEL` - chat model.
- `EMBEDDING_MODEL`, `EMBEDDING_DIM` - local embedding model and its dimension.
- `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` - vector store.
- `REDIS_URL` - conversation memory.
- `DATABASE_URL` - relational store for metadata and bookings.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` - email.
  Leave `SMTP_HOST` blank to skip sending (booking still succeeds).

## Findings reports

See [reports/FINDINGS.md](reports/FINDINGS.md) for the comparison of chunking
strategies, embedding models, and Qdrant similarity algorithms on retrieval
accuracy and latency. Reproduce with:

```bash
.venv/bin/python -m benchmarks.run_benchmark
```

## Tests

```bash
.venv/bin/python -m pytest
```

## Safety limits

- Upload size capped (`max_upload_bytes`) and chunk count capped (`max_chunks`).
- Booking inputs (email, date, time) are validated before persistence.
- Agent runs under a bounded recursion limit; failures return HTTP 503.

## Out of scope

Authentication and rate limiting are not implemented; add them before exposing
this service publicly.
