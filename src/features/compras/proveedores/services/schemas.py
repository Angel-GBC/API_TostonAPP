from pydantic import BaseModel, EmailStr
from typing import Optional


# ── Crear proveedor ──
class ProveedorCreate(BaseModel):
    Sujeto_Derecho: int             # ID de la tabla Sujeto_Derecho
    Responsable:    str
    Direccion:      Optional[str] = None
    Municipio:      Optional[str] = None
    Departamento:   Optional[str] = None
    Telefono:       Optional[str] = None
    Correo:         Optional[EmailStr] = None


# ── Editar proveedor ──
class ProveedorUpdate(BaseModel):
    Sujeto_Derecho: Optional[int] = None
    Responsable:    Optional[str] = None
    Direccion:      Optional[str] = None
    Municipio:      Optional[str] = None
    Departamento:   Optional[str] = None
    Telefono:       Optional[str] = None
    Correo:         Optional[EmailStr] = None


# ── Respuesta de un proveedor ──
class ProveedorResponse(BaseModel):
    ID_Proveedor:       int
    Sujeto_Derecho:     Optional[int] = None
    nombre_sujeto:      Optional[str] = None    # nombre legible del sujeto de derecho
    Responsable:        str
    Direccion:          Optional[str] = None
    Municipio:          Optional[str] = None
    Departamento:       Optional[str] = None
    Telefono:           Optional[str] = None
    Correo:             Optional[str] = None

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class ProveedorListResponse(BaseModel):
    total:       int
    pagina:      int
    por_pagina:  int
    proveedores: list[ProveedorResponse]