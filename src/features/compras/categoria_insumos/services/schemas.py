from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Crear categoría ──
class CategoriaInsumoCreate(BaseModel):
    Nombre_Categoria: str
    Descripcion:      Optional[str] = None
    Icono:            Optional[str] = None      # URL, ruta o emoji
    insumos_ids:      Optional[list[int]] = []  # IDs de insumos a asociar


# ── Editar categoría ──
class CategoriaInsumoUpdate(BaseModel):
    Nombre_Categoria: Optional[str] = None
    Descripcion:      Optional[str] = None
    Icono:            Optional[str] = None
    insumos_ids:      Optional[list[int]] = None


# ── Cambiar estado ON/OFF ──
class CategoriaInsumoEstado(BaseModel):
    Estado: int


# ── Insumo resumido para mostrar dentro de la categoría ──
class InsumoResumido(BaseModel):
    ID_Insumo: int
    Nombre:    str

    class Config:
        from_attributes = True


# ── Respuesta de una categoría ──
class CategoriaInsumoResponse(BaseModel):
    ID_Categoria:     int
    Nombre_Categoria: str
    Descripcion:      Optional[str] = None
    Icono:            Optional[str] = None
    Estado:           Optional[int] = None
    Fecha_creacion:   Optional[datetime] = None
    insumos:          list[InsumoResumido] = []
    total_insumos:    int = 0

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class CategoriaInsumoListResponse(BaseModel):
    total:      int
    pagina:     int
    por_pagina: int
    categorias: list[CategoriaInsumoResponse]