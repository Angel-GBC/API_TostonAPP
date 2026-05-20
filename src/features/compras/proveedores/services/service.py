from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.shared.services.models import Proveedor, SujetoDerecho
from .schemas import ProveedorCreate, ProveedorUpdate


def _formato_proveedor(proveedor: Proveedor, db: Session) -> dict:
    """Construye el dict de respuesta con el nombre del sujeto de derecho."""
    sujeto = db.query(SujetoDerecho).filter(
        SujetoDerecho.ID_Sujeto_Derecho == proveedor.Sujeto_Derecho
    ).first()

    return {
        "ID_Proveedor":   proveedor.ID_Proveedor,
        "Sujeto_Derecho": proveedor.Sujeto_Derecho,
        "nombre_sujeto":  sujeto.Sujeto_Derecho if sujeto else None,
        "Responsable":    proveedor.Responsable,
        "Direccion":      proveedor.Direccion,
        "Municipio":      proveedor.Municipio,
        "Departamento":   proveedor.Departamento,
        "Telefono":       proveedor.Telefono,
        "Correo":         proveedor.Correo,
    }


def obtener_proveedores(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None
) -> dict:
    """Lista paginada. Busca por nombre del responsable, correo o teléfono."""
    query = db.query(Proveedor)

    if busqueda:
        termino = f"%{busqueda}%"
        query = query.filter(
            Proveedor.Responsable.ilike(termino) |
            Proveedor.Correo.ilike(termino) |
            Proveedor.Telefono.ilike(termino)
        )

    total      = query.count()
    offset     = (pagina - 1) * por_pagina
    proveedores = query.offset(offset).limit(por_pagina).all()

    return {
        "total":       total,
        "pagina":      pagina,
        "por_pagina":  por_pagina,
        "proveedores": [_formato_proveedor(p, db) for p in proveedores],
    }


def obtener_proveedor(db: Session, id_proveedor: int) -> dict:
    """Retorna un proveedor por ID o lanza 404."""
    proveedor = db.query(Proveedor).filter(
        Proveedor.ID_Proveedor == id_proveedor
    ).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return _formato_proveedor(proveedor, db)


def crear_proveedor(db: Session, datos: ProveedorCreate) -> dict:
    """Crea un nuevo proveedor."""
    # Verifica que el correo no esté duplicado
    if datos.Correo and db.query(Proveedor).filter(
        Proveedor.Correo == datos.Correo
    ).first():
        raise HTTPException(status_code=400, detail="Ya existe un proveedor con ese correo")

    nuevo = Proveedor(
        Sujeto_Derecho = datos.Sujeto_Derecho,
        Responsable    = datos.Responsable,
        Direccion      = datos.Direccion,
        Municipio      = datos.Municipio,
        Departamento   = datos.Departamento,
        Telefono       = datos.Telefono,
        Correo         = datos.Correo,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _formato_proveedor(nuevo, db)


def editar_proveedor(db: Session, id_proveedor: int, datos: ProveedorUpdate) -> dict:
    """Edita solo los campos enviados."""
    proveedor = db.query(Proveedor).filter(
        Proveedor.ID_Proveedor == id_proveedor
    ).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(proveedor, campo, valor)

    db.commit()
    db.refresh(proveedor)
    return _formato_proveedor(proveedor, db)


def eliminar_proveedor(db: Session, id_proveedor: int) -> dict:
    """Elimina un proveedor."""
    proveedor = db.query(Proveedor).filter(
        Proveedor.ID_Proveedor == id_proveedor
    ).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    db.delete(proveedor)
    db.commit()
    return {"mensaje": f"Proveedor {id_proveedor} eliminado correctamente"}