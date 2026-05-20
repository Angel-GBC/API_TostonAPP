from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ── Crear orden ──
class OrdenCreate(BaseModel):
    ID_Producto:  int
    ID_Insumo:    int
    ID_Ficha:     Optional[int] = None
    Cantidad:     int
    Fecha_inicio: datetime
    Fecha_Entrega: datetime


# ── Editar orden ──
class OrdenUpdate(BaseModel):
    ID_Producto:   Optional[int]      = None
    ID_Insumo:     Optional[int]      = None
    ID_Ficha:      Optional[int]      = None
    Cantidad:      Optional[int]      = None
    Fecha_inicio:  Optional[datetime] = None
    Fecha_Entrega: Optional[datetime] = None


# ── Cambiar estado ──
class OrdenEstado(BaseModel):
    Estado: int     # ID del estado en la tabla Estados


# ── Respuesta de una orden ──
class OrdenResponse(BaseModel):
    ID_Orden_Produccion: int
    ID_Producto:         Optional[int]     = None
    nombre_producto:     Optional[str]     = None
    ID_Insumo:           Optional[int]     = None
    nombre_insumo:       Optional[str]     = None
    ID_Ficha:            Optional[int]     = None
    version_ficha:       Optional[str]     = None
    Cantidad:            Optional[int]     = None
    Fecha_inicio:        Optional[datetime] = None
    Fecha_Entrega:       Optional[datetime] = None
    Estado:              Optional[int]     = None
    estado_label:        Optional[str]     = None   # "Pendiente", "Completada", etc.
    Costo:               Optional[Decimal] = None   # calculado automáticamente

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class OrdenListResponse(BaseModel):
    total:      int
    pagina:     int
    por_pagina: int
    ordenes:    list[OrdenResponse]