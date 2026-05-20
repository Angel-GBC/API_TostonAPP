from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Crear categoría ──
class CategoriaProductoCreate(BaseModel):
    Nombre_Categoria: str
    Descripcion:      str
    Icono:            Optional[str] = None      # URL, ruta o emoji


# ── Editar categoría ──
class CategoriaProductoUpdate(BaseModel):
    Nombre_Categoria: Optional[str] = None
    Descripcion:      Optional[str] = None
    Icono:            Optional[str] = None


# ── Cambiar estado ON/OFF ──
class CategoriaProductoEstado(BaseModel):
    Estado: int


# ── Producto resumido para mostrar dentro de la categoría ──
class ProductoResumido(BaseModel):
    ID_Producto: int
    nombre:      str

    class Config:
        from_attributes = True


# ── Respuesta de una categoría ──
class CategoriaProductoResponse(BaseModel):
    ID_Categoria:     int
    Nombre_Categoria: str
    Descripcion:      Optional[str] = None
    Icono:            Optional[str] = None
    Estado:           Optional[int] = None
    Fecha_Creacion:   Optional[datetime] = None
    productos:        list[ProductoResumido] = []
    total_productos:  int = 0

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class CategoriaProductoListResponse(BaseModel):
    total:      int
    pagina:     int
    por_pagina: int
    categorias: list[CategoriaProductoResponse]