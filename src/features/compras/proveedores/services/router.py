from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import ProveedorCreate, ProveedorUpdate, ProveedorResponse, ProveedorListResponse
from .service import (
    obtener_proveedores, obtener_proveedor, crear_proveedor,
    editar_proveedor, eliminar_proveedor
)

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])


@router.get("/", response_model=ProveedorListResponse)
def listar_proveedores(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_insumos"))
):
    """Lista paginada de proveedores. Busca por responsable, correo o teléfono."""
    return obtener_proveedores(db, pagina, por_pagina, busqueda)


@router.get("/{id_proveedor}", response_model=ProveedorResponse)
def ver_proveedor(
    id_proveedor: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("ver_insumos"))
):
    """Retorna el detalle de un proveedor."""
    return obtener_proveedor(db, id_proveedor)


@router.post("/", response_model=ProveedorResponse, status_code=201)
def agregar_proveedor(
    datos: ProveedorCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_insumos"))
):
    """Crea un nuevo proveedor."""
    return crear_proveedor(db, datos)


@router.put("/{id_proveedor}", response_model=ProveedorResponse)
def actualizar_proveedor(
    id_proveedor: int,
    datos:        ProveedorUpdate,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("editar_insumos"))
):
    """Edita los datos de un proveedor. Solo se actualizan los campos enviados."""
    return editar_proveedor(db, id_proveedor, datos)


@router.delete("/{id_proveedor}")
def borrar_proveedor(
    id_proveedor: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("eliminar_insumos"))
):
    """Elimina un proveedor."""
    return eliminar_proveedor(db, id_proveedor)