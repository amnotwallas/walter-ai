from fastapi import APIRouter, Depends, Security
from app.tools.cv_tools import _load_data_sync
from app.core.security import validate_api_key

router = APIRouter()

@router.get("/data", dependencies=[Security(validate_api_key)])
async def get_data():
    return _load_data_sync()
