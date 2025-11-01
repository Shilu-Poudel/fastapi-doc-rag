# Modular FastAPI RAG Service

Overview
- Document ingestion (PDF/TXT) → chunk → embeddings → stored in Qdrant + metadata in SQLite
- Conversational RAG with memory in Redis and replies from Groq LLM
- Interview booking intent detection & persistence

Run locally
1. Create virtualenv and install deps:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy `.env.example` to `.env` and fill Qdrant and any other keys:
   cp .env.example .env

3. Start uvicorn:
   uvicorn app.main:app --reload

Endpoints
- POST /ingest
  - multipart form upload file (pdf or txt)
  - query param chunking_strategy=fixed|sentence
  - returns saved chunk metadata

- POST /chat
  - JSON: { "user_id": "user1", "query": "..." }
  - Returns assistant reply
  - Detects booking intent and persists to bookings table

Notes
- Qdrant and Groq credentials / URLs are expected via .env
- Embedding and LLM calls use either OPENAI_API_KEY or GROQ_API_KEY depending on env
- The chunking uses a simple whitespace token heuristic (approximate)
- This scaffold is intended for local development; production should add auth, robust error handling and batching