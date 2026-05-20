from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ── Ficha técnica opcional al crear producto ──
class FichaTecnicaInput(BaseModel):
    Version:       Optional[str] = None
    Observaciones: Optional[str] = None
    Procedimiento: Optional[str] = None


# ── Crear producto ──
class ProductoCreate(BaseModel):
    nombre:         str
    ID_Categoria:   int
    Precio_venta:   Decimal
    Stock:          int
    Stock_Minimo:   int                             # para calcular estado automático
    ficha_tecnica:  Optional[FichaTecnicaInput] = None


# ── Editar producto ──
class ProductoUpdate(BaseModel):
    nombre:        Optional[str]     = None
    ID_Categoria:  Optional[int]     = None
    Precio_venta:  Optional[Decimal] = None
    Stock:         Optional[int]     = None
    Stock_Minimo:  Optional[int]     = None


# ── Respuesta de imagen ──
class ImagenResponse(BaseModel):
    ID_Producto_Img: int
    url:             Optional[str] = None   # ruta para acceder a la imagen

    class Config:
        from_attributes = True


# ── Respuesta de ficha técnica resumida ──
class FichaTecnicaResumida(BaseModel):
    ID_Ficha:      int
    Version:       Optional[str] = None
    Observaciones: Optional[str] = None
    Procedimiento: Optional[str] = None
    Estado:        Optional[int] = None
    Fecha_Creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Respuesta de un producto ──
class ProductoResponse(BaseModel):
    ID_Producto:      int
    nombre:           str
    ID_Categoria:     Optional[int]     = None
    nombre_categoria: Optional[str]     = None
    Precio_venta:     Optional[Decimal] = None
    Stock:            Optional[int]     = None
    Stock_Minimo:     Optional[int]     = None
    Estado:           Optional[int]     = None
    estado_label:     Optional[str]     = None  # "Disponible" o "No disponible"
    imagenes:         list[ImagenResponse] = []
    ficha_tecnica:    Optional[FichaTecnicaResumida] = None

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class ProductoListResponse(BaseModel):
    total:      int
    pagina:     int
    por_pagina: int
    productos:  list[ProductoResponse]