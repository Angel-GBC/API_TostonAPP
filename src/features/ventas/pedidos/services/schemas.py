from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ── Respuesta de un pedido (hereda la misma estructura que venta) ──
class PedidoResponse(BaseModel):
    ID_Venta:          int
    ID_Usuario:        Optional[int]      = None
    nombre_cliente:    Optional[str]      = None
    Total:             Optional[Decimal]  = None
    subtotal_bruto:    Optional[Decimal]  = None
    credito_aplicado:  Optional[Decimal]  = None
    descuento_aplicado: Optional[Decimal] = None
    Estado:            Optional[int]      = None
    estado_label:      Optional[str]      = None
    Metodo_Pago:       Optional[str]      = None
    Fecha_pedido:      Optional[datetime] = None
    productos:         list              = []
    tiene_domicilio:   bool              = False
    ID_Domicilio:      Optional[int]     = None

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class PedidoListResponse(BaseModel):
    total:      int
    pagina:     int
    por_pagina: int
    pedidos:    list[PedidoResponse]