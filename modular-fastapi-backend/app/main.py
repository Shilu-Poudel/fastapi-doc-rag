from fastapi import FastAPI
from app.api.v1 import ingestion, chat  # Updated import path

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Modular RAG Service")
    app.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    return app

app = create_app()