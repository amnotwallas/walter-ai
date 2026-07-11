from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
import yaml
import pathlib

@lru_cache()
def _load_llm_yaml() -> dict:
    path = pathlib.Path("config/llm.yml")
    if not path.exists():
        path = pathlib.Path("config/llm.yml.example")
    if not path.exists():
        raise FileNotFoundError("Neither config/llm.yml nor config/llm.yml.example was found.")
    with path.open() as f:
        data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}


class Settings(BaseSettings):
    """
    Application settings and environment configuration.
    Uses Pydantic BaseSettings to automatically load variables from .env file.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_KEY: str  # Secret token to secure the API access
    APP_VERSION: str = "1.0.4"
    
    # Optional provider keys - LiteLLM picks up whichever matches the active model prefix
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    @property
    def llm_model(self) -> str:
        return _load_llm_yaml()["model"]

    @property
    def llm_temperature(self) -> float:
        return float(_load_llm_yaml().get("temperature", 0.5))

@lru_cache()
def get_settings():
    """
    Returns a cached instance of the settings.
    LRU Cache ensures the settings are only loaded once.
    """
    return Settings()
