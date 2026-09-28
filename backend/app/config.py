from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    FORESIGHT_MODE: str = "offline"  # live | offline
    PORT: int = 8000
    API_KEY: str = "foresight-secret-key-123"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    GROQ_API_KEY: str | None = None
    GROQ_PRIMARY_MODEL: str = "openai/gpt-oss-120b"
    GROQ_FALLBACK_MODEL: str = "qwen/qwen3-32b"

    HINDSIGHT_API_KEY: str | None = None
    HINDSIGHT_API_URL: str = "https://api.hindsight.vectorize.io"
    HINDSIGHT_BANK_ID: str = "foresight-paynest"

settings = Settings()
