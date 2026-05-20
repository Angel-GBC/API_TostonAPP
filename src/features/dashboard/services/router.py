from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import solo_empleados
from .schemas import DashboardResponse
from .service import obtener_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardResponse)
def vista_general(
    periodo: str     = Query("hoy", description="hoy | semana | mes"),
    db:      Session = Depends(get_db),
    _:       dict    = Depends(solo_empleados)
):
    """
    Retorna toda la información del dashboard en una sola llamada.

    Incluye:
    - Resumen general (4 tarjetas con variación vs período anterior)
    - Gráfica de ventas en el tiempo (barras/líneas)
    - Top 5 productos más vendidos (torta + ranking)

    Períodos disponibles: hoy | semana | mes
    """
    return obtener_dashboard(db, periodo)