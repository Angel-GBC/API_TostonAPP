from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any
import smtplib
import random
import uuid
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.shared.services.models import (
    Usuario, Empleado, Rol, UsuarioXRol, Permiso, RolXPermiso,
    VerificacionEmail, CodigoReset,
)

load_dotenv()

SECRET_KEY   = os.getenv("SECRET_KEY")
ALGORITHM    = os.getenv("ALGORITHM", "HS256")
EXPIRE_MIN   = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))
API_URL      = os.getenv("API_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

RESET_TOKEN_EXPIRE_MIN = 10
CODE_EXPIRE_MIN        = 10

# ── Proveedores de email ───────────────────────────────────────────────────────
# Prioridad: Gmail > Resend
# Gmail: crea una cuenta Gmail dedicada + genera "Contraseña de aplicación" en
#        Google Account → Seguridad → Verificación en 2 pasos → Contraseñas de app
GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

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

    if tipo == "usuario" and getattr(registro, "Estado", None) == 2:
        raise HTTPException(
            status_code=403,
            detail="Debes verificar tu correo electrónico antes de iniciar sesión. Revisa tu bandeja de entrada.",
        )

    return registro, tipo


# ─────────────────────────────────────────
# REGISTRO
# ─────────────────────────────────────────

def registrar_cliente(db: Session, datos) -> None:
    """
    Crea un nuevo usuario (cliente) con Estado=2 (inactivo hasta verificar correo)
    y le asigna automáticamente el rol Cliente en Usuario_x_Rol.
    Genera un token UUID de verificación y lo envía por email.
    """
    if buscar_por_correo(db, datos.Correo)[0]:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    rol_cliente = db.query(Rol).filter(Rol.Rol == "Cliente").first()
    if not rol_cliente:
        raise HTTPException(status_code=500, detail="Rol Cliente no encontrado en el sistema")

    nuevo = Usuario(
        Nombre         = datos.Nombre,
        Apellidos      = datos.Apellidos,
        Correo         = datos.Correo,
        Contrasena     = hashear_contrasena(datos.Contrasena),
        Fecha_creacion = datetime.now(),
        Estado         = 2,  # inactivo hasta verificar email
        Cedula         = None,
        Tipo_Documento = None,
        Direccion      = None,
        Municipio      = None,
        Departamento   = None,
        Telefono       = None,
    )
    db.add(nuevo)
    db.flush()

    db.add(UsuarioXRol(
        ID_Rol     = rol_cliente.ID_Rol,
        ID_Usuario = nuevo.ID_Usuario,
    ))

    token = str(uuid.uuid4())
    db.add(VerificacionEmail(
        ID_Usuario = nuevo.ID_Usuario,
        Token      = token,
        Expira_En  = datetime.utcnow() + timedelta(hours=24),
        Usado      = False,
    ))

    try:
        _enviar_email_verificacion(datos.Correo, token, datos.Nombre)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo enviar el correo de verificación: {exc}",
        )

    db.commit()


# ─────────────────────────────────────────
# ENVÍO DE EMAIL (Gmail o Resend)
# ─────────────────────────────────────────

def _email_from() -> str:
    if GMAIL_USER:
        return GMAIL_USER
    return "Brom's <onboarding@resend.dev>"


def _enviar_smtp(msg: MIMEMultipart, correo_destino: str) -> None:
    """Envía un email usando Gmail (preferido) o Resend como fallback."""
    remitente = _email_from()
    msg["From"] = remitente
    msg["To"]   = correo_destino

    if GMAIL_USER and GMAIL_PASSWORD:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.ehlo()
            s.starttls()
            s.login(GMAIL_USER, GMAIL_PASSWORD)
            s.sendmail(GMAIL_USER, correo_destino, msg.as_string())
    elif RESEND_API_KEY:
        with smtplib.SMTP("smtp.resend.com", 587) as s:
            s.starttls()
            s.login("resend", RESEND_API_KEY)
            s.sendmail(remitente, correo_destino, msg.as_string())
    else:
        raise RuntimeError("Sin proveedor de email. Configura GMAIL_USER+GMAIL_APP_PASSWORD o RESEND_API_KEY.")


# ─────────────────────────────────────────
# VERIFICACIÓN DE EMAIL
# ─────────────────────────────────────────

def _enviar_email_verificacion(correo_destino: str, token: str, nombre: str = "") -> None:
    """Envía el enlace de verificación de cuenta."""
    link = f"{API_URL}/api/auth/verificar-email?token={token}"

    msg            = MIMEMultipart("alternative")
    msg["Subject"] = "Verifica tu correo — Brom's"

    saludo = f"Hola <strong>{nombre}</strong>," if nombre else "Hola,"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:20px;">
      <div style="background:linear-gradient(135deg,#2E7D32,#66BB6A);padding:24px;border-radius:14px;text-align:center;margin-bottom:24px;">
        <h1 style="color:white;margin:0;font-size:22px;">Brom's</h1>
        <p style="color:rgba(255,255,255,0.85);margin:4px 0 0;font-size:13px;">Verificacion de correo</p>
      </div>
      <p style="color:#333;">{saludo}</p>
      <p style="color:#555;font-size:14px;">
        Gracias por registrarte. Haz clic en el boton para activar tu cuenta:
      </p>
      <div style="text-align:center;margin:28px 0;">
        <a href="{link}"
           style="background:#2E7D32;color:white;padding:14px 32px;border-radius:10px;
                  text-decoration:none;font-size:15px;font-weight:bold;display:inline-block;">
          Verificar mi correo
        </a>
      </div>
      <p style="color:#999;font-size:12px;">
        El enlace es valido por 24 horas. Si no creaste esta cuenta, ignora este correo.
      </p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))
    _enviar_smtp(msg, correo_destino)


def verificar_email_token(db: Session, token: str) -> str:
    """
    Valida el token UUID de verificación.
    Si es válido → activa el usuario (Estado=1) y marca el token como Usado.
    Retorna la URL del frontend para el redirect.
    """
    verificacion = db.query(VerificacionEmail).filter(VerificacionEmail.Token == token).first()

    if not verificacion:
        raise ValueError("Token de verificación inválido o inexistente.")

    if verificacion.Usado:
        raise ValueError("Este enlace ya fue utilizado.")

    if datetime.utcnow() > verificacion.Expira_En:
        raise ValueError("El enlace de verificación ha expirado. Solicita uno nuevo.")

    usuario = db.query(Usuario).filter(Usuario.ID_Usuario == verificacion.ID_Usuario).first()
    if not usuario:
        raise ValueError("El usuario asociado al token no existe.")

    usuario.Estado       = 1
    verificacion.Usado   = True
    db.commit()

    return f"{FRONTEND_URL}/login?verificado=1"


def reenviar_verificacion(db: Session, correo: str) -> None:
    """
    Invalida tokens anteriores del correo, genera uno nuevo y lo envía.
    No revela si el correo existe o no para evitar enumeración.
    """
    usuario = db.query(Usuario).filter(Usuario.Correo == correo).first()
    if not usuario or usuario.Estado != 2:
        return  # no revelar

    # Invalidar tokens previos
    db.query(VerificacionEmail).filter(
        VerificacionEmail.ID_Usuario == usuario.ID_Usuario,
        VerificacionEmail.Usado      == False,
    ).update({"Usado": True})

    token = str(uuid.uuid4())
    db.add(VerificacionEmail(
        ID_Usuario = usuario.ID_Usuario,
        Token      = token,
        Expira_En  = datetime.utcnow() + timedelta(hours=24),
        Usado      = False,
    ))
    db.commit()

    nombre = usuario.Nombre or ""
    _enviar_email_verificacion(correo, token, nombre)


# ─────────────────────────────────────────
# RECUPERACIÓN DE CONTRASEÑA
# ─────────────────────────────────────────

def _enviar_email_codigo(correo_destino: str, codigo: str, nombre: str = "") -> None:
    """Envía el código de recuperación de contraseña."""
    msg            = MIMEMultipart("alternative")
    msg["Subject"] = "Codigo de recuperacion de contrasena — Brom's"

    saludo = f"Hola <strong>{nombre}</strong>," if nombre else "Hola,"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:20px;">
      <div style="background:linear-gradient(135deg,#2E7D32,#66BB6A);padding:24px;border-radius:14px;text-align:center;margin-bottom:24px;">
        <h1 style="color:white;margin:0;font-size:22px;">Brom's</h1>
        <p style="color:rgba(255,255,255,0.85);margin:4px 0 0;font-size:13px;">Recuperacion de contrasena</p>
      </div>
      <p style="color:#333;">{saludo}</p>
      <p style="color:#555;font-size:14px;">
        Recibimos una solicitud para restablecer tu contrasena.
        Ingresa el siguiente codigo en la aplicacion:
      </p>
      <div style="background:#f5f9f5;border:2px solid #C8E6C9;border-radius:14px;padding:28px;text-align:center;margin:24px 0;">
        <div style="font-size:42px;font-weight:bold;letter-spacing:14px;color:#2E7D32;font-family:monospace;">
          {codigo}
        </div>
        <p style="color:#888;margin:10px 0 0;font-size:12px;">Valido por {CODE_EXPIRE_MIN} minutos</p>
      </div>
      <p style="color:#999;font-size:12px;">
        Si no solicitaste esto, ignora este correo. Tu contrasena no sera modificada.
      </p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))
    _enviar_smtp(msg, correo_destino)


def solicitar_recuperacion(db: Session, correo: str) -> None:
    """
    Genera un código de 6 dígitos, lo guarda en BD con expiración de 10 minutos
    y lo envía al correo. Silencioso si el correo no existe.
    """
    registro, _ = buscar_por_correo(db, correo)
    if not registro:
        return  # no revelar

    # Invalidar códigos anteriores del mismo correo
    db.query(CodigoReset).filter(
        CodigoReset.Correo == correo.lower(),
        CodigoReset.Usado  == False,
    ).update({"Usado": True})

    codigo = str(random.randint(100000, 999999))
    db.add(CodigoReset(
        Correo    = correo.lower(),
        Codigo    = codigo,
        Expira_En = datetime.utcnow() + timedelta(minutes=CODE_EXPIRE_MIN),
        Usado     = False,
    ))
    db.commit()

    nombre = getattr(registro, "Nombre", "") or ""
    _enviar_email_codigo(correo, codigo, nombre)


def verificar_codigo_recuperacion(db: Session, correo: str, codigo: str) -> str:
    """Valida el código desde BD. Si es correcto lo marca como usado y retorna JWT reset."""
    entrada = (
        db.query(CodigoReset)
        .filter(
            CodigoReset.Correo == correo.lower(),
            CodigoReset.Usado  == False,
        )
        .order_by(CodigoReset.Expira_En.desc())
        .first()
    )

    if not entrada:
        raise ValueError("No hay una solicitud activa para este correo. Solicita un nuevo código.")

    if datetime.utcnow() > entrada.Expira_En:
        entrada.Usado = True
        db.commit()
        raise ValueError("El código ha expirado. Solicita uno nuevo.")

    if entrada.Codigo != codigo.strip():
        raise ValueError("Código incorrecto. Verifica e intenta de nuevo.")

    entrada.Usado = True
    db.commit()

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