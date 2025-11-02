# Modular FastAPI Backend (RAG)

A modular FastAPI backend that implements Retrieval-Augmented Generation (RAG) with document ingestion, chunking, embeddings, vector search, and a chat endpoint with conversation memory.

## Overview
- Ingest PDF/TXT documents, extract text, chunk, and generate embeddings
- Store vectors and metadata for retrieval during Q&A
- Chat endpoint uses prior turns to maintain context (memory)
- Pluggable LLM via environment configuration (e.g., Groq)

## Quick Start
- Create a virtual environment and install dependencies:
  - `python -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Copy environment template and fill required keys:
  - `cp .env.example .env`
- Run the development server:
  - `uvicorn app.main:app --reload`

## API Docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints
- `POST /ingest`
  - Multipart upload: `file` (PDF or TXT)
  - Example:
    - `curl -X POST http://localhost:8000/ingest -F "file=@./path/to/document.pdf"`
- `POST /chat`
  - JSON body: `{"user_query": "...", "conversation_history": ["..."]}`
  - Example:
    - `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"user_query":"What is in the document?","conversation_history":[]}'`

## Configuration
These are commonly used variables. See `.env.example` for the full list and defaults.
- `GROQ_API_KEY` – API key for Groq LLM (if enabled)
- `GROQ_MODEL` – Model name for chat completions
- `DATABASE_URL` – SQLAlchemy database URL (e.g., SQLite)
- `REDIS_URL` – Redis connection string for conversation memory (optional)
- `VECTOR_STORE_URL` / `VECTOR_STORE_API_KEY` – Vector DB configuration (if using a remote store)

## Project Structure
- `app/main.py` – FastAPI app creation and router registration
- `app/api/v1/routers` – API route handlers for ingestion and chat
- `app/core` – Config and logging setup
- `app/db` – Database base and session
- `app/models` – ORM models (documents, vector storage)
- `app/schemas` – Pydantic request/response schemas
- `app/services` – Business logic (embeddings, RAG, ingestion)
- `app/utils` – Helpers (chunking, text, memory, db)
- `tests` – Pytest suite for ingestion and chat

## Running Tests
- `pytest` (ensure your virtual environment is active)

## Docker (optional)
- Build: `docker build -t modular-fastapi-backend .`
- Run: `docker run -p 8000:8000 --env-file .env modular-fastapi-backend`

## Notes
- Use `.env` to switch between local and remote services (LLM, vector DB)
- For production: add authentication, robust error handling, and request rate limiting
- Ensure large PDFs are chunked appropriately to control embedding costs and latency