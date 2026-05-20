from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import (
    CategoriaInsumoCreate, CategoriaInsumoUpdate, CategoriaInsumoEstado,
    CategoriaInsumoResponse, CategoriaInsumoListResponse
)
from .service import (
    obtener_categorias, obtener_categoria, crear_categoria,
    editar_categoria, cambiar_estado, eliminar_categoria
)

router = APIRouter(prefix="/categoria-insumos", tags=["Categorías de Insumos"])


@router.get("/", response_model=CategoriaInsumoListResponse)
def listar_categorias(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_insumos"))
):
    """Lista paginada de categorías con sus insumos."""
    return obtener_categorias(db, pagina, por_pagina, busqueda)


@router.get("/{id_categoria}", response_model=CategoriaInsumoResponse)
def ver_categoria(
    id_categoria: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("ver_insumos"))
):
    """Retorna el detalle de una categoría con todos sus insumos."""
    return obtener_categoria(db, id_categoria)


@router.post("/", response_model=CategoriaInsumoResponse, status_code=201)
def agregar_categoria(
    datos: CategoriaInsumoCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_insumos"))
):
    """Crea una categoría y opcionalmente asocia insumos existentes."""
    return crear_categoria(db, datos)


@router.put("/{id_categoria}", response_model=CategoriaInsumoResponse)
def actualizar_categoria(
    id_categoria: int,
    datos:        CategoriaInsumoUpdate,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("editar_insumos"))
):
    """Edita la categoría. Si se envía insumos_ids reemplaza la lista completa."""
    return editar_categoria(db, id_categoria, datos)


@router.patch("/{id_categoria}/estado", response_model=CategoriaInsumoResponse)
def toggle_estado(
    id_categoria: int,
    datos:        CategoriaInsumoEstado,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("editar_insumos"))
):
    """Cambia el estado ON/OFF de la categoría."""
    return cambiar_estado(db, id_categoria, datos.Estado)


@router.delete("/{id_categoria}")
def borrar_categoria(
    id_categoria: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("eliminar_insumos"))
):
    """Elimina la categoría. Los insumos asociados quedan sin categoría pero no se eliminan."""
    return eliminar_categoria(db, id_categoria)