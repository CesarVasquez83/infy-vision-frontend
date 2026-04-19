from fastapi import APIRouter
from app.core.config import SERVICE_NAME
from app.services.kpi_service import KPIService

router = APIRouter()
kpi_service = KPIService()

@router.get("/health", tags=["health"])
def health():
    df = kpi_service.get_df()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "kpis_cargados": len(df),
    }