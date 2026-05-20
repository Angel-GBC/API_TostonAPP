from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso, obtener_usuario_actual
from .schemas import (
    DevolucionCreate, DevolucionResolucion, DevolucionUpdate,
    DevolucionResponse, DevolucionListResponse
)
from .service import (
    obtener_devoluciones, obtener_mis_devoluciones, obtener_devolucion,
    crear_devolucion, editar_devolucion, resolver_devolucion
)

router = APIRouter(prefix="/devoluciones", tags=["Devoluciones"])


@router.get("/mis-devoluciones", response_model=DevolucionListResponse)
def mis_devoluciones(
    pagina:     int     = Query(1, ge=1),
    por_pagina: int     = Query(10, ge=1, le=100),
    db:         Session = Depends(get_db),
    actual:     dict    = Depends(obtener_usuario_actual),
):
    """Retorna solo las devoluciones del cliente autenticado."""
    if actual["tipo"] != "usuario":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo disponible para clientes")
    id_usuario = actual["registro"].ID_Usuario
    return obtener_mis_devoluciones(db, id_usuario, pagina, por_pagina)


@router.get("/", response_model=DevolucionListResponse)
def listar_devoluciones(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(20, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    estado:     Optional[int] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_devoluciones"))
):
    """Lista paginada de devoluciones (admin). Filtra por estado y busca por nombre."""
    return obtener_devoluciones(db, pagina, por_pagina, busqueda, estado)


@router.get("/{id_devolucion}", response_model=DevolucionResponse)
def ver_devolucion(
    id_devolucion: int,
    db:            Session = Depends(get_db),
    _:             dict    = Depends(requiere_permiso("ver_devoluciones"))
):
    """Retorna el detalle de una devolución con sus productos."""
    return obtener_devolucion(db, id_devolucion)


@router.post("/", response_model=DevolucionResponse, status_code=201)
def registrar_devolucion(
    datos:  DevolucionCreate,
    db:     Session = Depends(get_db),
    actual: dict    = Depends(obtener_usuario_actual),
):
    """
    Registra una devolución.
    - Clientes: solo pueden devolver sus propias ventas.
    - Empleados/Admin con permiso: pueden registrar para cualquier cliente.
    """
    if actual["tipo"] == "usuario":
        # Validar que el cliente solo devuelva sus propias ventas
        from src.shared.services.models import Venta
        from fastapi import HTTPException as _HTTPException
        venta = db.query(Venta).filter(Venta.ID_Venta == datos.ID_Venta).first()
        if not venta or venta.ID_Usuario != actual["registro"].ID_Usuario:
            raise _HTTPException(
                status_code=403,
                detail="Solo puedes devolver tus propias ventas"
            )
    return crear_devolucion(db, datos)


@router.patch("/{id_devolucion}", response_model=DevolucionResponse)
def editar_dev(
    id_devolucion: int,
    datos:         DevolucionUpdate,
    db:            Session = Depends(get_db),
    _:             dict    = Depends(requiere_permiso("editar_devoluciones"))
):
    """Edita motivo o comentario interno de una devolución pendiente."""
    return editar_devolucion(db, id_devolucion, datos)


@router.patch("/{id_devolucion}/resolver", response_model=DevolucionResponse)
def aprobar_rechazar(
    id_devolucion: int,
    datos:         DevolucionResolucion,
    db:            Session = Depends(get_db),
    _:             dict    = Depends(requiere_permiso("editar_devoluciones"))
):
    """Aprueba o rechaza la devolución. Si se aprueba → recarga crédito automáticamente."""
    return resolver_devolucion(db, id_devolucion, datos)