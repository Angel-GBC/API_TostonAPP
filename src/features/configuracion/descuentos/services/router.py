from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import (
    DescuentoCreate, DescuentoUpdate, DescuentoEstado, AsignarDescuento,
    DescuentoResponse, DescuentoListResponse, FiltroCreditos, MovimientoListResponse
)
from .service import (
    obtener_descuentos, obtener_descuento, crear_descuento,
    editar_descuento, cambiar_estado, eliminar_descuento,
    asignar_a_usuarios, ver_asignaciones, obtener_historial_creditos
)

router = APIRouter(prefix="/descuentos", tags=["Descuentos y Créditos"])


# ─────────────────────────────────────────
# DESCUENTOS
# ─────────────────────────────────────────

@router.get("/", response_model=DescuentoListResponse)
def listar_descuentos(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    tipo:       Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_descuentos"))
):
    """Lista todos los descuentos. Filtra por tipo o búsqueda por nombre/código."""
    return obtener_descuentos(db, pagina, por_pagina, busqueda, tipo)


@router.get("/{id_descuento}", response_model=DescuentoResponse)
def ver_descuento(
    id_descuento: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("ver_descuentos"))
):
    """Retorna el detalle de un descuento."""
    return obtener_descuento(db, id_descuento)


@router.post("/", response_model=DescuentoResponse, status_code=201)
def agregar_descuento(
    datos: DescuentoCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_descuentos"))
):
    """Crea un nuevo descuento. cupon requiere Codigo, antiguedad requiere Meses_Minimos."""
    return crear_descuento(db, datos)


@router.put("/{id_descuento}", response_model=DescuentoResponse)
def actualizar_descuento(
    id_descuento: int,
    datos:        DescuentoUpdate,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("editar_descuentos"))
):
    """Edita un descuento. Solo se actualizan los campos enviados."""
    return editar_descuento(db, id_descuento, datos)


@router.patch("/{id_descuento}/estado", response_model=DescuentoResponse)
def toggle_estado(
    id_descuento: int,
    datos:        DescuentoEstado,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("editar_descuentos"))
):
    """Activa o desactiva un descuento."""
    return cambiar_estado(db, id_descuento, datos.Estado)


@router.delete("/{id_descuento}")
def borrar_descuento(
    id_descuento: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("eliminar_descuentos"))
):
    """Elimina un descuento y sus asignaciones."""
    return eliminar_descuento(db, id_descuento)


# ─────────────────────────────────────────
# ASIGNACIONES (solo emision)
# ─────────────────────────────────────────

@router.post("/{id_descuento}/asignar")
def asignar_descuento(
    id_descuento: int,
    datos:        AsignarDescuento,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("editar_descuentos"))
):
    """Asigna masivamente un descuento de emisión a una lista de usuarios."""
    return asignar_a_usuarios(db, id_descuento, datos.usuarios_ids)


@router.get("/{id_descuento}/asignaciones")
def listar_asignaciones(
    id_descuento: int,
    pagina:       int     = Query(1, ge=1),
    por_pagina:   int     = Query(10, ge=1, le=100),
    db:           Session = Depends(get_db),
    _:            dict    = Depends(requiere_permiso("ver_descuentos"))
):
    """Lista los usuarios que tienen asignado este descuento de emisión."""
    return ver_asignaciones(db, id_descuento, pagina, por_pagina)


# ─────────────────────────────────────────
# HISTORIAL DE CREDITOS
# ─────────────────────────────────────────

@router.post("/creditos/historial", response_model=MovimientoListResponse)
def historial_creditos(
    filtros:    FiltroCreditos,
    pagina:     int     = Query(1, ge=1),
    por_pagina: int     = Query(10, ge=1, le=100),
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("ver_descuentos"))
):
    """Retorna el historial de movimientos de crédito de los clientes."""
    return obtener_historial_creditos(db, filtros, pagina, por_pagina)