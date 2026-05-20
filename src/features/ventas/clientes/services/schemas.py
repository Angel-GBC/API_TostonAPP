from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

TIPOS_DOCUMENTO = ["CC", "CE", "NIT", "TI", "PP"]


class ClienteCreate(BaseModel):
    Cedula:               str
    Tipo_Documento:       str
    Nombre:               str
    Apellidos:            str
    Correo:               EmailStr
    Contrasena:           str
    Confirmar_Contrasena: str
    Telefono:             Optional[str]      = None
    Fecha_creacion:       Optional[datetime] = None
    Estado:               Optional[int]      = 1
    Direccion:            Optional[str]      = None
    Departamento:         Optional[str]      = None
    Municipio:            Optional[str]      = None


class ClienteUpdate(BaseModel):
    Cedula:         Optional[str]       = None
    Tipo_Documento: Optional[str]       = None
    Nombre:         Optional[str]       = None
    Apellidos:      Optional[str]       = None
    Correo:         Optional[EmailStr]  = None
    Telefono:       Optional[str]       = None
    Direccion:      Optional[str]       = None
    Departamento:   Optional[str]       = None
    Municipio:      Optional[str]       = None


class ClienteEstado(BaseModel):
    Estado: int


class ClienteResponse(BaseModel):
    ID_Usuario:      int                        # ← PK autoincremental
    Cedula:          Optional[str]      = None  # ← campo normal
    Tipo_Documento:  Optional[str]      = None
    Nombre:          str
    Apellidos:       str
    Correo:          str
    Telefono:        Optional[str]      = None
    Fecha_creacion:  Optional[datetime] = None
    Estado:          Optional[int]      = None
    Direccion:       Optional[str]      = None
    Departamento:    Optional[str]      = None
    Municipio:       Optional[str]      = None
    tiene_foto:      bool               = False

    class Config:
        from_attributes = True


class ClienteListResponse(BaseModel):
    total:      int
    pagina:     int
    por_pagina: int
    clientes:   list[ClienteResponse]