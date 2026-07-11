import pytest
from app.adapters.data.json_loader import JSONDataLoaderAdapter, data_provider
from app.domain.models.schemas import PortfolioData

def test_json_loader_singleton():
    loader1 = JSONDataLoaderAdapter()
    loader2 = JSONDataLoaderAdapter()
    assert loader1 is loader2
    assert loader1 is data_provider

def test_json_loader_get_data():
    data = data_provider.get_data()
    assert isinstance(data, PortfolioData)
    assert data.basics.name == "Walter Jahir Ambriz Reyna"

def test_json_loader_get_section():
    work_json = data_provider.get_section("work")
    assert "IBICARE" in work_json
    
    invalid_section = data_provider.get_section("invalid_field")
    assert invalid_section == "[]"
