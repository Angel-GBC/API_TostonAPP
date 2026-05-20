from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal

from src.shared.services.models import (
    Venta, VentaXProducto, DetalleVenta, Producto, Usuario,
    Estado, Domicilio, CreditoCliente, MovimientoCredito,
    Descuento, DescuentoXUsuario, DescuentoXVenta
)
from .schemas import VentaCreate, DomicilioVentaInput


def _label_estado(db: Session, id_estado: int) -> str:
    estado = db.query(Estado).filter(Estado.ID_Estados == id_estado).first()
    return estado.Estado if estado else None


def _formato_venta(venta: Venta, db: Session) -> dict:
    """Construye la respuesta completa de una venta."""
    usuario = db.query(Usuario).filter(Usuario.ID_Usuario == venta.ID_Usuario).first()

    vxp       = db.query(VentaXProducto).filter(VentaXProducto.ID_Venta == venta.ID_Venta).all()
    productos = []
    for v in vxp:
        producto = db.query(Producto).filter(Producto.ID_Producto == v.ID_Producto).first()
        precio   = producto.Precio_venta if producto else Decimal("0")
        productos.append({
            "ID_Producto":     v.ID_Producto,
            "nombre_producto": producto.nombre if producto else None,
            "Cantidad":        v.Cantidad,
            "precio_unitario": precio,
            "subtotal":        precio * Decimal(str(v.Cantidad)),
        })

    detalle            = db.query(DetalleVenta).filter(DetalleVenta.ID_Venta == venta.ID_Venta).first()
    credito_aplicado   = detalle.Descuento if detalle else Decimal("0")
    iva                = detalle.IVA if detalle else Decimal("0")

    dxv                = db.query(DescuentoXVenta).filter(DescuentoXVenta.ID_Venta == venta.ID_Venta).first()
    descuento_aplicado = dxv.Monto_Aplicado if dxv else Decimal("0")

    domicilio      = db.query(Domicilio).filter(Domicilio.ID_Venta == venta.ID_Venta).first()
    subtotal_bruto = sum(p["subtotal"] for p in productos)

    return {
        "ID_Venta":           venta.ID_Venta,
        "ID_Usuario":         venta.ID_Usuario,
        "nombre_cliente":     f"{usuario.Nombre} {usuario.Apellidos}" if usuario else None,
        "Total":              venta.Total,
        "subtotal_bruto":     subtotal_bruto,
        "credito_aplicado":   credito_aplicado,
        "descuento_aplicado": descuento_aplicado,
        "Estado":             venta.Estado,
        "estado_label":       _label_estado(db, venta.Estado) if venta.Estado else None,
        "Metodo_Pago":        venta.Metodo_Pago,
        "Fecha_Venta":        venta.Fecha_Venta,
        "Fecha_pedido":       venta.Fecha_pedido,
        "productos":          productos,
        "tiene_domicilio":    domicilio is not None,
        "ID_Domicilio":       domicilio.ID_Domicilio if domicilio else None,
    }


def _aplicar_credito(db: Session, id_usuario: int, monto_restante: Decimal, id_venta: int) -> Decimal:
    credito = db.query(CreditoCliente).filter(
        CreditoCliente.ID_Usuario == id_usuario
    ).first()

    if not credito or credito.Saldo <= 0:
        return Decimal("0")

    credito_usado        = min(credito.Saldo, monto_restante)
    credito.Saldo       -= credito_usado
    credito.Fecha_Update = datetime.now()

    db.add(MovimientoCredito(
        ID_Credito    = credito.ID_Credito,
        ID_Devolucion = None,
        ID_Venta      = id_venta,
        Tipo          = "uso",
        Monto         = credito_usado,
        Fecha         = datetime.now(),
    ))
    return credito_usado


def _aplicar_descuento(
    db: Session,
    id_usuario: int,
    codigo: str,
    monto_restante: Decimal,
    id_venta: int
) -> Decimal:
    descuento = None

    if codigo:
        descuento = db.query(Descuento).filter(
            Descuento.Codigo == codigo,
            Descuento.Estado == 1,
        ).first()
        if descuento:
            if descuento.Fecha_Fin and descuento.Fecha_Fin < datetime.now():
                raise HTTPException(status_code=400, detail="El cupón ha vencido")
            if descuento.Usos_Max and descuento.Usos_Actuales >= descuento.Usos_Max:
                raise HTTPException(status_code=400, detail="El cupón ha alcanzado su límite de usos")

    if not descuento:
        asignacion = db.query(DescuentoXUsuario).filter(
            DescuentoXUsuario.ID_Usuario == id_usuario,
            DescuentoXUsuario.Usado      == False,
        ).join(Descuento).filter(Descuento.Estado == 1).first()

        if asignacion:
            descuento = db.query(Descuento).filter(
                Descuento.ID_Descuento == asignacion.ID_Descuento
            ).first()

    if not descuento:
        usuario = db.query(Usuario).filter(Usuario.ID_Usuario == id_usuario).first()
        if usuario and usuario.Fecha_creacion:
            meses     = (datetime.now() - usuario.Fecha_creacion).days // 30
            descuento = (
                db.query(Descuento)
                .filter(
                    Descuento.Tipo          == "antiguedad",
                    Descuento.Meses_Minimos <= meses,
                    Descuento.Estado        == 1,
                )
                .order_by(Descuento.Porcentaje.desc())
                .first()
            )

    if not descuento:
        return Decimal("0")

    monto_descontado = (monto_restante * descuento.Porcentaje / 100).quantize(Decimal("0.01"))

    db.add(DescuentoXVenta(
        ID_Venta       = id_venta,
        ID_Descuento   = descuento.ID_Descuento,
        Monto_Aplicado = monto_descontado,
    ))

    descuento.Usos_Actuales += 1

    if descuento.Tipo == "emision":
        asignacion = db.query(DescuentoXUsuario).filter(
            DescuentoXUsuario.ID_Descuento == descuento.ID_Descuento,
            DescuentoXUsuario.ID_Usuario   == id_usuario,
        ).first()
        if asignacion:
            asignacion.Usado = True

    return monto_descontado


def obtener_ventas(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None,
    id_usuario: int = None,
    estado: int = None,
) -> dict:
    query = db.query(Venta)

    if id_usuario:
        query = query.filter(Venta.ID_Usuario == id_usuario)

    if estado:
        query = query.filter(Venta.Estado == estado)

    if busqueda:
        termino      = f"%{busqueda}%"
        usuarios_ids = (
            db.query(Usuario.ID_Usuario)
            .filter(
                Usuario.Nombre.ilike(termino) |
                Usuario.Apellidos.ilike(termino)
            )
            .subquery()
        )
        query = query.filter(Venta.ID_Usuario.in_(usuarios_ids))

    total  = query.count()
    offset = (pagina - 1) * por_pagina
    ventas = query.order_by(Venta.Fecha_Venta.desc()).offset(offset).limit(por_pagina).all()

    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "ventas":     [_formato_venta(v, db) for v in ventas],
    }


def obtener_mis_ventas(
    db: Session,
    actual: dict,
    pagina: int = 1,
    por_pagina: int = 10,
) -> dict:
    """Retorna todas las ventas del cliente autenticado (cualquier estado)."""
    if actual["tipo"] != "usuario":
        raise HTTPException(status_code=403, detail="Solo disponible para clientes")

    id_usuario = actual["registro"].ID_Usuario
    query      = db.query(Venta).filter(Venta.ID_Usuario == id_usuario)
    total      = query.count()
    offset     = (pagina - 1) * por_pagina
    ventas     = query.order_by(Venta.Fecha_pedido.desc()).offset(offset).limit(por_pagina).all()

    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "ventas":     [_formato_venta(v, db) for v in ventas],
    }


def obtener_venta(db: Session, id_venta: int) -> dict:
    venta = db.query(Venta).filter(Venta.ID_Venta == id_venta).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return _formato_venta(venta, db)


def crear_venta(db: Session, datos: VentaCreate) -> dict:
    """
    Flujo completo de creación de venta:
    1. Valida cliente y productos
    2. Si hay domicilio → verifica que el cliente tenga teléfono registrado
    3. Calcula subtotal bruto
    4. Aplica crédito si el cliente lo desea
    5. Aplica descuento si queda saldo pendiente
    6. Descuenta stock de productos
    7. Crea domicilio si se solicitó
    """
    # Verifica cliente
    usuario = db.query(Usuario).filter(Usuario.ID_Usuario == datos.ID_Usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Si el pedido incluye domicilio, el cliente debe tener teléfono registrado
    if datos.domicilio and not usuario.Telefono:
        raise HTTPException(
            status_code=400,
            detail="Debes registrar tu número de teléfono en tu perfil antes de solicitar un domicilio"
        )

    # Valida productos y calcula subtotal
    subtotal_bruto = Decimal("0")
    for p in datos.productos:
        producto = db.query(Producto).filter(Producto.ID_Producto == p.ID_Producto).first()
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto {p.ID_Producto} no encontrado")
        if producto.Stock < p.Cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {producto.nombre}"
            )
        subtotal_bruto += producto.Precio_venta * Decimal(str(p.Cantidad))

    ESTADO_PENDIENTE = 1

    nueva_venta = Venta(
        ID_Usuario   = datos.ID_Usuario,
        Total        = subtotal_bruto,
        Estado       = ESTADO_PENDIENTE,
        Metodo_Pago  = datos.Metodo_Pago,
        Fecha_Venta  = datetime.now(),
        Fecha_pedido = datetime.now(),
    )
    db.add(nueva_venta)
    db.flush()

    for p in datos.productos:
        producto = db.query(Producto).filter(Producto.ID_Producto == p.ID_Producto).first()
        db.add(VentaXProducto(
            ID_Venta    = nueva_venta.ID_Venta,
            ID_Producto = p.ID_Producto,
            Cantidad    = p.Cantidad,
        ))
        producto.Stock -= p.Cantidad

    monto_restante   = subtotal_bruto
    credito_aplicado = Decimal("0")

    if datos.usar_credito:
        credito_aplicado = _aplicar_credito(db, datos.ID_Usuario, monto_restante, nueva_venta.ID_Venta)
        monto_restante  -= credito_aplicado

    descuento_aplicado = Decimal("0")
    if monto_restante > 0:
        descuento_aplicado = _aplicar_descuento(
            db, datos.ID_Usuario, datos.codigo_descuento, monto_restante, nueva_venta.ID_Venta
        )
        monto_restante -= descuento_aplicado

    nueva_venta.Total = max(monto_restante, Decimal("0"))

    db.add(DetalleVenta(
        ID_Venta    = nueva_venta.ID_Venta,
        A_Nombre_De = datos.A_Nombre_De,
        IVA         = Decimal("0"),
        Descuento   = credito_aplicado,
        SubTotal    = subtotal_bruto,
    ))

    if datos.domicilio:
        ESTADO_ASIGNADO = 2
        estado_dom      = ESTADO_ASIGNADO if datos.domicilio.ID_Empleado else ESTADO_PENDIENTE
        db.add(Domicilio(
            ID_Venta             = nueva_venta.ID_Venta,
            ID_Empleado          = datos.domicilio.ID_Empleado,
            Fecha_asignacion     = datetime.now(),
            Fecha_entrega        = datos.domicilio.Fecha_entrega,
            Observaciones        = datos.domicilio.Observaciones,
            Estado               = estado_dom,
            Direccion_entrega    = datos.domicilio.Direccion_entrega,
            Municipio_entrega    = datos.domicilio.Municipio_entrega,
            Departamento_entrega = datos.domicilio.Departamento_entrega,
        ))

    db.commit()
    db.refresh(nueva_venta)
    return _formato_venta(nueva_venta, db)


def cambiar_estado(db: Session, id_venta: int, nuevo_estado: int) -> dict:
    venta = db.query(Venta).filter(Venta.ID_Venta == id_venta).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    # Si se está cancelando y el estado anterior no era ya cancelado,
    # devolver el stock de cada producto al inventario.
    ESTADOS_CANCELACION = {3, 5}
    if nuevo_estado in ESTADOS_CANCELACION and venta.Estado not in ESTADOS_CANCELACION:
        items = db.query(VentaXProducto).filter(VentaXProducto.ID_Venta == id_venta).all()
        for item in items:
            producto = db.query(Producto).filter(Producto.ID_Producto == item.ID_Producto).first()
            if producto:
                producto.Stock += item.Cantidad

        # Devolver crédito si se usó en esta venta
        detalle = db.query(DetalleVenta).filter(DetalleVenta.ID_Venta == id_venta).first()
        if detalle and detalle.Descuento and detalle.Descuento > 0:
            credito = db.query(CreditoCliente).filter(
                CreditoCliente.ID_Usuario == venta.ID_Usuario
            ).first()
            if credito:
                credito.Saldo        += detalle.Descuento
                credito.Fecha_Update  = datetime.now()
                db.add(MovimientoCredito(
                    ID_Credito    = credito.ID_Credito,
                    ID_Devolucion = None,
                    ID_Venta      = id_venta,
                    Tipo          = "recarga",
                    Monto         = detalle.Descuento,
                    Fecha         = datetime.now(),
                ))

    venta.Estado = nuevo_estado
    db.commit()
    db.refresh(venta)
    return _formato_venta(venta, db)