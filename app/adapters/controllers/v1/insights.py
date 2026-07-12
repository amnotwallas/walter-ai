from fastapi import APIRouter, Depends, HTTPException, Security, status
from app.core.dependencies import get_audit
from app.core.security import validate_api_key

router = APIRouter()


@router.get("/insights", dependencies=[Security(validate_api_key)])
async def get_insights(
    audit=Depends(get_audit),
):
    """Returns anomaly detection results from the audit database."""
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit database is not available on this platform."
        )
    return await audit.get_anomalies()
