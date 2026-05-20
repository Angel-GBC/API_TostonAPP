from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from src.shared.services.models import Domicilio, Venta, Empleado, Usuario, Estado, Producto, VentaXProducto
from .schemas import DomicilioCreate, DomicilioUpdate


def _label_estado(db: Session, id_estado: int) -> str:
    estado = db.query(Estado).filter(Estado.ID_Estados == id_estado).first()
    return estado.Estado if estado else None


def _formato_domicilio(dom: Domicilio, db: Session) -> dict:
    """Construye el dict con cliente, repartidor, estado y datos de la venta."""
    # Obtiene el cliente desde la venta
    venta   = db.query(Venta).filter(Venta.ID_Venta == dom.ID_Venta).first()
    cliente = db.query(Usuario).filter(
        Usuario.ID_Usuario == venta.ID_Usuario
    ).first() if venta else None

    # Obtiene el repartidor
    repartidor = db.query(Empleado).filter(
        Empleado.ID_Empleado == dom.ID_Empleado
    ).first() if dom.ID_Empleado else None

    # Datos de la venta: total, metodo_pago y productos
    total       = float(venta.Total) if venta and venta.Total else 0.0
    metodo_pago = venta.Metodo_Pago or "" if venta else ""
    productos   = []
    if venta:
        items = db.query(VentaXProducto).filter(
            VentaXProducto.ID_Venta == venta.ID_Venta
        ).all()
        for item in items:
            prod   = db.query(Producto).filter(
                Producto.ID_Producto == item.ID_Producto
            ).first()
            precio = float(prod.Precio_venta) if prod and prod.Precio_venta else 0.0
            productos.append({
                "ID_Producto":     item.ID_Producto,
                "nombre_producto": prod.nombre if prod else "",
                "Cantidad":        item.Cantidad,
                "precio_unitario": precio,
                "subtotal":        precio * (item.Cantidad or 0),
            })

    return {
        "ID_Domicilio":         dom.ID_Domicilio,
        "ID_Venta":             dom.ID_Venta,
        "nombre_cliente":       f"{cliente.Nombre} {cliente.Apellidos}" if cliente else None,
        "ID_Empleado":          dom.ID_Empleado,
        "nombre_repartidor":    f"{repartidor.Nombre} {repartidor.Apellidos}" if repartidor else None,
        "Fecha_asignacion":     dom.Fecha_asignacion,
        "Fecha_entrega":        dom.Fecha_entrega,
        "Observaciones":        dom.Observaciones,
        "Estado":               dom.Estado,
        "estado_label":         _label_estado(db, dom.Estado) if dom.Estado else None,
        "Direccion_entrega":    dom.Direccion_entrega,
        "Municipio_entrega":    dom.Municipio_entrega,
        "Departamento_entrega": dom.Departamento_entrega,
        "total":                total,
        "metodo_pago":          metodo_pago,
        "productos":            productos,
    }


def obtener_domicilios(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None,
    estado: int = None
) -> dict:
    """Lista paginada. Busca por nombre de cliente o repartidor. Filtra por estado."""
    query = db.query(Domicilio)

    if estado:
        query = query.filter(Domicilio.Estado == estado)

    if busqueda:
        termino = f"%{busqueda}%"

        # IDs de clientes que coinciden
        clientes_ids = (
            db.query(Venta.ID_Venta)
            .join(Usuario, Usuario.ID_Usuario == Venta.ID_Usuario)
            .filter(
                Usuario.Nombre.ilike(termino) |
                Usuario.Apellidos.ilike(termino)
            )
            .subquery()
        )

        # IDs de repartidores que coinciden
        repartidores_ids = (
            db.query(Empleado.ID_Empleado)
            .filter(
                Empleado.Nombre.ilike(termino) |
                Empleado.Apellidos.ilike(termino)
            )
            .subquery()
        )

        query = query.filter(
            Domicilio.ID_Venta.in_(clientes_ids) |
            Domicilio.ID_Empleado.in_(repartidores_ids) |
            Domicilio.Direccion_entrega.ilike(termino)
        )

    total      = query.count()
    offset     = (pagina - 1) * por_pagina
    domicilios = query.offset(offset).limit(por_pagina).all()

    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "domicilios": [_formato_domicilio(d, db) for d in domicilios],
    }


def obtener_domicilio(db: Session, id_domicilio: int) -> dict:
    dom = db.query(Domicilio).filter(Domicilio.ID_Domicilio == id_domicilio).first()
    if not dom:
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")
    return _formato_domicilio(dom, db)


def crear_domicilio(db: Session, datos: DomicilioCreate) -> dict:
    """Crea un domicilio. Si viene ID_Empleado el estado es Asignado, si no Pendiente."""
    if not db.query(Venta).filter(Venta.ID_Venta == datos.ID_Venta).first():
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    if datos.ID_Empleado:
        if not db.query(Empleado).filter(Empleado.ID_Empleado == datos.ID_Empleado).first():
            raise HTTPException(status_code=404, detail="Empleado repartidor no encontrado")

    # Estado inicial según si viene repartidor o no
    # Ajusta los IDs según tu tabla Estados
    ESTADO_PENDIENTE = 1
    ESTADO_ASIGNADO  = 2
    estado_inicial   = ESTADO_ASIGNADO if datos.ID_Empleado else ESTADO_PENDIENTE

    nuevo = Domicilio(
        ID_Venta             = datos.ID_Venta,
        ID_Empleado          = datos.ID_Empleado,
        Fecha_asignacion     = datetime.now(),
        Fecha_entrega        = datos.Fecha_entrega,
        Observaciones        = datos.Observaciones,
        Estado               = estado_inicial,
        Direccion_entrega    = datos.Direccion_entrega,
        Municipio_entrega    = datos.Municipio_entrega,
        Departamento_entrega = datos.Departamento_entrega,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _formato_domicilio(nuevo, db)


def editar_domicilio(db: Session, id_domicilio: int, datos: DomicilioUpdate) -> dict:
    dom = db.query(Domicilio).filter(Domicilio.ID_Domicilio == id_domicilio).first()
    if not dom:
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(dom, campo, valor)

    db.commit()
    db.refresh(dom)
    return _formato_domicilio(dom, db)


def asignar_repartidor(db: Session, id_domicilio: int, id_empleado: int) -> dict:
    """
    Asigna un repartidor al domicilio.
    Si estaba Pendiente, cambia automáticamente a Asignado.
    """
    dom = db.query(Domicilio).filter(Domicilio.ID_Domicilio == id_domicilio).first()
    if not dom:
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")

    if not db.query(Empleado).filter(Empleado.ID_Empleado == id_empleado).first():
        raise HTTPException(status_code=404, detail="Empleado repartidor no encontrado")

    ESTADO_PENDIENTE = 1
    ESTADO_ASIGNADO  = 2

    dom.ID_Empleado = id_empleado
    if dom.Estado == ESTADO_PENDIENTE:
        dom.Estado = ESTADO_ASIGNADO

    db.commit()
    db.refresh(dom)
    return _formato_domicilio(dom, db)


def cambiar_estado(db: Session, id_domicilio: int, nuevo_estado: int) -> dict:
    # Mapa domicilio -> venta segun lo que interpreta el mobile:
    #   3 = en camino  ->  venta pasa a "en camino"
    #   4 = entregado  ->  venta pasa a "entregado"
    #   5 = cancelado  ->  venta pasa a "cancelado"
    ESTADO_ENTREGADO = 4
    ESTADOS_PROPAGAR = {3, 4, 5}

    dom = db.query(Domicilio).filter(Domicilio.ID_Domicilio == id_domicilio).first()
    if not dom:
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")

    if nuevo_estado == ESTADO_ENTREGADO:
        dom.Fecha_entrega = datetime.now()

    # Propagar el estado del domicilio a la venta asociada
    if nuevo_estado in ESTADOS_PROPAGAR and dom.ID_Venta:
        venta = db.query(Venta).filter(Venta.ID_Venta == dom.ID_Venta).first()
        if venta:
            venta.Estado = nuevo_estado

    dom.Estado = nuevo_estado
    db.commit()
    db.refresh(dom)
    return _formato_domicilio(dom, db)
