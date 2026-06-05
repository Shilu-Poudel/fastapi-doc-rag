# Technical Overview

This document explains the design of the Modular RAG Backend: the stack, the
module layout, the two request flows, and the key design decisions.

## Stack

- Web: FastAPI + Uvicorn.
- Agent: LangGraph prebuilt ReAct agent (tool-calling).
- LLM: Groq via the OpenAI-compatible API (`langchain-openai` ChatOpenAI).
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`, run locally on CPU.
- Vector store: Qdrant (`qdrant-client`).
- Memory: Redis.
- Relational DB: SQLAlchemy 2.0 (SQLite by default).
- PDF parsing: PyMuPDF.
- Config: pydantic-settings (`.env`).

## Module layout

- `app/core/config.py` - typed settings loaded from environment / `.env`.
- `app/core/logging.py` - logging setup.
- `app/db/models.py` - `ChunkMetadata` and `Booking` ORM models.
- `app/db/session.py` - engine, session factory, `init_db`, `get_db`.
- `app/schemas/` - Pydantic request/response models.
- `app/services/text_extractor.py` - PDF/TXT to text.
- `app/services/chunking.py` - recursive, sentence, and fixed strategies.
- `app/services/embeddings.py` - local embedding model wrapper.
- `app/services/vectorstore.py` - Qdrant collection wrapper (upsert/search).
- `app/services/memory.py` - Redis conversation history.
- `app/services/email_service.py` - SMTP confirmation email.
- `app/services/booking.py` - booking validation and persistence.
- `app/services/agent.py` - LangGraph agent and its tools.
- `app/api/v1/routers/ingestion.py`, `chat.py` - the two endpoints.
- `app/main.py` - application factory wiring routers.

## Ingestion flow (POST /api/v1/ingest)

1. Validate content type (PDF or TXT) and size.
2. Extract text with PyMuPDF (PDF) or decode (TXT).
3. Chunk with the requested strategy (`recursive` by default).
4. Reject if chunk count exceeds the configured cap.
5. Embed every chunk locally with sentence-transformers.
6. Upsert each vector into Qdrant with `{text, file_name, chunk_index}` payload.
7. Persist one `ChunkMetadata` row per chunk (file name, index, strategy,
   embedding model, vector id, text).

## Chat flow (POST /api/v1/chat)

1. Load the user's prior messages from Redis.
2. Append the new user message and invoke the LangGraph agent with a bounded
   recursion limit.
3. The agent reasons and may call tools:
   - `retrieve_context(query)` - embeds the query, searches Qdrant, returns the
     top matching chunks as grounding context.
   - `book_interview(full_name, email, date, time)` - validates the fields,
     stores a `Booking`, and sends a confirmation email.
4. The final assistant message is returned and both turns are appended to Redis.
5. Any backend failure (LLM, Qdrant, Redis) returns HTTP 503; hitting the
   recursion limit also returns 503.

## Why these choices

- LangGraph over RetrievalQA: the task forbids RetrievalQA and requires an agent
  that reasons through tools. LangGraph gives an explicit, inspectable tool-using
  loop with a built-in recursion bound.
- Local embeddings: the task allows any embedding method. A local
  sentence-transformers model removes the dependency on a paid embedding API and
  runs fully offline; only the chat LLM uses an external (free-tier) API.
- Qdrant only: the in-memory placeholder store was removed so retrieval always
  uses real similarity search. Qdrant is one of the allowed databases
  (FAISS/Chroma are excluded).
- Cosine distance: see `reports/FINDINGS.md` - cosine matches the accuracy of
  dot and Euclidean on normalized embeddings while giving interpretable scores.

## Resilience and safety

- Upload size and chunk-count caps bound memory use per request.
- Booking email/date/time are validated; the email regex also blocks header
  injection. Invalid input is reported back to the agent so it can re-ask.
- SMTP failures are logged and never block booking persistence.
- The chat endpoint wraps agent execution and degrades to HTTP 503 on failure.

## Testing and benchmarking

- `pytest` covers endpoint validation paths.
- `benchmarks/run_benchmark.py` measures retrieval accuracy and latency across
  chunking strategies, embedding models, and Qdrant distances; results are in
  `reports/FINDINGS.md`.

## Out of scope

Authentication, rate limiting, and observability are not implemented and should
be added before public deployment.
