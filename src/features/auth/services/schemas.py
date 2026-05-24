from pydantic import BaseModel, model_validator
from typing import Optional
from pydantic import Field


# ── Login ──
class LoginInput(BaseModel):
    correo:     str = Field(example="admin@empresa.com")
    contrasena: str = Field(example="Admin123@")


# ── Token interno ──
class TokenData(BaseModel):
    cedula: Optional[int] = None
    tipo:   Optional[str] = None
    rol:    Optional[str] = None


# ── Respuesta de login / registro ──
class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    tipo:         str
    cedula:       int
    nombre:       str
    apellidos:    str
    rol:          Optional[str] = None


# ── Registro nuevo cliente ──
class RegistroInput(BaseModel):
    Nombre:               str = Field(example="Ana")
    Apellidos:            str = Field(example="García")
    Correo:               str = Field(example="ana@gmail.com")
    Contrasena:           str = Field(example="MiClave123@")
    Confirmar_contrasena: str = Field(example="MiClave123@")

    @model_validator(mode="after")
    def validar_contrasenas(self):
        if len(self.Contrasena) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if self.Contrasena != self.Confirmar_contrasena:
            raise ValueError("Las contraseñas no coinciden")
        return self


# ── Recuperación de contraseña ──
class RecuperarContrasenaInput(BaseModel):
    correo: str = Field(example="admin@empresa.com")


class RecuperarContrasenaResponse(BaseModel):
    mensaje: str   # NO reset_token — el código va al correo del usuario


# ── Verificar código de 6 dígitos ──
class VerificarCodigoInput(BaseModel):
    correo: str = Field(example="usuario@gmail.com")
    codigo: str = Field(example="482931")


class VerificarCodigoResponse(BaseModel):
    reset_token: str
    mensaje:     str


# ── Resetear contraseña ──
class ResetearContrasenaInput(BaseModel):
    token:            str = Field(example="eyJhbGci...")
    nueva_contrasena: str = Field(example="NuevaClave123@")

    @model_validator(mode="after")
    def validar_contrasena(self):
        if len(self.nueva_contrasena) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return self


class ResetearContrasenaResponse(BaseModel):
    mensaje: str


# ── Cambio de contraseña (usuario autenticado) ──
class CambiarContrasenaInput(BaseModel):
    contrasena_actual:    str = Field(example="MiClave123@")
    nueva_contrasena:     str = Field(example="NuevaClave456@")
    confirmar_contrasena: str = Field(example="NuevaClave456@")

    @model_validator(mode="after")
    def validar_contrasenas(self):
        if len(self.nueva_contrasena) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if self.nueva_contrasena != self.confirmar_contrasena:
            raise ValueError("Las contraseñas nuevas no coinciden")
        if self.contrasena_actual == self.nueva_contrasena:
            raise ValueError("La nueva contraseña debe ser diferente a la actual")
        return self


class CambiarContrasenaResponse(BaseModel):
    mensaje: str


# ── Actualizar perfil ──
class PerfilUpdate(BaseModel):
    Telefono:     Optional[str] = None
    Direccion:    Optional[str] = None
    Municipio:    Optional[str] = None
    Departamento: Optional[str] = None


# ── Foto de perfil (Cloudinary) ──
class FotoUrlInput(BaseModel):
    url: str = Field(example="https://res.cloudinary.com/demo/image/upload/sample.jpg")


# ── Registro (respuesta simple — token se da después de verificar email) ──
class RegistroResponse(BaseModel):
    mensaje: str


# ── Reenviar verificación ──
class ReenviarVerificacionInput(BaseModel):
    correo: str = Field(example="ana@gmail.com")


class ReenviarVerificacionResponse(BaseModel):
    mensaje: str