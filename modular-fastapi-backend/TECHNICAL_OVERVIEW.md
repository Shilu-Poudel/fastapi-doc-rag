# Technical Overview — Modular FastAPI Backend (RAG)

This document explains the project from basics to advanced: stack, architecture, data flows, dependencies, resilience patterns, and how to discuss it in an interview.

## Summary
- FastAPI backend implementing Retrieval-Augmented Generation (RAG)
- Document ingestion (PDF/TXT) → text extraction → chunking → embeddings → vector search
- Chat endpoint with conversation memory; pluggable LLM provider (e.g., Groq)
- Modular layers: API, services, utils, models, schemas, core config, DB

## Stack & Key Dependencies
- Web framework: `fastapi`, server: `uvicorn`
- Data & infra: `sqlalchemy`, `redis`/`aioredis`, `qdrant-client`
- Parsing/IO: `pymupdf` (PDF text extraction), `requests` (HTTP to LLMs)
- Config & validation: `python-dotenv`, `pydantic`
- Tests: `pytest` (see `tests/`)

Version hints (see `requirements.txt`): FastAPI ≥0.95, Uvicorn ≥0.22, Qdrant-client ≥1.7, SQLAlchemy ≥1.4, Redis ≥4.5, PyMuPDF ≥1.22.

## Architecture
- `app/main.py`: creates FastAPI app, registers routers
- `app/api/v1/routers`: HTTP endpoints (document ingestion, chat)
- `app/services`: domain logic (ingestion, embeddings, RAG, vector store)
- `app/utils`: helpers (chunking, text processing, redis memory, embeddings utils)
- `app/models`: ORM models (e.g., document, vector store)
- `app/schemas`: Pydantic request/response models
- `app/core`: configuration and logging
- `app/db`: SQLAlchemy base/session
- `tests`: ingestion and conversation tests

## Ingestion Pipeline (Basics → Advanced)
1. Upload: `POST /ingest` accepts PDF/TXT via multipart form `file`
2. Extract: `text_extractor.py` pulls raw text (PDF via PyMuPDF)
3. Chunk: `utils/chunking.py` splits into manageable pieces (fixed size or sentence-aware)
4. Embed: `services/embeddings.py` →
   - Primary: OpenAI embeddings API (if `OPENAI_API_KEY` present)
   - Resilience: retries with exponential backoff on 429/5xx
   - Fallback: a deterministic local embedding when API fails or key missing
5. Store: `services/vectorstore.py` + `models/vector_store.py`
   - Persist vectors and metadata (Qdrant or local strategy, depending on env)
   - Metadata stored in relational DB via SQLAlchemy

## RAG Conversation Flow
1. Input: `POST /chat` accepts `{ user_query, conversation_history }`
2. Retrieve: generate embeddings for the query → similarity search in vector store → get top-k relevant chunks
3. Compose prompt: combine user query + retrieved context + (optionally) prior turns
4. Generate: call LLM via `call_groq_completion(...)`
   - Primary: Groq chat completions (`/chat/completions`) if `GROQ_API_KEY` provided
   - Fallbacks: OpenAI completions if configured, otherwise safe fallback string
5. Memory: append response to `conversation_history`; optional Redis-based memory in `utils/redis_memory.py`
6. Respond: return structured `ChatResponse`

## Memory Strategy
- Conversation history passed in the request schema, updated on each turn
- Optional Redis utilities prepared (`utils/redis_memory.py`) to persist/recall per user/session
- Rationale: enables multi-turn context retention; decouples memory from stateless HTTP

## Vector Store Strategy
- Similarity search on embeddings to retrieve relevant context
- Can be backed by Qdrant (`qdrant-client`) or a local approximation depending on configuration
- Metadata ties chunks to documents; facilitates provenance and future re-ranking

## Resilience & Error Handling
- Embeddings: retries on rate limits/server errors; deterministic fallback embeddings
- LLM completions: try Groq → fallback to OpenAI → return safe message if both unavailable
- API errors: use `HTTPException` with meaningful status codes/messages
- Configuration loaded via `.env` with defaults to avoid hard failures

## Configuration (.env)
Common keys (see `.env.example`):
- `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `OPENAI_BASE_URL`
- `GROQ_API_KEY`, `GROQ_BASE_URL`, `LLM_MODEL`
- `DATABASE_URL` (e.g., SQLite), `REDIS_URL`
- `VECTOR_STORE_URL`, `VECTOR_STORE_API_KEY` (if remote vector DB)

## Endpoints
- `POST /ingest`
  - Form: `file=@document.pdf|.txt`
  - Returns document metadata or success status
  - Example: `curl -X POST http://localhost:8000/ingest -F "file=@./docs/sample.pdf"`
- `POST /chat`
  - JSON: `{ "user_query": "...", "conversation_history": [] }`
  - Returns assistant reply with updated conversation history
  - Example:
    ```bash
    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -d '{"user_query":"Summarize the ingested doc.","conversation_history":[]}'
    ```

Note: Some tests expect `/api/v1/...`. Verify your router prefixes in `app/main.py` and adjust accordingly.

## Testing
- Run: `pytest`
- Coverage areas:
  - Document ingestion success/validation
  - Chat path: empty/invalid payloads; memory behavior

## Deployment
- Dev: `uvicorn app.main:app --reload`
- Docker:
  - `docker build -t modular-fastapi-backend .`
  - `docker run -p 8000:8000 --env-file .env modular-fastapi-backend`
- Production considerations: auth, rate limiting, observability, background workers for batch ingestion

## Interview Talking Points
- Why RAG: reduces hallucinations by grounding LLM with retrieved context
- Resilience: retries + fallbacks for embeddings and completions; graceful degradation
- Modularity: clean separation between API, services, utils, and data layers
- Memory design: stateless request carries history; optional Redis persistence for scalability
- Trade-offs: chunk sizing vs. retrieval quality; vector DB choice (Qdrant/local) vs. operational complexity
- Security: env-based secrets; recommend adding auth, input validation hardening, and PII handling
- Performance: async FastAPI, batched embeddings, caching strategies (future)

## Future Improvements
- Router versioning alignment (`/api/v1`) across tests and runtime
- Ensemble retrieval: hybrid sparse+dense search, re-ranking
- Streaming responses from LLM for better UX
- Background task queues for ingestion (Celery/RQ) and rate control
- Observability: metrics, tracing, structured logs shipped to a backend