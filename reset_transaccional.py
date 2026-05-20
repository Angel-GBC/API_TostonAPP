"""
reset_transaccional.py
======================
Limpia todos los datos transaccionales (ventas, domicilios, pedidos,
devoluciones) y deja intacto el catálogo (usuarios, productos, roles, etc.).

Ejecutar con:
    python reset_transaccional.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from src.shared.services.database import SessionLocal
from src.shared.services.models import (
    DevolucionDetalle, MovimientoCredito, Devolucion,
    DescuentoXVenta, DescuentoXUsuario, Descuento,
    Domicilio, DetalleVenta, VentaXProducto, Venta,
    CreditoCliente, Producto,
)


def reset():
    db = SessionLocal()
    try:
        # ── 1. Restaurar stock de productos ──────────────────────────────────
        # Suma las cantidades de ventas NO canceladas (estados 3 y 5 ya
        # tuvieron su stock restaurado en el momento de cancelación).
        ESTADOS_CANCELADOS = {3, 5}
        ventas_activas = db.query(Venta).filter(
            Venta.Estado.notin_(ESTADOS_CANCELADOS)
        ).all()
        ids_activas = {v.ID_Venta for v in ventas_activas}

        items = db.query(VentaXProducto).filter(
            VentaXProducto.ID_Venta.in_(ids_activas)
        ).all() if ids_activas else []

        restaurados = {}
        for item in items:
            restaurados[item.ID_Producto] = (
                restaurados.get(item.ID_Producto, 0) + item.Cantidad
            )

        for id_producto, cantidad in restaurados.items():
            producto = db.query(Producto).filter(
                Producto.ID_Producto == id_producto
            ).first()
            if producto:
                producto.Stock += cantidad

        print(f"✅ Stock restaurado para {len(restaurados)} producto(s)")

        # ── 2. Borrar en orden de dependencias FK ─────────────────────────
        n = db.query(DevolucionDetalle).delete()
        print(f"🗑  DevolucionDetalle:  {n} fila(s)")

        n = db.query(MovimientoCredito).delete()
        print(f"🗑  MovimientoCredito:  {n} fila(s)")

        n = db.query(Devolucion).delete()
        print(f"🗑  Devoluciones:       {n} fila(s)")

        n = db.query(DescuentoXVenta).delete()
        print(f"🗑  DescuentoXVenta:    {n} fila(s)")

        n = db.query(Domicilio).delete()
        print(f"🗑  Domicilios:         {n} fila(s)")

        n = db.query(DetalleVenta).delete()
        print(f"🗑  DetalleVenta:       {n} fila(s)")

        n = db.query(VentaXProducto).delete()
        print(f"🗑  VentaXProducto:     {n} fila(s)")

        n = db.query(Venta).delete()
        print(f"🗑  Ventas:             {n} fila(s)")

        # ── 3. Resetear créditos de clientes a 0 ─────────────────────────
        n = db.query(CreditoCliente).update(
            {"Saldo": Decimal("0"), "Fecha_Update": None}
        )
        print(f"💳 CreditoCliente reseteado: {n} registro(s)")

        # ── 4. Resetear contadores de usos de descuentos ──────────────────
        n = db.query(Descuento).update({"Usos_Actuales": 0})
        print(f"🎟  Descuentos (usos):  {n} cupón(es) reseteado(s)")

        n = db.query(DescuentoXUsuario).update({"Usado": False})
        print(f"🎟  DescuentoXUsuario:  {n} asignación(es) reseteada(s)")

        db.commit()
        print("\n✅ Base de datos transaccional limpiada correctamente.")
        print("   Usuarios, productos, roles y configuración intactos.")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    confirmar = input(
        "⚠️  Esto borrará TODAS las ventas, domicilios y devoluciones.\n"
        "   ¿Confirmas? (escribe 'si' para continuar): "
    )
    if confirmar.strip().lower() == "si":
        reset()
    else:
        print("Operación cancelada.")
