from pydantic import BaseModel
from typing import Optional


# ── Respuesta de un permiso ──
class PermisoResponse(BaseModel):
    ID_Permiso:  int
    Permiso:     str
    Descripcion: Optional[str] = None

    class Config:
        from_attributes = True


# ── Respuesta paginada / lista de permisos ──
class PermisoListResponse(BaseModel):
    total:    int
    permisos: list[PermisoResponse]
