import os
import json
import hashlib
from typing import Optional
from app.core.logger import get_logger
from app.domain.models.schemas import PortfolioData

logger = get_logger(__name__)

ALLOWED_SECTIONS = {"projects", "work", "education", "skills", "basics"}


class DataProvider:
    """
    Singleton data provider responsible for loading, validating, and caching portfolio data.

    Key responsibilities:
    - Load data from a JSON file.
    - Validate structure using Pydantic (PortfolioData).
    - Cache the parsed object in memory.
    - Reload data only when the file changes (based on mtime + content hash).
    - Provide safe access to specific sections of the data.

    Design notes:
    - Uses both file modification time and content hash to detect real changes.
    - Returns None if data cannot be loaded or validated (fail-fast approach).
    - Prevents arbitrary attribute access via an explicit whitelist (ALLOWED_SECTIONS).
    """

    _instance = None
    _data = None
    _last_mtime = 0
    _last_hash = None
    _file_path = os.path.join(os.path.dirname(__file__), "../data/data.json")

    def __new__(cls):
        """
        Ensures a single shared instance (Singleton pattern).

        This avoids reloading or revalidating data multiple times across the app.
        """
        if cls._instance is None:
            cls._instance = super(DataProvider, cls).__new__(cls)
        return cls._instance

    def _file_hash(self) -> str:
        """
        Computes an MD5 hash of the data file.

        Used to detect actual content changes, not just timestamp changes.

        Returns:
            str: Hex digest of the file content.
        """
        with open(self._file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def get_data(self) -> Optional[PortfolioData]:
        """
        Loads and returns the validated portfolio data.

        Reloads the file only if:
        - No data is cached yet, OR
        - File modification time changed, OR
        - File content hash changed

        Returns:
            Optional[PortfolioData]:
                - PortfolioData instance if successful
                - None if file is missing or validation fails

        Behavior on failure:
        - Logs the error
        - Clears cached data to avoid serving corrupted state
        """
        try:
            if not os.path.exists(self._file_path):
                logger.error(f"Data file not found at: {self._file_path}")
                return None

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

                logger.info("Data validation successful.")

            return self._data

        except Exception as e:
            logger.error(f"DATA_VALIDATION_ERROR: {e}")
            self._data = None
            self._last_hash = None
            return None

    def get_section(self, key: str, default=None) -> str:
        """
        Retrieves a specific section of the portfolio data and returns it as a JSON string.

        Access is restricted to predefined sections (ALLOWED_SECTIONS) to prevent
        unintended exposure of internal attributes.

        Args:
            key (str): Section name to retrieve (e.g., "projects", "work").
            default (any, optional): Fallback value if section is missing or data is unavailable.
                                     Defaults to an empty list.

        Returns:
            str: JSON-formatted string of the requested section.

        Behavior:
        - Returns default if:
            - Section is not allowed
            - Data is unavailable
        - Automatically serializes:
            - Pydantic models via `.model_dump()`
            - Lists of models
            - Primitive types
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


data_provider = DataProvider()