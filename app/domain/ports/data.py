from abc import ABC, abstractmethod
from typing import Any

class DataProviderPort(ABC):
    @abstractmethod
    def get_data(self) -> Any:
        pass
