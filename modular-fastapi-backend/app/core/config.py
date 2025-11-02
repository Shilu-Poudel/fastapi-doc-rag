from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Modular FastAPI Backend"
    api_version: str = "v1"
    debug: bool = False

    # Database settings
    database_url: str

    # Redis settings
    redis_url: str

    class Config:
        env_file = ".env"

settings = Settings()