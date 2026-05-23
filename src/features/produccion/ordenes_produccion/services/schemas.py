from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


# ── Crear orden ──
class OrdenCreate(BaseModel):
    ID_Producto:  int
    ID_Insumo:    int
    ID_Ficha:     Optional[int] = None
    Cantidad:     int
    Fecha_inicio: datetime
    Fecha_Entrega: datetime

    @model_validator(mode="after")
    def validar_fechas(self):
        hoy = date.today()
        if self.Fecha_inicio.date() < hoy:
            raise ValueError("La Fecha_inicio no puede ser anterior a hoy")
        if self.Fecha_Entrega < self.Fecha_inicio:
            raise ValueError("La Fecha_Entrega no puede ser anterior a la Fecha_inicio")
        return self


# ── Editar orden ──
class OrdenUpdate(BaseModel):
    ID_Producto:   Optional[int]      = None
    ID_Insumo:     Optional[int]      = None
    ID_Ficha:      Optional[int]      = None
    Cantidad:      Optional[int]      = None
    Fecha_inicio:  Optional[datetime] = None
    Fecha_Entrega: Optional[datetime] = None

    @model_validator(mode="after")
    def validar_fechas_update(self):
        hoy = date.today()
        if self.Fecha_inicio is not None and self.Fecha_inicio.date() < hoy:
            raise ValueError("La Fecha_inicio no puede ser anterior a hoy")
        if self.Fecha_inicio is not None and self.Fecha_Entrega is not None:
            if self.Fecha_Entrega < self.Fecha_inicio:
                raise ValueError("La Fecha_Entrega no puede ser anterior a la Fecha_inicio")
        return self


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