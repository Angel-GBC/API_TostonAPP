from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso, obtener_usuario_actual
from .schemas import ProductoCreate, ProductoUpdate, ProductoResponse, ProductoListResponse
from .service import (
    obtener_productos, obtener_producto, crear_producto,
    editar_producto, agregar_imagenes, eliminar_imagen, eliminar_producto
)

router = APIRouter(prefix="/productos", tags=["Gesti\u00f3n de Productos"])


@router.get("/publico", response_model=ProductoListResponse)
def listar_productos_publico(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
):
    """Lista paginada de productos. P\u00daBLICO - Sin autenticaci\u00f3n requerida."""
    return obtener_productos(db, pagina, por_pagina, busqueda)


@router.get("/", response_model=ProductoListResponse)
def listar_productos(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(obtener_usuario_actual),
):
    """Lista paginada de productos. Accesible para cualquier usuario autenticado."""
    return obtener_productos(db, pagina, por_pagina, busqueda)


@router.get("/{id_producto}", response_model=ProductoResponse)
def ver_producto(
    id_producto: int,
    db:          Session = Depends(get_db),
    _:           dict    = Depends(obtener_usuario_actual),
):
    """Retorna el detalle de un producto. Accesible para cualquier usuario autenticado."""
    return obtener_producto(db, id_producto)


@router.post("/", response_model=ProductoResponse, status_code=201)
def agregar_producto(
    datos: ProductoCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_productos"))
):
    """Crea un producto. El estado se calcula autom\u00e1ticamente seg\u00fan stock."""
    return crear_producto(db, datos)


@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(
    id_producto: int,
    datos:       ProductoUpdate,
    db:          Session = Depends(get_db),
    _:           dict    = Depends(requiere_permiso("editar_productos"))
):
    """Edita el producto. El estado se recalcula autom\u00e1ticamente."""
    return editar_producto(db, id_producto, datos)


@router.post("/{id_producto}/imagenes", response_model=ProductoResponse)
def subir_imagenes(
    id_producto: int,
    imagenes:    list[UploadFile] = File(...),
    db:          Session          = Depends(get_db),
    _:           dict             = Depends(requiere_permiso("editar_productos"))
):
    """Sube una o varias im\u00e1genes al producto (multipart/form-data)."""
    return agregar_imagenes(db, id_producto, imagenes)


@router.delete("/{id_producto}/imagenes/{id_imagen}")
def borrar_imagen(
    id_producto: int,
    id_imagen:   int,
    db:          Session = Depends(get_db),
    _:           dict    = Depends(requiere_permiso("editar_productos"))
):
    """Elimina una imagen espec\u00edfica del producto."""
    return eliminar_imagen(db, id_imagen)


@router.delete("/{id_producto}")
def borrar_producto(
    id_producto: int,
    db:          Session = Depends(get_db),
    _:           dict    = Depends(requiere_permiso("eliminar_productos"))
):
    """Elimina el producto junto con sus im\u00e1genes y ficha t\u00e9cnica."""
    return eliminar_producto(db, id_producto)
