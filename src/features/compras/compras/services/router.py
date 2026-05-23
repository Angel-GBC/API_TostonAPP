from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import CompraCreate, CompraResponse, CompraListResponse
from .service import obtener_compras, obtener_compra, crear_compra

router = APIRouter(prefix="/compras", tags=["Compras"])


@router.get("/", response_model=CompraListResponse)
def listar_compras(
    pagina:       int           = Query(1, ge=1),
    por_pagina:   int           = Query(10, ge=1, le=100),
    busqueda:     Optional[str] = Query(None),
    id_proveedor: Optional[int] = Query(None),
    db:           Session       = Depends(get_db),
    _:            dict          = Depends(requiere_permiso("ver_insumos")),
):
    """Lista paginada de compras. Filtra por proveedor o busca por método de pago."""
    return obtener_compras(db, pagina, por_pagina, busqueda, id_proveedor)


@router.get("/{id_compra}", response_model=CompraResponse)
def ver_compra(
    id_compra: int,
    db:        Session = Depends(get_db),
    _:         dict    = Depends(requiere_permiso("ver_insumos")),
):
    """Retorna el detalle completo de una compra con sus ítems."""
    return obtener_compra(db, id_compra)


@router.post("/", response_model=CompraResponse, status_code=201)
def registrar_compra(
    datos: CompraCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_insumos")),
):
    """
    Registra una compra completa con sus detalles.
    Por cada ítem: crea un LoteCompra y actualiza el Stock_Actual del insumo.
    El total se calcula automáticamente sumando (precio_und * cantidad) de cada ítem.
    """
    return crear_compra(db, datos)
