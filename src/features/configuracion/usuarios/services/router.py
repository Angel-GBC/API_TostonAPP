from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import EmpleadoCreate, UsuarioCreate, PersonaUpdate, PersonaEstado, PersonaResponse, PersonaListResponse
from .service import (
    obtener_todos, obtener_persona, crear_empleado,
    crear_cliente, editar_persona, cambiar_estado, eliminar_persona
)

router = APIRouter(prefix="/usuarios", tags=["Gestión de Usuarios"])


@router.get("/", response_model=PersonaListResponse)
def listar_todos(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_usuarios"))
):
    """Lista paginada de empleados + clientes. Busca por nombre, correo o cédula."""
    return obtener_todos(db, pagina, por_pagina, busqueda)


@router.get("/{tipo}/{id_persona}", response_model=PersonaResponse)
def ver_persona(
    id_persona: int,
    tipo:       str,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("ver_usuarios"))
):
    """Retorna el detalle. tipo puede ser 'empleado' o 'cliente'."""
    return obtener_persona(db, id_persona, tipo)


@router.post("/empleado", response_model=PersonaResponse, status_code=201)
def agregar_empleado(
    datos: EmpleadoCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_usuarios"))
):
    return crear_empleado(db, datos)


@router.post("/cliente", response_model=PersonaResponse, status_code=201)
def agregar_cliente(
    datos: UsuarioCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_usuarios"))
):
    return crear_cliente(db, datos)


@router.put("/{tipo}/{id_persona}", response_model=PersonaResponse)
def actualizar_persona(
    id_persona: int,
    tipo:       str,
    datos:      PersonaUpdate,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("editar_usuarios"))
):
    return editar_persona(db, id_persona, tipo, datos)


@router.patch("/{tipo}/{id_persona}/estado", response_model=PersonaResponse)
def toggle_estado(
    id_persona: int,
    tipo:       str,
    datos:      PersonaEstado,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("editar_usuarios"))
):
    return cambiar_estado(db, id_persona, tipo, datos.Estado)


@router.delete("/{tipo}/{id_persona}")
def borrar_persona(
    id_persona: int,
    tipo:       str,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("eliminar_usuarios"))
):
    return eliminar_persona(db, id_persona, tipo)