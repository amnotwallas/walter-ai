import os
from fastapi import APIRouter, Security, HTTPException
from fastapi.responses import FileResponse
from app.core.security import validate_api_key

router = APIRouter()

PROJECTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/projects"))

@router.get("/{project_name}/{image_name}", dependencies=[Security(validate_api_key)])
async def get_project_image(project_name: str, image_name: str):
    """
    Serves project images securely.
    Requires X-API-KEY header.
    """
    file_path = os.path.join(PROJECTS_DIR, project_name, image_name)
    
    if not os.path.abspath(file_path).startswith(PROJECTS_DIR):
        raise HTTPException(status_code=400, detail="INVALID_PATH")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="IMAGE_NOT_FOUND")

    return FileResponse(file_path)
