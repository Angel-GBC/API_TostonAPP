from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import (
    CategoriaProductoCreate, CategoriaProductoUpdate, CategoriaProductoEstado,
    CategoriaProductoResponse, CategoriaProductoListResponse
)
from .service import (
    obtener_categorias, obtener_categoria, crear_categoria,
    editar_categoria, cambiar_estado, eliminar_categoria
)

router = APIRouter(prefix="/categoria-productos", tags=["Categorías de Productos"])


@router.get("/", response_model=CategoriaProductoListResponse)
def listar_categorias(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_productos"))
):
    """Lista paginada de categorías con sus productos."""
    return obtener_categorias(db, pagina, por_pagina, busqueda)


@router.get("/{id_categoria}", response_model=CategoriaProductoResponse)
def ver_categoria(
    id_categoria: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("ver_productos"))
):
    """Retorna el detalle de una categoría con todos sus productos."""
    return obtener_categoria(db, id_categoria)


@router.post("/", response_model=CategoriaProductoResponse, status_code=201)
def agregar_categoria(
    datos: CategoriaProductoCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_productos"))
):
    """Crea una nueva categoría de productos."""
    return crear_categoria(db, datos)


@router.put("/{id_categoria}", response_model=CategoriaProductoResponse)
def actualizar_categoria(
    id_categoria: int,
    datos:        CategoriaProductoUpdate,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("editar_productos"))
):
    """Edita la categoría. Solo se actualizan los campos enviados."""
    return editar_categoria(db, id_categoria, datos)


@router.patch("/{id_categoria}/estado", response_model=CategoriaProductoResponse)
def toggle_estado(
    id_categoria: int,
    datos:        CategoriaProductoEstado,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("editar_productos"))
):
    """Cambia el estado ON/OFF de la categoría."""
    return cambiar_estado(db, id_categoria, datos.Estado)


@router.delete("/{id_categoria}")
def borrar_categoria(
    id_categoria: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("eliminar_productos"))
):
    """Elimina la categoría. Los productos asociados quedan sin categoría pero no se eliminan."""
    return eliminar_categoria(db, id_categoria)