from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


# ── Filtro de período ──
# "hoy", "semana", "mes"
class PeriodoFiltro(BaseModel):
    periodo: str = "hoy"


# ── Tarjetas del resumen general ──
class TarjetaResumen(BaseModel):
    valor:            Decimal
    variacion_pct:    Optional[float] = None    # ej: 12.0 = +12%
    subiendo:         bool            = True    # True = verde, False = rojo


class ResumenGeneral(BaseModel):
    total_ventas:    TarjetaResumen
    total_pedidos:   TarjetaResumen
    total_clientes:  TarjetaResumen
    ticket_promedio: TarjetaResumen


# ── Punto en la gráfica de ventas en el tiempo ──
class PuntoGrafica(BaseModel):
    etiqueta:  str              # "8am", "Lun", "Ene 1"
    actual:    Decimal
    anterior:  Optional[Decimal] = None
    meta:      Optional[Decimal] = None


# ── Producto en el ranking / gráfica de torta ──
class ProductoRanking(BaseModel):
    ID_Producto:  int
    nombre:       str
    cantidad:     int
    porcentaje:   float


# ── Respuesta completa del dashboard ──
class DashboardResponse(BaseModel):
    periodo:          str
    resumen:          ResumenGeneral
    grafica_ventas:   list[PuntoGrafica]        # gráfica de barras/líneas
    productos_top:    list[ProductoRanking]     # torta + ranking lateral