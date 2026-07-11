import os
import json
import hashlib
from typing import Any, Optional
from app.core.logger import get_logger
from app.domain.ports.data import DataProviderPort
from app.domain.models.schemas import PortfolioData

logger = get_logger(__name__)

ALLOWED_SECTIONS = {"projects", "work", "education", "skills", "basics"}

class JSONDataLoaderAdapter(DataProviderPort):
    """
    Concrete data loader adapter implementing DataProviderPort for JSON files.
    Implements Singleton pattern.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = None
            cls._instance._last_mtime = 0
            cls._instance._last_hash = None
            cls._instance._data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "data"
            )
            cls._instance._file_path = os.path.join(cls._instance._data_dir, "data.json")
        return cls._instance

    def _file_hash(self) -> str:
        """Computes an MD5 hash of the data file."""
        with open(self._file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def load_all(self):
        """Loads and parses the portfolio json data from data.json."""
        try:
            if not os.path.exists(self._file_path):
                logger.error(f"Data file not found at: {self._file_path}")
                return

            current_mtime = os.path.getmtime(self._file_path)
            current_hash = self._file_hash()

            should_reload = (
                self._data is None
                or current_mtime > self._last_mtime
                or current_hash != self._last_hash
            )

            if should_reload:
                logger.info(f"Reloading and validating data from {self._file_path}")
                with open(self._file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                self._data = PortfolioData(**raw_data)
                self._last_mtime = current_mtime
                self._last_hash = current_hash
                logger.info("Portfolio data loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading portfolio data: {e}")
            self._data = None
            self._last_hash = None
            raise e

    def get_data(self) -> Optional[PortfolioData]:
        try:
            self.load_all()
        except Exception as e:
            logger.error(f"Lazy loading of portfolio data failed: {e}")
            return None
        return self._data

    def get_section(self, key: str, default=None) -> str:
        """
        Retrieves a specific section of the portfolio data and returns it as a JSON string.
        """
        if default is None:
            default = []

        if key not in ALLOWED_SECTIONS:
            return json.dumps(default)

        data = self.get_data()
        if not data:
            return json.dumps(default)

        section = getattr(data, key, default)

        if hasattr(section, "model_dump"):
            return json.dumps(section.model_dump(), indent=2)

        if isinstance(section, list):
            if section and hasattr(section[0], "model_dump"):
                return json.dumps([i.model_dump() for i in section], indent=2)
            return json.dumps(section, indent=2)

        return json.dumps(section, indent=2)

# Global singleton instance for backwards compatibility
data_provider = JSONDataLoaderAdapter()
