from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Tipos de notificación disponibles ──
TIPO_STOCK      = "stock_minimo"
TIPO_PEDIDO     = "pedido_nuevo"
TIPO_DEVOLUCION = "devolucion"
TIPO_DOMICILIO  = "domicilio"


# ── Estructura de una notificación ──
class NotificacionResponse(BaseModel):
    id:          str           # identificador único generado: "tipo_idregistro" ej: "stock_3"
    tipo:        str           # stock_minimo | pedido_nuevo | devolucion | domicilio
    titulo:      str
    mensaje:     str
    fecha:       Optional[datetime] = None
    referencia_id: int         # ID del registro origen (insumo, venta, etc.)


# ── Respuesta general ──
class NotificacionesResponse(BaseModel):
    total:          int
    notificaciones: list[NotificacionResponse]


# ── Para eliminar una notificación (se guarda en lista negra en memoria) ──
class EliminarNotificacion(BaseModel):
    id: str                    # "tipo_idregistro"