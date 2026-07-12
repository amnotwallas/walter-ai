from fastapi import APIRouter, Depends, HTTPException, Security, status
from pydantic import BaseModel
from app.core.dependencies import get_audit
from app.core.security import validate_api_key

router = APIRouter()


class SlowTool(BaseModel):
    tool: str
    avg_ms: float


class AnomaliesResponse(BaseModel):
    high_failure_tools: list[str]
    slow_sessions: list[str]
    slow_tools: list[SlowTool]


@router.get(
    "/insights",
    response_model=AnomaliesResponse,
    dependencies=[Security(validate_api_key)],
    summary="AIOps anomaly detection",
    description="Returns tools with high error rates, slow sessions, and slowest tools from the audit database.",
)
async def get_insights(
    audit=Depends(get_audit),
):
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit database is not available on this platform.",
        )
    return await audit.get_anomalies()
