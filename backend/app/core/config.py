import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./rag.db"
    SECRET_KEY: str = "your-super-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL: str = "mistral-small-latest"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    QDRANT_PATH: str = "./data/qdrant"
    COLLECTION_NAME: str = "popatkus_documents"
    FINAL_TOP_K: int = 5
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 700

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
