from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import OrdenCreate, OrdenUpdate, OrdenEstado, OrdenResponse, OrdenListResponse
from .service import (
    obtener_ordenes, obtener_orden, crear_orden,
    editar_orden, cambiar_estado, eliminar_orden
)

router = APIRouter(prefix="/ordenes-produccion", tags=["Órdenes de Producción"])


@router.get("/", response_model=OrdenListResponse)
def listar_ordenes(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_productos"))
):
    """Lista paginada de órdenes. Busca por nombre de producto."""
    return obtener_ordenes(db, pagina, por_pagina, busqueda)


@router.get("/{id_orden}", response_model=OrdenResponse)
def ver_orden(
    id_orden: int,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(requiere_permiso("ver_productos"))
):
    """Retorna el detalle de una orden con producto, insumo y ficha."""
    return obtener_orden(db, id_orden)


@router.post("/", response_model=OrdenResponse, status_code=201)
def agregar_orden(
    datos: OrdenCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_productos"))
):
    """Crea una orden de producción. El costo se calcula automáticamente."""
    return crear_orden(db, datos)


@router.put("/{id_orden}", response_model=OrdenResponse)
def actualizar_orden(
    id_orden: int,
    datos:    OrdenUpdate,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(requiere_permiso("editar_productos"))
):
    """Edita la orden. El costo se recalcula si cambia cantidad o insumo."""
    return editar_orden(db, id_orden, datos)


@router.patch("/{id_orden}/estado", response_model=OrdenResponse)
def actualizar_estado(
    id_orden: int,
    datos:    OrdenEstado,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(requiere_permiso("editar_productos"))
):
    """Cambia el estado de la orden."""
    return cambiar_estado(db, id_orden, datos.Estado)


@router.delete("/{id_orden}")
def borrar_orden(
    id_orden: int,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(requiere_permiso("eliminar_productos"))
):
    """Elimina una orden de producción."""
    return eliminar_orden(db, id_orden)