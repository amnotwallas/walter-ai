from fastapi import APIRouter, Security
from app.adapters.data.json_loader import data_provider
from app.core.security import validate_api_key

router = APIRouter()

@router.get("/data", dependencies=[Security(validate_api_key)])
async def get_data():
    """Returns the complete portfolio data from the centralized provider."""
    return data_provider.get_data()
