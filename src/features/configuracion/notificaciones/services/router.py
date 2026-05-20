from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import EliminarNotificacion, NotificacionesResponse
from .service import obtener_notificaciones, eliminar_notificacion, limpiar_todas

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.get("/", response_model=NotificacionesResponse)
def listar_notificaciones(
    db: Session = Depends(get_db),
    _:  dict    = Depends(requiere_permiso("ver_dashboard"))
):
    """Retorna todas las notificaciones activas consultando en tiempo real."""
    return obtener_notificaciones(db)


@router.delete("/limpiar")
def limpiar_notificaciones(
    _: dict = Depends(requiere_permiso("ver_dashboard"))
):
    """Elimina todas las notificaciones de golpe."""
    return limpiar_todas()


@router.delete("/{nid}")
def borrar_notificacion(
    nid: str,
    _:   dict = Depends(requiere_permiso("ver_dashboard"))
):
    """Elimina una notificación por su ID. Formato: tipo_idregistro ej: stock_minimo_3"""
    return eliminar_notificacion(nid)