from fastapi import FastAPI

from app.api.v1.routers import chat, ingestion
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import init_db


def create_app() -> FastAPI:
    configure_logging()
    init_db()

    app = FastAPI(title=settings.app_name)
    app.include_router(
        ingestion.router, prefix=f"{settings.api_v1_prefix}/ingest", tags=["ingestion"]
    )
    app.include_router(
        chat.router, prefix=f"{settings.api_v1_prefix}/chat", tags=["chat"]
    )
    return app


app = create_app()
