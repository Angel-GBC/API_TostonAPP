from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from src.shared.services.models import Insumo, CategoriaInsumo, UnidadMedida, LoteCompra
from .schemas import InsumoCreate, InsumoUpdate


def _formato_insumo(insumo: Insumo, db: Session) -> dict:
    """Construye el dict de respuesta con categoria, unidad y lote."""
    categoria = db.query(CategoriaInsumo).filter(
        CategoriaInsumo.ID_Categoria == insumo.ID_Categoria
    ).first()

    unidad = db.query(UnidadMedida).filter(
        UnidadMedida.ID_Unidad_Medida == insumo.Unidad_Medida
    ).first()

    lote = db.query(LoteCompra).filter(
        LoteCompra.ID_Lote_Compra == insumo.ID_Lote_Compra
    ).first() if insumo.ID_Lote_Compra else None

    return {
        "ID_Insumo":        insumo.ID_Insumo,
        "Nombre":           insumo.Nombre,
        "ID_Categoria":     insumo.ID_Categoria,
        "nombre_categoria": categoria.Nombre_Categoria if categoria else None,
        "Unidad_Medida":    insumo.Unidad_Medida,
        "simbolo_unidad":   unidad.Simbolo if unidad else None,
        "Stock_Actual":     insumo.Stock_Actual,
        "Stock_Minimo":     insumo.Stock_Minimo,
        "Estado":           insumo.Estado,
        "lote": {
            "ID_Lote_Compra":    lote.ID_Lote_Compra,
            "Fecha_Vencimiento": lote.Fecha_Vencimiento,
            "Cantidad_Inicial":  lote.Cantidad_Inicial,
            "Estado":            lote.Estado,
        } if lote else None,
    }


def _calcular_resumen(db: Session) -> dict:
    """Calcula las 4 tarjetas del tope de la página."""
    todos = db.query(Insumo).all()
    total       = len(todos)
    agotados    = sum(1 for i in todos if i.Stock_Actual == 0)
    stock_bajo  = sum(1 for i in todos if 0 < i.Stock_Actual <= i.Stock_Minimo)
    disponibles = total - agotados - stock_bajo
    return {
        "total":       total,
        "disponibles": disponibles,
        "stock_bajo":  stock_bajo,
        "agotados":    agotados,
    }


def obtener_insumos(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None
) -> dict:
    """Lista paginada con resumen. Busca por nombre, categoría o lote."""
    query = db.query(Insumo)

    if busqueda:
        termino = f"%{busqueda}%"
        # Busca en nombre del insumo o nombre de categoría
        query = query.join(
            CategoriaInsumo,
            CategoriaInsumo.ID_Categoria == Insumo.ID_Categoria,
            isouter=True
        ).filter(
            Insumo.Nombre.ilike(termino) |
            CategoriaInsumo.Nombre_Categoria.ilike(termino)
        )

    total   = query.count()
    offset  = (pagina - 1) * por_pagina
    insumos = query.offset(offset).limit(por_pagina).all()

    return {
        "resumen":    _calcular_resumen(db),
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "insumos":    [_formato_insumo(i, db) for i in insumos],
    }


def obtener_insumo(db: Session, id_insumo: int) -> dict:
    """Retorna un insumo por ID o lanza 404."""
    insumo = db.query(Insumo).filter(Insumo.ID_Insumo == id_insumo).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    return _formato_insumo(insumo, db)


def crear_insumo(db: Session, datos: InsumoCreate) -> dict:
    """
    Crea un insumo y opcionalmente crea su lote de compra.
    Si viene lote, primero crea el lote y luego lo asocia al insumo.
    """
    lote_id = None

    if datos.Lote_Compra and datos.Lote_Compra.Cantidad_Inicial is not None:
        nuevo_lote = LoteCompra(
            Fecha_Vencimiento = datos.Lote_Compra.Fecha_Vencimiento,
            Cantidad_Inicial  = datos.Lote_Compra.Cantidad_Inicial,
            Estado            = 1,
        )
        db.add(nuevo_lote)
        db.flush()          # obtiene el ID sin hacer commit aún
        lote_id = nuevo_lote.ID_Lote_Compra

    nuevo = Insumo(
        Nombre         = datos.Nombre,
        ID_Categoria   = datos.ID_Categoria,
        Unidad_Medida  = datos.Unidad_Medida,
        Stock_Actual   = datos.Stock_Actual,
        Stock_Minimo   = datos.Stock_Minimo,
        ID_Lote_Compra = lote_id,
        Estado         = 1,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Asocia el insumo al lote si se creó
    if lote_id:
        lote = db.query(LoteCompra).filter(LoteCompra.ID_Lote_Compra == lote_id).first()
        lote.ID_Insumo = nuevo.ID_Insumo
        db.commit()

    return _formato_insumo(nuevo, db)


def editar_insumo(db: Session, id_insumo: int, datos: InsumoUpdate) -> dict:
    """Edita solo los campos enviados."""
    insumo = db.query(Insumo).filter(Insumo.ID_Insumo == id_insumo).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(insumo, campo, valor)

    db.commit()
    db.refresh(insumo)
    return _formato_insumo(insumo, db)


def cambiar_estado(db: Session, id_insumo: int, nuevo_estado: int) -> dict:
    """Cambia el estado ON/OFF del insumo."""
    insumo = db.query(Insumo).filter(Insumo.ID_Insumo == id_insumo).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    insumo.Estado = nuevo_estado
    db.commit()
    db.refresh(insumo)
    return _formato_insumo(insumo, db)


def eliminar_insumo(db: Session, id_insumo: int) -> dict:
    """Elimina un insumo y su lote asociado si existe."""
    insumo = db.query(Insumo).filter(Insumo.ID_Insumo == id_insumo).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    # Elimina el lote asociado si existe
    if insumo.ID_Lote_Compra:
        lote = db.query(LoteCompra).filter(
            LoteCompra.ID_Lote_Compra == insumo.ID_Lote_Compra
        ).first()
        if lote:
            db.delete(lote)

    db.delete(insumo)
    db.commit()
    return {"mensaje": f"Insumo {id_insumo} eliminado correctamente"}