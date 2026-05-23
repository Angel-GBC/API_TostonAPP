from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any
import smtplib
import random
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.shared.services.models import Usuario, Empleado, Rol, UsuarioXRol, Permiso, RolXPermiso

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

RESET_TOKEN_EXPIRE_MIN = 10
CODE_EXPIRE_MIN        = 10

RESEND_API_KEY  = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM      = "Brom's <onboarding@resend.dev>"

# Almacén en memoria: { correo_lower: { "codigo": "123456", "expires": datetime } }
_codigos_reset: Dict[str, Dict[str, Any]] = {}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────

def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    return pwd_context.verify(contrasena_plana, contrasena_hash)


def hashear_contrasena(contrasena: str) -> str:
    return pwd_context.hash(contrasena)


def crear_token(data: dict) -> str:
    payload = data.copy()
    payload.update({"exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def crear_reset_token(correo: str) -> str:
    payload = {
        "correo": correo,
        "tipo":   "reset",
        "exp":    datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def validar_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise ValueError("Token inválido o expirado")

    if payload.get("tipo") != "reset":
        raise ValueError("El token proporcionado no es un token de recuperación")

    correo = payload.get("correo")
    if not correo:
        raise ValueError("Token malformado")

    return correo


# ─────────────────────────────────────────
# BÚSQUEDA Y AUTENTICACIÓN
# ─────────────────────────────────────────

def buscar_por_correo(db: Session, correo: str):
    """Busca por correo en Empleados primero, luego en Usuarios."""
    empleado = db.query(Empleado).filter(Empleado.Correo == correo).first()
    if empleado:
        return empleado, "empleado"

    usuario = db.query(Usuario).filter(Usuario.Correo == correo).first()
    if usuario:
        return usuario, "usuario"

    return None, None


def obtener_nombre_rol(db: Session, id_rol: int) -> str:
    rol = db.query(Rol).filter(Rol.ID_Rol == id_rol).first()
    return rol.Rol if rol else None


def autenticar(db: Session, correo: str, contrasena: str):
    registro, tipo = buscar_por_correo(db, correo)

    if not registro:
        return None, None

    if not verificar_contrasena(contrasena, registro.Contrasena):
        return None, None

    return registro, tipo


# ─────────────────────────────────────────
# REGISTRO
# ─────────────────────────────────────────

def registrar_cliente(db: Session, datos) -> Usuario:
    """
    Crea un nuevo usuario (cliente) con los datos mínimos
    y le asigna automáticamente el rol Cliente en Usuario_x_Rol.
    Los campos opcionales quedan null hasta que complete su perfil.
    """
    if buscar_por_correo(db, datos.Correo)[0]:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # Verificar que el rol Cliente existe en BD
    rol_cliente = db.query(Rol).filter(Rol.Rol == "Cliente").first()
    if not rol_cliente:
        raise HTTPException(status_code=500, detail="Rol Cliente no encontrado en el sistema")

    # Crear el usuario
    nuevo = Usuario(
        Nombre         = datos.Nombre,
        Apellidos      = datos.Apellidos,
        Correo         = datos.Correo,
        Contrasena     = hashear_contrasena(datos.Contrasena),
        Fecha_creacion = datetime.now(),
        Estado         = 1,
        Cedula         = None,
        Tipo_Documento = None,
        Direccion      = None,
        Municipio      = None,
        Departamento   = None,
        Telefono       = None,
    )
    db.add(nuevo)
    db.flush()  # genera el ID_Usuario sin hacer commit aún

    # Asignar rol Cliente automáticamente
    db.add(UsuarioXRol(
        ID_Rol     = rol_cliente.ID_Rol,
        ID_Usuario = nuevo.ID_Usuario,
    ))

    db.commit()
    db.refresh(nuevo)
    return nuevo


# ─────────────────────────────────────────
# RECUPERACIÓN DE CONTRASEÑA
# ─────────────────────────────────────────

def _enviar_email_codigo(correo_destino: str, codigo: str, nombre: str = "") -> None:
    """Envía el código de verificación vía Resend SMTP relay."""
    msg            = MIMEMultipart("alternative")
    msg["Subject"] = "🔑 Código de recuperación — Brom's"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = correo_destino

    saludo = f"Hola <strong>{nombre}</strong>," if nombre else "Hola,"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:20px;">
      <div style="background:linear-gradient(135deg,#2E7D32,#66BB6A);padding:24px;border-radius:14px;text-align:center;margin-bottom:24px;">
        <h1 style="color:white;margin:0;font-size:22px;">🌿 Brom's</h1>
        <p style="color:rgba(255,255,255,0.85);margin:4px 0 0;font-size:13px;">Recuperación de contraseña</p>
      </div>
      <p style="color:#333;">{saludo}</p>
      <p style="color:#555;font-size:14px;">
        Recibimos una solicitud para restablecer tu contraseña.
        Ingresa el siguiente código en la aplicación:
      </p>
      <div style="background:#f5f9f5;border:2px solid #C8E6C9;border-radius:14px;padding:28px;text-align:center;margin:24px 0;">
        <div style="font-size:42px;font-weight:bold;letter-spacing:14px;color:#2E7D32;font-family:monospace;">
          {codigo}
        </div>
        <p style="color:#888;margin:10px 0 0;font-size:12px;">Válido por {CODE_EXPIRE_MIN} minutos</p>
      </div>
      <p style="color:#999;font-size:12px;">
        Si no solicitaste esto, ignora este correo. Tu contraseña no será modificada.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
      <p style="color:#bbb;font-size:11px;text-align:center;">
        Brom's · Correo automático, no respondas a este mensaje.
      </p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    # Resend SMTP relay: host=smtp.resend.com, user="resend", pass=API_KEY
    with smtplib.SMTP("smtp.resend.com", 587) as server:
        server.starttls()
        server.login("resend", RESEND_API_KEY)
        server.sendmail(EMAIL_FROM, correo_destino, msg.as_string())


def solicitar_recuperacion(db: Session, correo: str) -> None:
    """
    Genera un código de 6 dígitos, lo almacena con expiración de 10 minutos
    y lo envía al correo del usuario.
    Siempre responde igual para no revelar si el correo existe o no.
    """
    registro, _ = buscar_por_correo(db, correo)
    if not registro:
        return  # No revelar que el correo no existe

    codigo = str(random.randint(100000, 999999))
    _codigos_reset[correo.lower()] = {
        "codigo":  codigo,
        "expires": datetime.utcnow() + timedelta(minutes=CODE_EXPIRE_MIN),
    }

    nombre = getattr(registro, "Nombre", "") or ""
    _enviar_email_codigo(correo, codigo, nombre)


def verificar_codigo_recuperacion(db: Session, correo: str, codigo: str) -> str:
    """
    Valida el código. Si es correcto lo elimina (uso único)
    y retorna un JWT de reset de 10 minutos.
    """
    key   = correo.lower()
    entry = _codigos_reset.get(key)

    if not entry:
        raise ValueError("No hay una solicitud activa para este correo. Solicita un nuevo código.")

    if datetime.utcnow() > entry["expires"]:
        _codigos_reset.pop(key, None)
        raise ValueError("El código ha expirado. Solicita uno nuevo.")

    if entry["codigo"] != codigo.strip():
        raise ValueError("Código incorrecto. Verifica e intenta de nuevo.")

    _codigos_reset.pop(key, None)   # consumir el código

    registro, _ = buscar_por_correo(db, correo)
    if not registro:
        raise ValueError("Correo no encontrado.")

    return crear_reset_token(correo)


def resetear_contrasena(db: Session, token: str, nueva_contrasena: str) -> None:
    correo = validar_reset_token(token)

    registro, _ = buscar_por_correo(db, correo)
    if not registro:
        raise ValueError("El correo asociado al token no existe en el sistema")

    registro.Contrasena = hashear_contrasena(nueva_contrasena)
    db.commit()


# ─────────────────────────────────────────
# CAMBIO DE CONTRASEÑA AUTENTICADO
# ─────────────────────────────────────────

def cambiar_contrasena(db: Session, actual: dict, contrasena_actual: str, nueva_contrasena: str) -> None:
    """
    Cambia la contraseña de un usuario o empleado autenticado.
    Valida que la contraseña actual sea correcta antes de actualizar.
    Funciona para tipo 'usuario' y tipo 'empleado'.
    """
    registro = actual["registro"]

    if not verificar_contrasena(contrasena_actual, registro.Contrasena):
        raise ValueError("La contraseña actual es incorrecta")

    registro.Contrasena = hashear_contrasena(nueva_contrasena)
    db.commit()


# ─────────────────────────────────────────
# FOTO DE PERFIL (Cloudinary)
# ─────────────────────────────────────────

def serializar_foto(url: str | None) -> str | None:
    """Retorna la URL de Cloudinary tal cual (ya no hay base64)."""
    return url or None


def actualizar_foto_perfil(db: Session, actual: dict, url: str) -> str:
    """
    Guarda la URL de Cloudinary en Foto_perfil del usuario o empleado.
    El frontend sube la imagen a Cloudinary y envía solo la URL resultante.
    """
    registro = actual["registro"]
    registro.Foto_perfil = url
    db.commit()
    db.refresh(registro)
    return registro.Foto_perfil


def eliminar_foto_perfil(db: Session, actual: dict) -> None:
    """Elimina la foto de perfil poniendo el campo en NULL."""
    registro = actual["registro"]
    registro.Foto_perfil = None
    db.commit()


# ─────────────────────────────────────────
# PERMISOS DEL USUARIO ACTUAL
# ─────────────────────────────────────────

def obtener_mis_permisos(db: Session, actual: dict) -> list[str]:
    """
    Retorna los nombres de permisos del usuario autenticado.
    Admin (ID_Rol=1) recibe todos los permisos existentes sin consultar Rol_x_Permiso.
    """
    registro = actual["registro"]
    tipo     = actual["tipo"]

    if tipo == "empleado":
        id_rol = registro.ID_Rol
        if id_rol == 1:
            return [p.Permiso for p in db.query(Permiso).all()]
    else:
        uxr = db.query(UsuarioXRol).filter(UsuarioXRol.ID_Usuario == registro.ID_Usuario).first()
        if not uxr:
            return []
        id_rol = uxr.ID_Rol

    return [
        p.Permiso
        for p in (
            db.query(Permiso)
            .join(RolXPermiso, RolXPermiso.ID_Permiso == Permiso.ID_Permiso)
            .filter(RolXPermiso.ID_Rol == id_rol)
            .all()
        )
    ]