from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import NotificacionResponse, NotificacionesResponse
from .service import obtener_notificaciones, marcar_leida, eliminar_notificacion, limpiar_leidas

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.get("/", response_model=NotificacionesResponse)
def listar_notificaciones(
    db: Session = Depends(get_db),
    _:  dict    = Depends(requiere_permiso("ver_dashboard")),
):
    return obtener_notificaciones(db)


@router.patch("/{id_notificacion}/leer", response_model=NotificacionResponse)
def leer_notificacion(
    id_notificacion: int,
    db: Session = Depends(get_db),
    _:  dict    = Depends(requiere_permiso("ver_dashboard")),
):
    return marcar_leida(db, id_notificacion)


@router.delete("/limpiar")
def limpiar_notificaciones(
    db: Session = Depends(get_db),
    _:  dict    = Depends(requiere_permiso("ver_dashboard")),
):
    return limpiar_leidas(db)


@router.delete("/{id_notificacion}")
def borrar_notificacion(
    id_notificacion: int,
    db: Session = Depends(get_db),
    _:  dict    = Depends(requiere_permiso("ver_dashboard")),
):
    return eliminar_notificacion(db, id_notificacion)
