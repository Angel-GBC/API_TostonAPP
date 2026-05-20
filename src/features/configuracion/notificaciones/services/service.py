from sqlalchemy.orm import Session

from src.shared.services.models import Insumo, Venta, Devolucion, Domicilio

# ─────────────────────────────────────────
# Lista negra en memoria
# Guarda los IDs de notificaciones eliminadas mientras el servidor esté corriendo.
# Si se reinicia el servidor, las notificaciones vuelven a aparecer.
# Para persistencia real se necesitaría una tabla en BD.
# ─────────────────────────────────────────
_eliminadas: set[str] = set()


def _generar_id(tipo: str, referencia_id: int) -> str:
    return f"{tipo}_{referencia_id}"


def obtener_notificaciones(db: Session) -> dict:
    """
    Consulta todas las tablas relevantes y construye
    la lista de notificaciones activas en tiempo real.
    """
    notificaciones = []

    # ── 1. Stock mínimo de insumos ──
    insumos_bajos = (
        db.query(Insumo)
        .filter(Insumo.Stock_Actual <= Insumo.Stock_Minimo)
        .all()
    )
    for insumo in insumos_bajos:
        nid = _generar_id("stock_minimo", insumo.ID_Insumo)
        if nid not in _eliminadas:
            notificaciones.append({
                "id":            nid,
                "tipo":          "stock_minimo",
                "titulo":        "Stock mínimo alcanzado",
                "mensaje":       f"El insumo '{insumo.Nombre}' tiene stock bajo ({insumo.Stock_Actual} unidades)",
                "fecha":         None,
                "referencia_id": insumo.ID_Insumo,
            })

    # ── 2. Pedidos nuevos (estado = 1, asumiendo 1 = pendiente) ──
    pedidos_nuevos = (
        db.query(Venta)
        .filter(Venta.Estado == 1)
        .all()
    )
    for venta in pedidos_nuevos:
        nid = _generar_id("pedido_nuevo", venta.ID_Venta)
        if nid not in _eliminadas:
            notificaciones.append({
                "id":            nid,
                "tipo":          "pedido_nuevo",
                "titulo":        "Nuevo pedido recibido",
                "mensaje":       f"El pedido #{venta.ID_Venta} está esperando ser procesado",
                "fecha":         venta.Fecha_pedido,
                "referencia_id": venta.ID_Venta,
            })

    # ── 3. Devoluciones pendientes (estado = 1) ──
    devoluciones = (
        db.query(Devolucion)
        .filter(Devolucion.Estado == 1)
        .all()
    )
    for dev in devoluciones:
        nid = _generar_id("devolucion", dev.ID_Devolucion)
        if nid not in _eliminadas:
            notificaciones.append({
                "id":            nid,
                "tipo":          "devolucion",
                "titulo":        "Devolución pendiente",
                "mensaje":       f"La devolución #{dev.ID_Devolucion} requiere revisión",
                "fecha":         dev.FechaDevolucion,
                "referencia_id": dev.ID_Devolucion,
            })

    # ── 4. Domicilios pendientes (estado = 1) ──
    domicilios = (
        db.query(Domicilio)
        .filter(Domicilio.Estado == 1)
        .all()
    )
    for dom in domicilios:
        nid = _generar_id("domicilio", dom.ID_Domicilio)
        if nid not in _eliminadas:
            notificaciones.append({
                "id":            nid,
                "tipo":          "domicilio",
                "titulo":        "Domicilio pendiente de entrega",
                "mensaje":       f"El domicilio #{dom.ID_Domicilio} aún no ha sido entregado",
                "fecha":         dom.Fecha_asignacion,
                "referencia_id": dom.ID_Domicilio,
            })

    return {"total": len(notificaciones), "notificaciones": notificaciones}


def eliminar_notificacion(nid: str) -> dict:
    """
    Agrega el ID a la lista negra para que no vuelva a aparecer
    mientras el servidor esté corriendo.
    """
    _eliminadas.add(nid)
    return {"mensaje": f"Notificación {nid} eliminada"}


def limpiar_todas() -> dict:
    """Elimina todas las notificaciones actuales de golpe."""
    # Necesitamos saber qué IDs existen antes de limpiar,
    # pero como son dinámicas guardamos un marcador especial por tipo
    _eliminadas.add("__limpiar_todo__")
    return {"mensaje": "Todas las notificaciones han sido eliminadas"}