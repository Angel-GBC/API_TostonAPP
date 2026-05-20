from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Crear empleado ──
class EmpleadoCreate(BaseModel):
    Cedula:         str             # ya no es PK, es campo normal
    Tipo_Documento: str             # CC, CE, NIT, etc.
    Nombre:         str
    Apellidos:      str
    Correo:         EmailStr
    Contrasena:     str
    Direccion:      Optional[str] = None
    Municipio:      Optional[str] = None
    Departamento:   Optional[str] = None
    Telefono:       Optional[str] = None
    ID_Rol:         int


# ── Crear cliente ──
class UsuarioCreate(BaseModel):
    Cedula:         str
    Tipo_Documento: str
    Nombre:         str
    Apellidos:      str
    Correo:         EmailStr
    Contrasena:     str
    Direccion:      Optional[str] = None
    Municipio:      Optional[str] = None
    Departamento:   Optional[str] = None
    Telefono:       Optional[str] = None


# ── Editar (aplica para ambos) ──
class PersonaUpdate(BaseModel):
    Cedula:         Optional[str]       = None
    Tipo_Documento: Optional[str]       = None
    Nombre:         Optional[str]       = None
    Apellidos:      Optional[str]       = None
    Correo:         Optional[EmailStr]  = None
    Direccion:      Optional[str]       = None
    Municipio:      Optional[str]       = None
    Departamento:   Optional[str]       = None
    Telefono:       Optional[str]       = None
    ID_Rol:         Optional[int]       = None  # solo empleados


# ── Cambiar estado ON/OFF ──
class PersonaEstado(BaseModel):
    Estado: int


# ── Respuesta unificada ──
class PersonaResponse(BaseModel):
    id:             int             # ID_Usuario o ID_Empleado
    Cedula:         Optional[str]   = None
    Tipo_Documento: Optional[str]   = None
    Nombre:         str
    Apellidos:      str
    Correo:         str
    Direccion:      Optional[str]   = None
    Municipio:      Optional[str]   = None
    Departamento:   Optional[str]   = None
    Telefono:       Optional[str]   = None
    ID_Rol:         Optional[int]   = None
    nombre_rol:     Optional[str]   = None
    Estado:         Optional[int]   = None
    Fecha_creacion: Optional[datetime] = None
    tipo:           str             # "empleado" o "cliente"

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class PersonaListResponse(BaseModel):
    total:      int
    pagina:     int
    por_pagina: int
    personas:   list[PersonaResponse]