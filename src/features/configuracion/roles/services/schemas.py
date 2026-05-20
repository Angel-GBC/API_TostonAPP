from pydantic import BaseModel
from typing import Optional


# ── IDs de roles protegidos (nunca se editan ni eliminan) ──
ROLES_PROTEGIDOS = [1]  # Admin


# ── Respuesta de un permiso ──
class PermisoResponse(BaseModel):
    ID_Permiso:  int
    Permiso:     str
    Descripcion: Optional[str] = None

    class Config:
        from_attributes = True


# ── Respuesta de un rol ──
class RolResponse(BaseModel):
    ID_Rol:          int
    Rol:             str
    Icono:           Optional[str] = None   # base64 string o None
    Estado:          Optional[int] = None
    total_usuarios:  int = 0
    protegido:       bool = False
    permisos:        list[PermisoResponse] = []

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class RolListResponse(BaseModel):
    total: int
    roles: list[RolResponse]


# ── Cambiar estado ON/OFF ──
class RolEstado(BaseModel):
    Estado: int


# ── Asignar/quitar permisos a un rol ──
class AsignarPermisos(BaseModel):
    permisos_ids: list[int]


# ── Update parcial (usado internamente, el router usa Form) ──
class RolUpdate(BaseModel):
    Rol:   Optional[str] = None
    Icono: Optional[str] = None