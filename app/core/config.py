from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Modular RAG Backend"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "info"

    # Safety limits
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB
    max_chunks: int = 1000
    agent_recursion_limit: int = 12

    # Relational storage (metadata + bookings)
    database_url: str = "sqlite:///./app.db"

    # Conversation memory
    redis_url: str = "redis://localhost:6379/0"

    # Vector store (Qdrant)
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "documents"

    # Embeddings (local sentence-transformers model)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Chat model (Groq, OpenAI-compatible API)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-120b"

    # SMTP for booking confirmation emails
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()