from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import RolEstado, AsignarPermisos, RolResponse, RolListResponse
from .service import (
    obtener_roles, obtener_rol, crear_rol,
    editar_rol, cambiar_estado, eliminar_rol, asignar_permisos
)

router = APIRouter(prefix="/roles", tags=["Roles y Permisos"])

ESTADO_ACTIVO = 1


# ── Schemas de entrada para los endpoints JSON ──
class RolCreateBody(BaseModel):
    Rol:   str
    Icono: Optional[str] = None   # URL de Cloudinary o emoji


class RolUpdateBody(BaseModel):
    Rol:           Optional[str]  = None
    Icono:         Optional[str]  = None   # URL de Cloudinary o emoji
    limpiar_icono: bool           = False  # True = quitar ícono actual


@router.get("/", response_model=RolListResponse)
def listar_roles(
    busqueda: Optional[str] = Query(None, description="Filtrar por nombre (parcial)"),
    estado:   Optional[int] = Query(None, description="1=Activo, 2=Inactivo"),
    db:       Session       = Depends(get_db),
    _:        dict          = Depends(requiere_permiso("ver_roles")),
):
    """Lista todos los roles. Soporta búsqueda por nombre y filtro por estado."""
    return obtener_roles(db, busqueda=busqueda, estado=estado)


@router.get("/{id_rol}", response_model=RolResponse)
def ver_rol(
    id_rol: int,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(requiere_permiso("ver_roles")),
):
    """Retorna el detalle de un rol con sus permisos."""
    return obtener_rol(db, id_rol)


@router.post("/", response_model=RolResponse, status_code=201)
def agregar_rol(
    datos: RolCreateBody,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_roles")),
):
    """
    Crea un nuevo rol.
    - Nombre: no puede repetirse (ignora mayúsculas y espacios).
    - Ícono: URL de Cloudinary (subida previa desde el frontend) o emoji.
    - Estado inicial: Activo (1).
    """
    return crear_rol(
        db     = db,
        nombre = datos.Rol,
        icono  = datos.Icono,
        estado = ESTADO_ACTIVO,
    )


@router.put("/{id_rol}", response_model=RolResponse)
def actualizar_rol(
    id_rol: int,
    datos:  RolUpdateBody,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(requiere_permiso("editar_roles")),
):
    """
    Edita nombre e ícono de un rol.
    - Admin (ID=1) no se puede editar.
    - limpiar_icono=true elimina el ícono existente sin poner uno nuevo.
    """
    return editar_rol(
        db            = db,
        id_rol        = id_rol,
        nombre        = datos.Rol,
        icono         = datos.Icono,
        limpiar_icono = datos.limpiar_icono,
    )


@router.patch("/{id_rol}/estado", response_model=RolResponse)
def toggle_estado(
    id_rol: int,
    datos:  RolEstado,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(requiere_permiso("editar_roles")),
):
    """
    Cambia el estado de un rol (1=Activo / 2=Inactivo).
    Al desactivar: desactiva todos los empleados y usuarios con ese rol.
    Al activar: reactiva todos los empleados y usuarios con ese rol.
    Admin no puede modificarse.
    """
    return cambiar_estado(db, id_rol, datos.Estado)


@router.delete("/{id_rol}")
def borrar_rol(
    id_rol: int,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(requiere_permiso("eliminar_roles")),
):
    """
    Elimina un rol.
    - Admin nunca se puede eliminar.
    - Si tiene usuarios asociados retorna error 400.
    - La confirmación de "¿está seguro?" la maneja el frontend.
    """
    return eliminar_rol(db, id_rol)


@router.put("/{id_rol}/permisos", response_model=RolResponse)
def gestionar_permisos(
    id_rol: int,
    datos:  AsignarPermisos,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(requiere_permiso("editar_roles")),
):
    """Reemplaza los permisos del rol con la lista enviada. Lista vacía = sin permisos."""
    return asignar_permisos(db, id_rol, datos.permisos_ids)