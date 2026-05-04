import os
import json
from app.core.logger import get_logger

logger = get_logger(__name__)

class DataProvider:
    """
    Centralized provider for loading and caching data from data.json.
    Uses file modification time (mtime) to ensure data freshness without constant reloading.
    """
    _instance = None
    _data = None
    _last_mtime = 0
    _file_path = os.path.join(os.path.dirname(__file__), "../data/data.json")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataProvider, cls).__new__(cls)
        return cls._instance

    def get_data(self) -> dict:
        """
        Returns the data from data.json. Reloads if the file has been modified.
        """
        try:
            if not os.path.exists(self._file_path):
                logger.error(f"Data file not found at: {self._file_path}")
                return {}

            current_mtime = os.path.getmtime(self._file_path)
            if self._data is None or current_mtime > self._last_mtime:
                logger.info(f"Reloading data from {self._file_path} (mtime changed)")
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                self._last_mtime = current_mtime
            
            return self._data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return self._data or {}

data_provider = DataProvider()
