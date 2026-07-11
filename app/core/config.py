import os
import pathlib
from functools import lru_cache
from typing import Optional
import dotenv
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load dotenv at start to export keys to os.environ for LiteLLM
dotenv.load_dotenv()

def _load_llm_yaml() -> dict:
    path = pathlib.Path("app/config/config.yml")
    if not path.exists():
        path = pathlib.Path("app/config/config.yml.example")
    if not path.exists():
        raise FileNotFoundError("Neither app/config/config.yml nor app/config/config.yml.example was found.")
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
        llm_config = _load_llm_yaml().get("llm") or {}
        return llm_config.get("model") or "groq/meta-llama/llama-4-scout-17b-16e-instruct"

    @property
    def llm_temperature(self) -> float:
        llm_config = _load_llm_yaml().get("llm") or {}
        val = llm_config.get("temperature")
        return float(val) if val is not None else 0.5

@lru_cache()
def get_settings():
    """
    Returns a cached instance of the settings.
    LRU Cache ensures the settings are only loaded once.
    """
    return Settings()

