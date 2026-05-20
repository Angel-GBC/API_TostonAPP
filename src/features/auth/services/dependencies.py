from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from src.shared.services.database import get_db
from src.shared.services.models import Usuario, Empleado, Rol, RolXPermiso, Permiso
from .schemas import TokenData

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = HTTPBearer()


def obtener_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Decodifica el token y retorna el usuario o empleado activo."""
    token = credentials.credentials

    credenciales_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload    = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id_persona = payload.get("id")
        tipo       = payload.get("tipo")

        # Rechazar tokens de reset usados como tokens de sesión
        if payload.get("tipo") == "reset":
            raise credenciales_error

        if id_persona is None or tipo is None:
            raise credenciales_error

        token_data = TokenData(cedula=id_persona, tipo=tipo, rol=payload.get("rol"))

    except JWTError:
        raise credenciales_error

    if tipo == "empleado":
        registro = db.query(Empleado).filter(Empleado.ID_Empleado == id_persona).first()
    else:
        registro = db.query(Usuario).filter(Usuario.ID_Usuario == id_persona).first()

    if registro is None:
        raise credenciales_error

    return {"registro": registro, "tipo": tipo, "rol": token_data.rol}


def solo_empleados(actual: dict = Depends(obtener_usuario_actual)):
    """
    Protege endpoints exclusivos de empleados (cualquier rol de empleado).
    Usar solo donde NO se necesite un permiso específico.
    """
    if actual["tipo"] != "empleado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso"
        )
    return actual


def requiere_permiso(nombre_permiso: str):
    """
    Dependencia factory que verifica si el usuario autenticado
    tiene el permiso requerido según su rol en Rol_x_Permiso.

    Uso en router:
        _ = Depends(requiere_permiso("ver_insumos"))

    Reglas:
    - Empleados: se verifica su ID_Rol contra Rol_x_Permiso + Permisos
    - Usuarios (clientes): se verifica su rol en Usuario_x_Rol contra Rol_x_Permiso
    - Si no tiene el permiso → 403
    """
    def verificar(
        actual: dict    = Depends(obtener_usuario_actual),
        db:     Session = Depends(get_db)
    ):
        registro = actual["registro"]
        tipo     = actual["tipo"]
        
        # Obtener el ID_Rol según el tipo de usuario
        if tipo == "empleado":
            id_rol = registro.ID_Rol
        else:
            # Clientes: buscar su rol en Usuario_x_Rol
            from src.shared.services.models import UsuarioXRol
            uxr = (
                db.query(UsuarioXRol)
                .filter(UsuarioXRol.ID_Usuario == registro.ID_Usuario)
                .first()
            )
            if not uxr:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tu cuenta no tiene un rol asignado"
                )
            id_rol = uxr.ID_Rol

        # Verificar si ese rol tiene el permiso requerido
        tiene_permiso = (
            db.query(RolXPermiso)
            .join(Permiso, Permiso.ID_Permiso == RolXPermiso.ID_Permiso)
            .filter(
                RolXPermiso.ID_Rol == id_rol,
                Permiso.Permiso    == nombre_permiso
            )
            .first()
        )

        if not tiene_permiso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para realizar esta acción"
            )

        return actual

    return verificar