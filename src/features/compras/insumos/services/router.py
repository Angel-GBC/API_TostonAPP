from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import InsumoCreate, InsumoUpdate, InsumoEstado, InsumoResponse, InsumoListResponse
from .service import (
    obtener_insumos, obtener_insumo, crear_insumo,
    editar_insumo, cambiar_estado, eliminar_insumo
)

router = APIRouter(prefix="/insumos", tags=["Gestión de Insumos"])


@router.get("/", response_model=InsumoListResponse)
def listar_insumos(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_insumos"))
):
    """Lista paginada de insumos con resumen de tarjetas. Busca por nombre o categoría."""
    return obtener_insumos(db, pagina, por_pagina, busqueda)


@router.get("/{id_insumo}", response_model=InsumoResponse)
def ver_insumo(
    id_insumo: int,
    db:        Session = Depends(get_db),
    _:         dict    = Depends(requiere_permiso("ver_insumos"))
):
    """Retorna el detalle de un insumo con su lote y unidad de medida."""
    return obtener_insumo(db, id_insumo)


@router.post("/", response_model=InsumoResponse, status_code=201)
def agregar_insumo(
    datos: InsumoCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_insumos"))
):
    """Crea un insumo. Si se envía lote_compra, también crea el lote y lo asocia automáticamente."""
    return crear_insumo(db, datos)


@router.put("/{id_insumo}", response_model=InsumoResponse)
def actualizar_insumo(
    id_insumo: int,
    datos:     InsumoUpdate,
    db:        Session = Depends(get_db),
    _:         dict    = Depends(requiere_permiso("editar_insumos"))
):
    """Edita los datos del insumo. Solo se actualizan los campos enviados."""
    return editar_insumo(db, id_insumo, datos)


@router.patch("/{id_insumo}/estado", response_model=InsumoResponse)
def toggle_estado(
    id_insumo: int,
    datos:     InsumoEstado,
    db:        Session = Depends(get_db),
    _:         dict    = Depends(requiere_permiso("editar_insumos"))
):
    """Cambia el estado ON/OFF del insumo."""
    return cambiar_estado(db, id_insumo, datos.Estado)


@router.delete("/{id_insumo}")
def borrar_insumo(
    id_insumo: int,
    db:        Session = Depends(get_db),
    _:         dict    = Depends(requiere_permiso("eliminar_insumos"))
):
    """Elimina un insumo y su lote asociado si existe."""
    return eliminar_insumo(db, id_insumo)