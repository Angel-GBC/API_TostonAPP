from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from src.shared.services.models import Empleado, Usuario, Rol
from src.features.auth.services.service import hashear_contrasena
from .schemas import EmpleadoCreate, UsuarioCreate, PersonaUpdate


def _formato_persona(registro, tipo: str, rol_nombre: str = None) -> dict:
    id_persona = registro.ID_Empleado if tipo == "empleado" else registro.ID_Usuario
    return {
        "id":             id_persona,
        "Cedula":         registro.Cedula,
        "Tipo_Documento": getattr(registro, "Tipo_Documento", None),
        "Nombre":         registro.Nombre,
        "Apellidos":      registro.Apellidos,
        "Correo":         registro.Correo,
        "Direccion":      registro.Direccion,
        "Municipio":      registro.Municipio,
        "Departamento":   registro.Departamento,
        "Telefono":       registro.Telefono,
        "ID_Rol":         getattr(registro, "ID_Rol", None),
        "nombre_rol":     rol_nombre,
        "Estado":         registro.Estado,
        "Fecha_creacion": registro.Fecha_creacion,
        "tipo":           tipo,
    }


def obtener_todos(db: Session, pagina: int = 1, por_pagina: int = 10, busqueda: str = None) -> dict:
    termino = f"%{busqueda}%" if busqueda else None

    q_emp = db.query(Empleado)
    q_usr = db.query(Usuario)

    if termino:
        q_emp = q_emp.filter(
            Empleado.Nombre.ilike(termino) |
            Empleado.Apellidos.ilike(termino) |
            Empleado.Correo.ilike(termino) |
            Empleado.Cedula.ilike(termino)
        )
        q_usr = q_usr.filter(
            Usuario.Nombre.ilike(termino) |
            Usuario.Apellidos.ilike(termino) |
            Usuario.Correo.ilike(termino) |
            Usuario.Cedula.ilike(termino)
        )

    resultado = []
    for emp in q_emp.all():
        rol = db.query(Rol).filter(Rol.ID_Rol == emp.ID_Rol).first()
        resultado.append(_formato_persona(emp, "empleado", rol.Rol if rol else None))
    for cli in q_usr.all():
        resultado.append(_formato_persona(cli, "cliente"))

    total    = len(resultado)
    offset   = (pagina - 1) * por_pagina
    paginado = resultado[offset: offset + por_pagina]

    return {"total": total, "pagina": pagina, "por_pagina": por_pagina, "personas": paginado}


def obtener_persona(db: Session, id_persona: int, tipo: str) -> dict:
    if tipo == "empleado":
        registro = db.query(Empleado).filter(Empleado.ID_Empleado == id_persona).first()
        rol = db.query(Rol).filter(Rol.ID_Rol == registro.ID_Rol).first() if registro else None
        return _formato_persona(registro, tipo, rol.Rol if rol else None)
    else:
        registro = db.query(Usuario).filter(Usuario.ID_Usuario == id_persona).first()

    if not registro:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return _formato_persona(registro, tipo)


def crear_empleado(db: Session, datos: EmpleadoCreate) -> dict:
    if db.query(Empleado).filter(Empleado.Correo == datos.Correo).first():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    nuevo = Empleado(
        Cedula         = datos.Cedula,
        Tipo_Documento = datos.Tipo_Documento,
        Nombre         = datos.Nombre,
        Apellidos      = datos.Apellidos,
        Correo         = datos.Correo,
        Direccion      = datos.Direccion,
        Municipio      = datos.Municipio,
        Departamento   = datos.Departamento,
        Telefono       = datos.Telefono,
        ID_Rol         = datos.ID_Rol,
        Contrasena     = hashear_contrasena(datos.Contrasena),
        Fecha_creacion = datetime.now(),
        Estado         = 1
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _formato_persona(nuevo, "empleado")


def crear_cliente(db: Session, datos: UsuarioCreate) -> dict:
    if db.query(Usuario).filter(Usuario.Correo == datos.Correo).first():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    nuevo = Usuario(
        Cedula         = datos.Cedula,
        Tipo_Documento = datos.Tipo_Documento,
        Nombre         = datos.Nombre,
        Apellidos      = datos.Apellidos,
        Correo         = datos.Correo,
        Direccion      = datos.Direccion,
        Municipio      = datos.Municipio,
        Departamento   = datos.Departamento,
        Telefono       = datos.Telefono,
        Contrasena     = hashear_contrasena(datos.Contrasena),
        Fecha_creacion = datetime.now(),
        Estado         = 1
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _formato_persona(nuevo, "cliente")


def editar_persona(db: Session, id_persona: int, tipo: str, datos: PersonaUpdate) -> dict:
    if tipo == "empleado":
        registro = db.query(Empleado).filter(Empleado.ID_Empleado == id_persona).first()
    else:
        registro = db.query(Usuario).filter(Usuario.ID_Usuario == id_persona).first()

    if not registro:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        if campo == "ID_Rol" and tipo == "cliente":
            continue
        setattr(registro, campo, valor)

    db.commit()
    db.refresh(registro)
    return _formato_persona(registro, tipo)


def cambiar_estado(db: Session, id_persona: int, tipo: str, nuevo_estado: int) -> dict:
    if tipo == "empleado":
        registro = db.query(Empleado).filter(Empleado.ID_Empleado == id_persona).first()
    else:
        registro = db.query(Usuario).filter(Usuario.ID_Usuario == id_persona).first()

    if not registro:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    registro.Estado = nuevo_estado
    db.commit()
    db.refresh(registro)
    return _formato_persona(registro, tipo)


def eliminar_persona(db: Session, id_persona: int, tipo: str) -> dict:
    if tipo == "empleado":
        registro = db.query(Empleado).filter(Empleado.ID_Empleado == id_persona).first()
    else:
        registro = db.query(Usuario).filter(Usuario.ID_Usuario == id_persona).first()

    if not registro:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    db.delete(registro)
    db.commit()
    return {"mensaje": f"{tipo.capitalize()} {id_persona} eliminado correctamente"}