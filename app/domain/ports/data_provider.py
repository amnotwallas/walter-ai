from typing import Protocol, Optional
from app.domain.models.schemas import PortfolioData

class DataProviderPort(Protocol):
    """
    Port interface for loading and querying portfolio data.
    """
    def get_data(self) -> Optional[PortfolioData]:
        ...

    def get_section(self, key: str, default=None) -> str:
        ...
