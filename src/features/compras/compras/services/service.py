from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal

from src.shared.services.models import (
    Compra, DetalleCompra, LoteCompra, Insumo, Proveedor, Estado
)
from src.shared.services.notificaciones_utils import notificar_stock_insumo
from .schemas import CompraCreate


# ─────────────────────────────────────────
# HELPERS DE STOCK
# ─────────────────────────────────────────

def _actualizar_estado_insumo(insumo: Insumo) -> None:
    """Actualiza el estado del insumo según reglas de stock de CLAUDE.md."""
    stock  = insumo.Stock_Actual or 0
    minimo = insumo.Stock_Minimo or 0
    if stock == 0:
        insumo.Estado = 15      # Agotado
    elif stock <= minimo:
        insumo.Estado = 14      # Stock bajo
    else:
        insumo.Estado = 1       # Activo


# ─────────────────────────────────────────
# FORMATO DE RESPUESTA
# ─────────────────────────────────────────

def _formato_detalle(detalle: DetalleCompra, db: Session) -> dict:
    insumo = db.query(Insumo).filter(Insumo.ID_Insumo == detalle.ID_Insumo).first()
    return {
        "ID_Detalle_Compra": detalle.ID_Detalle_Compra,
        "ID_Insumo":         detalle.ID_Insumo,
        "nombre_insumo":     insumo.Nombre if insumo else None,
        "ID_Lote_Compra":    detalle.ID_Lote_Compra,
        "Cantidad":          detalle.Cantidad,
        "Precio_Und":        detalle.Precio_Und,
        "Notas":             detalle.Notas,
    }


def _formato_compra(compra: Compra, db: Session) -> dict:
    proveedor = db.query(Proveedor).filter(
        Proveedor.ID_Proveedor == compra.ID_Proveedor
    ).first()
    estado = db.query(Estado).filter(Estado.ID_Estados == compra.Estado).first()
    detalles = db.query(DetalleCompra).filter(
        DetalleCompra.ID_Compra == compra.ID_Compra
    ).all()

    return {
        "ID_Compra":         compra.ID_Compra,
        "ID_Proveedor":      compra.ID_Proveedor,
        "nombre_proveedor":  proveedor.Responsable if proveedor else None,
        "Total_Pago":        compra.Total_Pago,
        "Fecha_Compra":      compra.Fecha_Compra,
        "Estado":            compra.Estado,
        "estado_label":      estado.Estado if estado else None,
        "Metodo_Pago":       compra.Metodo_Pago,
        "detalles":          [_formato_detalle(d, db) for d in detalles],
    }


# ─────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────

def obtener_compras(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None,
    id_proveedor: int = None,
) -> dict:
    """Lista paginada de compras. Filtra por proveedor o busca por método de pago."""
    query = db.query(Compra)

    if id_proveedor:
        query = query.filter(Compra.ID_Proveedor == id_proveedor)

    if busqueda:
        termino = f"%{busqueda}%"
        query = query.filter(Compra.Metodo_Pago.ilike(termino))

    total   = query.count()
    offset  = (pagina - 1) * por_pagina
    compras = query.order_by(Compra.Fecha_Compra.desc()).offset(offset).limit(por_pagina).all()

    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "compras":    [_formato_compra(c, db) for c in compras],
    }


def obtener_compra(db: Session, id_compra: int) -> dict:
    """Retorna el detalle de una compra por ID o lanza 404."""
    compra = db.query(Compra).filter(Compra.ID_Compra == id_compra).first()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return _formato_compra(compra, db)


def crear_compra(db: Session, datos: CompraCreate) -> dict:
    """
    Registra una compra completa:
    1. Valida que el proveedor exista.
    2. Por cada detalle: valida insumo, crea LoteCompra, actualiza Stock_Actual del insumo.
    3. Crea la Compra con el total calculado.
    4. Crea los DetalleCompra asociando lote e insumo.
    5. Actualiza el estado de cada insumo y envía notificaciones de stock.
    Todo en una sola transacción — si algo falla, se hace rollback completo.
    """
    # Valida proveedor
    proveedor = db.query(Proveedor).filter(
        Proveedor.ID_Proveedor == datos.ID_Proveedor
    ).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    # Calcula el total de la compra
    total_pago = sum(
        Decimal(str(d.Precio_Und)) * d.Cantidad
        for d in datos.detalles
    )

    # Crea la compra principal
    nueva_compra = Compra(
        ID_Proveedor = datos.ID_Proveedor,
        Total_Pago   = total_pago,
        Fecha_Compra = datos.Fecha_Compra or datetime.now(),
        Estado       = 4,           # 4 = Confirmado
        Metodo_Pago  = datos.Metodo_Pago,
    )
    db.add(nueva_compra)
    db.flush()   # obtiene el ID sin commit aún

    for item in datos.detalles:
        # Valida que el insumo exista
        insumo = db.query(Insumo).filter(Insumo.ID_Insumo == item.ID_Insumo).first()
        if not insumo:
            db.rollback()
            raise HTTPException(
                status_code=404,
                detail=f"Insumo con ID {item.ID_Insumo} no encontrado"
            )

        # Crea el LoteCompra para este ítem
        lote = LoteCompra(
            ID_Insumo         = item.ID_Insumo,
            Fecha_Vencimiento = item.Fecha_Vencimiento,
            Cantidad_Inicial  = item.Cantidad,
            Estado            = 1,     # Activo
        )
        db.add(lote)
        db.flush()  # obtiene el ID del lote

        # Crea el DetalleCompra
        detalle = DetalleCompra(
            ID_Compra      = nueva_compra.ID_Compra,
            ID_Insumo      = item.ID_Insumo,
            ID_Lote_Compra = lote.ID_Lote_Compra,
            Cantidad       = item.Cantidad,
            Precio_Und     = item.Precio_Und,
            Notas          = item.Notas,
        )
        db.add(detalle)

        # Actualiza Stock_Actual del insumo
        insumo.Stock_Actual = (insumo.Stock_Actual or 0) + item.Cantidad

        # Actualiza el ID_Lote_Compra del insumo (último lote asociado)
        insumo.ID_Lote_Compra = lote.ID_Lote_Compra

        # Recalcula estado del insumo
        _actualizar_estado_insumo(insumo)

    db.commit()
    db.refresh(nueva_compra)

    # Notificaciones de stock (fuera de la transacción principal)
    for item in datos.detalles:
        insumo = db.query(Insumo).filter(Insumo.ID_Insumo == item.ID_Insumo).first()
        if insumo:
            notificar_stock_insumo(db, insumo)
    db.commit()

    return _formato_compra(nueva_compra, db)
