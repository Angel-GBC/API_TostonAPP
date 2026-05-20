from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Lote de compra opcional al crear insumo ──
class LoteCompraInput(BaseModel):
    ID_Lote_Compra:   Optional[str] = None      # ej: "L-001"
    Fecha_Vencimiento: Optional[datetime] = None
    Cantidad_Inicial:  Optional[int] = None


# ── Crear insumo ──
class InsumoCreate(BaseModel):
    Nombre:        str
    ID_Categoria:  int
    Unidad_Medida: int
    Stock_Actual:  int
    Stock_Minimo:  int
    Lote_Compra:   Optional[LoteCompraInput] = None


# ── Editar insumo ──
class InsumoUpdate(BaseModel):
    Nombre:        Optional[str] = None
    ID_Categoria:  Optional[int] = None
    Unidad_Medida: Optional[int] = None
    Stock_Actual:  Optional[int] = None
    Stock_Minimo:  Optional[int] = None


# ── Cambiar estado ON/OFF ──
class InsumoEstado(BaseModel):
    Estado: int


# ── Respuesta del lote ──
class LoteCompraResponse(BaseModel):
    ID_Lote_Compra:    int
    Fecha_Vencimiento: Optional[datetime] = None
    Cantidad_Inicial:  Optional[int] = None
    Estado:            Optional[int] = None

    class Config:
        from_attributes = True


# ── Respuesta de un insumo ──
class InsumoResponse(BaseModel):
    ID_Insumo:        int
    Nombre:           str
    ID_Categoria:     Optional[int] = None
    nombre_categoria: Optional[str] = None
    Unidad_Medida:    Optional[int] = None
    simbolo_unidad:   Optional[str] = None      # ej: "kg", "l"
    Stock_Actual:     Optional[int] = None
    Stock_Minimo:     Optional[int] = None
    Estado:           Optional[int] = None
    lote:             Optional[LoteCompraResponse] = None

    class Config:
        from_attributes = True


# ── Resumen para las tarjetas del tope de la página ──
class ResumenInsumos(BaseModel):
    total:       int
    disponibles: int     # stock_actual > stock_minimo
    stock_bajo:  int     # stock_actual <= stock_minimo y > 0
    agotados:    int     # stock_actual == 0


# ── Respuesta paginada ──
class InsumoListResponse(BaseModel):
    resumen:    ResumenInsumos
    total:      int
    pagina:     int
    por_pagina: int
    insumos:    list[InsumoResponse]