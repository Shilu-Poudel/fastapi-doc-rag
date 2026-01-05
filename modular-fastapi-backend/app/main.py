from fastapi import FastAPI
from app.api.v1 import ingestion, chat  # Updated import path

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Modular RAG Service")
    # Align to tests expecting /api/v1/*
    app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    return app

app = create_app()