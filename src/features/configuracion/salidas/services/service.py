from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from src.shared.services.models import Salida, Insumo, Producto, Empleado, Estado
from src.shared.services.notificaciones_utils import notificar_stock_insumo, notificar_stock_producto
from .schemas import SalidaCreate

ESTADO_ACTIVO  = 1
ESTADO_ANULADA = 12


# ─────────────────────────────────────────
# HELPERS DE STOCK
# ─────────────────────────────────────────

def _actualizar_estado_insumo(insumo: Insumo) -> None:
    stock   = insumo.Stock_Actual or 0
    minimo  = insumo.Stock_Minimo or 0
    if stock == 0:
        insumo.Estado = 15      # Agotado
    elif stock <= minimo:
        insumo.Estado = 14      # Stock bajo
    else:
        insumo.Estado = 1       # Activo


def _actualizar_estado_producto(producto: Producto) -> None:
    stock   = producto.Stock or 0
    minimo  = getattr(producto, "Stock_Minimo", 0) or 0
    if stock == 0:
        producto.Estado = 15    # Agotado
    elif stock <= minimo:
        producto.Estado = 14    # Stock bajo
    else:
        producto.Estado = 1     # Activo


# ─────────────────────────────────────────
# FORMATO DE RESPUESTA
# ─────────────────────────────────────────

def _formato_salida(salida: Salida, db: Session) -> dict:
    insumo   = db.query(Insumo).filter(Insumo.ID_Insumo == salida.ID_Insumo).first() \
               if salida.ID_Insumo else None
    producto = db.query(Producto).filter(Producto.ID_Producto == salida.ID_Producto).first() \
               if salida.ID_Producto else None
    empleado = db.query(Empleado).filter(Empleado.ID_Empleado == salida.ID_Empleado).first() \
               if salida.ID_Empleado else None
    estado   = db.query(Estado).filter(Estado.ID_Estados == salida.Estado).first()

    return {
        "ID_Salida":       salida.ID_Salida,
        "Tipo":            salida.Tipo,
        "ID_Insumo":       salida.ID_Insumo,
        "nombre_insumo":   insumo.Nombre if insumo else None,
        "ID_Producto":     salida.ID_Producto,
        "nombre_producto": producto.nombre if producto else None,
        "Cantidad":        salida.Cantidad,
        "Motivo":          salida.Motivo,
        "ID_Empleado":     salida.ID_Empleado,
        "nombre_empleado": f"{empleado.Nombre} {empleado.Apellidos}" if empleado else None,
        "Fecha":           salida.Fecha,
        "Estado":          salida.Estado,
        "estado_label":    estado.Estado if estado else None,
    }


# ─────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────

def obtener_salidas(
    db:          Session,
    pagina:      int  = 1,
    por_pagina:  int  = 10,
    busqueda:    str  = None,
    tipo:        str  = None,
    estado:      int  = None,
    fecha_desde: str  = None,
    fecha_hasta: str  = None,
    id_insumo:   int  = None,
    id_producto: int  = None,
) -> dict:
    query = db.query(Salida)

    if tipo:
        query = query.filter(Salida.Tipo == tipo)
    if estado is not None:
        query = query.filter(Salida.Estado == estado)
    if fecha_desde:
        query = query.filter(Salida.Fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Salida.Fecha <= fecha_hasta)
    if id_insumo:
        query = query.filter(Salida.ID_Insumo == id_insumo)
    if id_producto:
        query = query.filter(Salida.ID_Producto == id_producto)

    if busqueda:
        termino      = f"%{busqueda}%"
        ids_insumo   = db.query(Insumo.ID_Insumo).filter(Insumo.Nombre.ilike(termino)).subquery()
        ids_producto = db.query(Producto.ID_Producto).filter(Producto.nombre.ilike(termino)).subquery()
        query = query.filter(
            Salida.Motivo.ilike(termino)         |
            Salida.ID_Insumo.in_(ids_insumo)     |
            Salida.ID_Producto.in_(ids_producto)
        )

    total   = query.count()
    offset  = (pagina - 1) * por_pagina
    salidas = query.order_by(Salida.Fecha.desc()).offset(offset).limit(por_pagina).all()

    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "salidas":    [_formato_salida(s, db) for s in salidas],
    }


def obtener_salida(db: Session, id_salida: int) -> dict:
    salida = db.query(Salida).filter(Salida.ID_Salida == id_salida).first()
    if not salida:
        raise HTTPException(status_code=404, detail="Salida no encontrada")
    return _formato_salida(salida, db)


def crear_salida(db: Session, datos: SalidaCreate) -> dict:
    """
    Registra la salida y descuenta el stock en una sola transacción.
    Las notificaciones se envían después del commit para no romper atomicidad.
    """
    if datos.ID_Insumo:
        insumo = db.query(Insumo).filter(Insumo.ID_Insumo == datos.ID_Insumo).first()
        if not insumo:
            raise HTTPException(status_code=404, detail="Insumo no encontrado")
        if (insumo.Stock_Actual or 0) < datos.Cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente — disponible: {insumo.Stock_Actual or 0}"
            )
        insumo.Stock_Actual -= datos.Cantidad
        _actualizar_estado_insumo(insumo)

    else:
        producto = db.query(Producto).filter(Producto.ID_Producto == datos.ID_Producto).first()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        if (producto.Stock or 0) < datos.Cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente — disponible: {producto.Stock or 0}"
            )
        producto.Stock -= datos.Cantidad
        _actualizar_estado_producto(producto)

    nueva = Salida(
        Tipo        = datos.Tipo,
        ID_Insumo   = datos.ID_Insumo,
        ID_Producto = datos.ID_Producto,
        Cantidad    = datos.Cantidad,
        Motivo      = datos.Motivo,
        ID_Empleado = datos.ID_Empleado,
        Fecha       = datos.Fecha or datetime.now(),
        Estado      = ESTADO_ACTIVO,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    # Notificaciones fuera de la transacción principal
    if nueva.ID_Insumo:
        insumo = db.query(Insumo).filter(Insumo.ID_Insumo == nueva.ID_Insumo).first()
        if insumo:
            notificar_stock_insumo(db, insumo)
    else:
        producto = db.query(Producto).filter(Producto.ID_Producto == nueva.ID_Producto).first()
        if producto:
            notificar_stock_producto(db, producto)

    return _formato_salida(nueva, db)


def anular_salida(db: Session, id_salida: int) -> dict:
    """
    Anula la salida (Estado=12) y restaura el stock descontado.
    Recalcula el estado de stock del ítem afectado.
    """
    salida = db.query(Salida).filter(Salida.ID_Salida == id_salida).first()
    if not salida:
        raise HTTPException(status_code=404, detail="Salida no encontrada")
    if salida.Estado == ESTADO_ANULADA:
        raise HTTPException(status_code=400, detail="Esta salida ya fue anulada")

    if salida.ID_Insumo:
        insumo = db.query(Insumo).filter(Insumo.ID_Insumo == salida.ID_Insumo).first()
        if insumo:
            insumo.Stock_Actual = (insumo.Stock_Actual or 0) + salida.Cantidad
            _actualizar_estado_insumo(insumo)
    else:
        producto = db.query(Producto).filter(Producto.ID_Producto == salida.ID_Producto).first()
        if producto:
            producto.Stock = (producto.Stock or 0) + salida.Cantidad
            _actualizar_estado_producto(producto)

    salida.Estado = ESTADO_ANULADA
    db.commit()
    db.refresh(salida)

    # Notificaciones fuera de la transacción principal
    if salida.ID_Insumo:
        insumo = db.query(Insumo).filter(Insumo.ID_Insumo == salida.ID_Insumo).first()
        if insumo:
            notificar_stock_insumo(db, insumo)
    else:
        producto = db.query(Producto).filter(Producto.ID_Producto == salida.ID_Producto).first()
        if producto:
            notificar_stock_producto(db, producto)

    return _formato_salida(salida, db)
