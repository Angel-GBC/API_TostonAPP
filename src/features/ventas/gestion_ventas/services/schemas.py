from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ── Producto dentro de una venta ──
class ProductoVentaInput(BaseModel):
    ID_Producto: int
    Cantidad:    int


# ── Domicilio opcional al crear venta ──
class DomicilioVentaInput(BaseModel):
    Direccion_entrega:    str
    Municipio_entrega:    str
    Departamento_entrega: str
    Observaciones:        Optional[str]      = None
    Fecha_entrega:        Optional[datetime] = None
    ID_Empleado:          Optional[int]      = None  # repartidor


# ── Crear venta ──
class VentaCreate(BaseModel):
    ID_Usuario:    int
    Metodo_Pago:   str                              # "Efectivo", "Transferencia", "Contra entrega"
    A_Nombre_De:   Optional[str]       = None       # para el detalle de venta
    productos:     list[ProductoVentaInput]
    codigo_descuento: Optional[str]    = None       # cupón ingresado por el cliente
    usar_credito:  bool                = False      # si el cliente quiere usar su saldo
    domicilio:     Optional[DomicilioVentaInput] = None


# ── Cambiar estado de venta ──
class VentaEstado(BaseModel):
    Estado: int


# ── Respuesta de producto en venta ──
class ProductoVentaResponse(BaseModel):
    ID_Producto:     int
    nombre_producto: Optional[str]    = None
    Cantidad:        int
    precio_unitario: Optional[Decimal] = None
    subtotal:        Optional[Decimal] = None


# ── Respuesta de una venta ──
class VentaResponse(BaseModel):
    ID_Venta:          int
    ID_Usuario:        Optional[int]      = None
    nombre_cliente:    Optional[str]      = None
    Total:             Optional[Decimal]  = None
    subtotal_bruto:    Optional[Decimal]  = None    # antes de crédito y descuento
    credito_aplicado:  Optional[Decimal]  = None
    descuento_aplicado: Optional[Decimal] = None
    Estado:            Optional[int]      = None
    estado_label:      Optional[str]      = None
    Metodo_Pago:       Optional[str]      = None
    Fecha_Venta:       Optional[datetime] = None
    Fecha_pedido:      Optional[datetime] = None
    productos:         list[ProductoVentaResponse] = []
    tiene_domicilio:   bool               = False
    ID_Domicilio:      Optional[int]      = None

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class VentaListResponse(BaseModel):
    total:      int
    pagina:     int
    por_pagina: int
    ventas:     list[VentaResponse]