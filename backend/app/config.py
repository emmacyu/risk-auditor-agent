from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/app/config.py (自身) -> app (退1层) -> backend (退2层) -> root (退3层)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"

class Settings(BaseSettings):
    # if these variables are not found in the environment variables or .env file, Pydantic will throw an exception immediately when this file is imported, refusing to start.
    OPENROUTER_API_KEY: str
    DATABASE_URL: str
    REDIS_URL: str
    
    # Optional parameters with default fallbacks
    LLM_MODEL: str = "openai/gpt-4o-mini"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # 精准锁定绝对路径
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH), 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()  # singleton
