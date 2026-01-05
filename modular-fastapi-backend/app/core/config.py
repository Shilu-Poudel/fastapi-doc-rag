from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Modular FastAPI Backend"
    api_version: str = "v1"
    debug: bool = False

    # Database settings
    database_url: str = "sqlite:///./app.db"

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # Pydantic v2: use model_config instead of deprecated Config
    model_config = {
        "env_file": ".env",
        "env_prefix": "",
    }

settings = Settings()