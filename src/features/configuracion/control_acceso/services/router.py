from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import PermisoResponse, PermisoListResponse
from .service import (
    obtener_permisos, obtener_permiso,
    obtener_permisos_de_rol, asignar_permisos_rol,
)

router = APIRouter(prefix="/control-acceso", tags=["Control de Acceso"])


class AsignarPermisosBody(BaseModel):
    permisos_ids: list[int]


@router.get("/permisos", response_model=PermisoListResponse)
def listar_permisos(
    busqueda: Optional[str] = Query(None),
    db:       Session       = Depends(get_db),
    _:        dict          = Depends(requiere_permiso("ver_roles")),
):
    """Lista todos los permisos disponibles en el sistema."""
    return obtener_permisos(db, busqueda)


@router.get("/permisos/{id_permiso}", response_model=PermisoResponse)
def ver_permiso(
    id_permiso: int,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("ver_roles")),
):
    """Retorna el detalle de un permiso por ID."""
    return obtener_permiso(db, id_permiso)


@router.get("/roles/{id_rol}/permisos")
def ver_permisos_de_rol(
    id_rol: int,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(requiere_permiso("ver_roles")),
):
    """Retorna todos los permisos asignados a un rol específico."""
    return obtener_permisos_de_rol(db, id_rol)


@router.put("/roles/{id_rol}/permisos")
def asignar_permisos(
    id_rol: int,
    datos:  AsignarPermisosBody,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(requiere_permiso("editar_roles")),
):
    """
    Reemplaza todos los permisos de un rol con la lista enviada.
    Lista vacía = quitar todos los permisos.
    """
    return asignar_permisos_rol(db, id_rol, datos.permisos_ids)
