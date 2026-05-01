from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings and environment configuration.
    Uses Pydantic BaseSettings to automatically load variables from .env file.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GROQ_API_KEY: str
    API_KEY: str  # Secret token to secure the API access
    MODEL_NAME: str = "llama-3.1-8b-instant"
    APP_VERSION: str = "1.0.4"

@lru_cache()
def get_settings():
    """
    Returns a cached instance of the settings.
    LRU Cache ensures the settings are only loaded once.
    """
    return Settings()
