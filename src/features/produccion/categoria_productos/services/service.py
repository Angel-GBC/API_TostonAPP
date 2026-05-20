from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from src.shared.services.models import CategoriaProducto, Producto
from .schemas import CategoriaProductoCreate, CategoriaProductoUpdate


def _formato_categoria(categoria: CategoriaProducto, db: Session) -> dict:
    """Construye el dict con los productos asociados."""
    productos = db.query(Producto).filter(
        Producto.ID_Categoria == categoria.ID_Categoria
    ).all()

    return {
        "ID_Categoria":     categoria.ID_Categoria,
        "Nombre_Categoria": categoria.Nombre_Categoria,
        "Descripcion":      categoria.Descripcion,
        "Icono":            categoria.Icono,
        "Estado":           categoria.Estado,
        "Fecha_creacion":   categoria.Fecha_Creacion,
        "productos": [
            {"ID_Producto": p.ID_Producto, "nombre": p.nombre}
            for p in productos
        ],
        "total_productos": len(productos),
    }


def obtener_categorias(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None
) -> dict:
    """Lista paginada. Busca por nombre o descripción."""
    query = db.query(CategoriaProducto)

    if busqueda:
        termino = f"%{busqueda}%"
        query = query.filter(
            CategoriaProducto.Nombre_Categoria.ilike(termino) |
            CategoriaProducto.Descripcion.ilike(termino)
        )

    total      = query.count()
    offset     = (pagina - 1) * por_pagina
    categorias = query.offset(offset).limit(por_pagina).all()

    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "categorias": [_formato_categoria(c, db) for c in categorias],
    }


def obtener_categoria(db: Session, id_categoria: int) -> dict:
    """Retorna una categoría por ID o lanza 404."""
    categoria = db.query(CategoriaProducto).filter(
        CategoriaProducto.ID_Categoria == id_categoria
    ).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return _formato_categoria(categoria, db)


def crear_categoria(db: Session, datos: CategoriaProductoCreate) -> dict:
    """Crea una nueva categoría de productos."""
    if db.query(CategoriaProducto).filter(
        CategoriaProducto.Nombre_Categoria == datos.Nombre_Categoria
    ).first():
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")

    nueva = CategoriaProducto(
        Nombre_Categoria = datos.Nombre_Categoria,
        Descripcion      = datos.Descripcion,
        Icono            = datos.Icono,
        Estado           = 1,
        Fecha_Creacion   = datetime.now(),
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return _formato_categoria(nueva, db)


def editar_categoria(db: Session, id_categoria: int, datos: CategoriaProductoUpdate) -> dict:
    """Edita solo los campos enviados."""
    categoria = db.query(CategoriaProducto).filter(
        CategoriaProducto.ID_Categoria == id_categoria
    ).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(categoria, campo, valor)

    db.commit()
    db.refresh(categoria)
    return _formato_categoria(categoria, db)


def cambiar_estado(db: Session, id_categoria: int, nuevo_estado: int) -> dict:
    """Cambia el estado ON/OFF."""
    categoria = db.query(CategoriaProducto).filter(
        CategoriaProducto.ID_Categoria == id_categoria
    ).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    categoria.Estado = nuevo_estado
    db.commit()
    db.refresh(categoria)
    return _formato_categoria(categoria, db)


def eliminar_categoria(db: Session, id_categoria: int) -> dict:
    """
    Elimina la categoría. Los productos asociados quedan sin categoría
    pero no se eliminan.
    """
    categoria = db.query(CategoriaProducto).filter(
        CategoriaProducto.ID_Categoria == id_categoria
    ).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Desasocia los productos antes de eliminar
    db.query(Producto).filter(
        Producto.ID_Categoria == id_categoria
    ).update({"ID_Categoria": None})

    db.delete(categoria)
    db.commit()
    return {"mensaje": f"Categoría {id_categoria} eliminada correctamente"}