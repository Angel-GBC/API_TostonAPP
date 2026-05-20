from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal

from src.shared.services.models import OrdenProduccion, Producto, Insumo, FichaTecnica, Estado
from .schemas import OrdenCreate, OrdenUpdate


def _label_estado(db: Session, id_estado: int) -> str:
    """Obtiene el nombre del estado desde la tabla Estados."""
    estado = db.query(Estado).filter(Estado.ID_Estados == id_estado).first()
    return estado.Estado if estado else None


def _calcular_costo(db: Session, id_insumo: int, cantidad: int) -> Decimal:
    """
    Calcula el costo de la orden buscando el precio unitario del insumo
    en su último lote de compra.
    Fórmula: precio_unitario_lote * cantidad
    Si no hay lote, retorna 0.
    """
    from src.shared.services.models import LoteCompra, DetalleCompra

    # Busca el último detalle de compra del insumo para obtener el precio unitario
    detalle = (
        db.query(DetalleCompra)
        .filter(DetalleCompra.ID_Insumo == id_insumo)
        .order_by(DetalleCompra.ID_Detalle_Compra.desc())
        .first()
    )

    if detalle and detalle.Precio_Und:
        return Decimal(str(detalle.Precio_Und)) * Decimal(str(cantidad))
    return Decimal("0")


def _formato_orden(orden: OrdenProduccion, db: Session) -> dict:
    """Construye el dict de respuesta con nombres legibles."""
    producto = db.query(Producto).filter(
        Producto.ID_Producto == orden.ID_Producto
    ).first()

    insumo = db.query(Insumo).filter(
        Insumo.ID_Insumo == orden.ID_Insumo
    ).first()

    ficha = db.query(FichaTecnica).filter(
        FichaTecnica.ID_Ficha == orden.ID_Ficha
    ).first() if orden.ID_Ficha else None

    return {
        "ID_Orden_Produccion": orden.ID_Orden_Produccion,
        "ID_Producto":         orden.ID_Producto,
        "nombre_producto":     producto.nombre if producto else None,
        "ID_Insumo":           orden.ID_Insumo,
        "nombre_insumo":       insumo.Nombre if insumo else None,
        "ID_Ficha":            orden.ID_Ficha,
        "version_ficha":       ficha.Version if ficha else None,
        "Cantidad":            orden.Cantidad,
        "Fecha_inicio":        orden.Fecha_inicio,
        "Fecha_Entrega":       orden.Fecha_Entrega,
        "Estado":              orden.Estado,
        "estado_label":        _label_estado(db, orden.Estado) if orden.Estado else None,
        "Costo":               orden.Costo,
    }


def obtener_ordenes(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None
) -> dict:
    """Lista paginada. Busca por nombre de producto o código de orden."""
    query = db.query(OrdenProduccion)

    if busqueda:
        termino = f"%{busqueda}%"
        productos_ids = (
            db.query(Producto.ID_Producto)
            .filter(Producto.nombre.ilike(termino))
            .subquery()
        )
        query = query.filter(
            OrdenProduccion.ID_Producto.in_(productos_ids)
        )

    total  = query.count()
    offset = (pagina - 1) * por_pagina
    ordenes = query.offset(offset).limit(por_pagina).all()

    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "ordenes":    [_formato_orden(o, db) for o in ordenes],
    }


def obtener_orden(db: Session, id_orden: int) -> dict:
    """Retorna una orden por ID o lanza 404."""
    orden = db.query(OrdenProduccion).filter(
        OrdenProduccion.ID_Orden_Produccion == id_orden
    ).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return _formato_orden(orden, db)


def crear_orden(db: Session, datos: OrdenCreate) -> dict:
    """Crea la orden y calcula el costo automáticamente."""

    # Verifica que el producto existe
    if not db.query(Producto).filter(Producto.ID_Producto == datos.ID_Producto).first():
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Verifica que el insumo existe
    if not db.query(Insumo).filter(Insumo.ID_Insumo == datos.ID_Insumo).first():
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    costo = _calcular_costo(db, datos.ID_Insumo, datos.Cantidad)

    # Estado inicial: Pendiente (ID quemado en BD, ajusta si difiere)
    ESTADO_PENDIENTE = 1

    nueva = OrdenProduccion(
        ID_Producto   = datos.ID_Producto,
        ID_Insumo     = datos.ID_Insumo,
        ID_Ficha      = datos.ID_Ficha,
        Cantidad      = datos.Cantidad,
        Fecha_inicio  = datos.Fecha_inicio,
        Fecha_Entrega = datos.Fecha_Entrega,
        Estado        = ESTADO_PENDIENTE,
        Costo         = costo,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return _formato_orden(nueva, db)


def editar_orden(db: Session, id_orden: int, datos: OrdenUpdate) -> dict:
    """Edita la orden y recalcula el costo si cambia cantidad o insumo."""
    orden = db.query(OrdenProduccion).filter(
        OrdenProduccion.ID_Orden_Produccion == id_orden
    ).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(orden, campo, valor)

    # Recalcula costo si cambió cantidad o insumo
    if datos.Cantidad or datos.ID_Insumo:
        orden.Costo = _calcular_costo(db, orden.ID_Insumo, orden.Cantidad)

    db.commit()
    db.refresh(orden)
    return _formato_orden(orden, db)


def cambiar_estado(db: Session, id_orden: int, nuevo_estado: int) -> dict:
    """Cambia el estado de la orden."""
    orden = db.query(OrdenProduccion).filter(
        OrdenProduccion.ID_Orden_Produccion == id_orden
    ).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    orden.Estado = nuevo_estado
    db.commit()
    db.refresh(orden)
    return _formato_orden(orden, db)


def eliminar_orden(db: Session, id_orden: int) -> dict:
    """Elimina una orden de producción."""
    orden = db.query(OrdenProduccion).filter(
        OrdenProduccion.ID_Orden_Produccion == id_orden
    ).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    db.delete(orden)
    db.commit()
    return {"mensaje": f"Orden {id_orden} eliminada correctamente"}