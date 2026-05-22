from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import SalidaCreate, SalidaResponse, SalidaListResponse
from .service import obtener_salidas, obtener_salida, crear_salida, anular_salida

router = APIRouter(prefix="/salidas", tags=["Salidas"])


@router.get("/", response_model=SalidaListResponse)
def listar_salidas(
    pagina:      int             = Query(1, ge=1),
    por_pagina:  int             = Query(10, ge=1, le=100),
    busqueda:    Optional[str]   = Query(None),
    tipo:        Optional[str]   = Query(None),
    estado:      Optional[int]   = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    id_insumo:   Optional[int]   = Query(None),
    id_producto: Optional[int]   = Query(None),
    db:          Session         = Depends(get_db),
    _:           dict            = Depends(requiere_permiso("ver_salidas")),
):
    return obtener_salidas(
        db, pagina, por_pagina, busqueda,
        tipo, estado, fecha_desde, fecha_hasta,
        id_insumo, id_producto,
    )


@router.get("/{id_salida}", response_model=SalidaResponse)
def ver_salida(
    id_salida: int,
    db:        Session = Depends(get_db),
    _:         dict    = Depends(requiere_permiso("ver_salidas")),
):
    return obtener_salida(db, id_salida)


@router.post("/", response_model=SalidaResponse, status_code=201)
def registrar_salida(
    datos: SalidaCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_salidas")),
):
    return crear_salida(db, datos)


@router.patch("/{id_salida}/anular", response_model=SalidaResponse)
def anular(
    id_salida: int,
    db:        Session = Depends(get_db),
    _:         dict    = Depends(requiere_permiso("eliminar_salidas")),
):
    return anular_salida(db, id_salida)
