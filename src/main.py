from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Auth ──
from src.features.auth.services.router import router as auth_router

# ── Configuración ──
from src.features.configuracion.usuarios.services.router       import router as usuarios_router
from src.features.configuracion.roles.services.router          import router as roles_router
from src.features.configuracion.notificaciones.services.router import router as notificaciones_router
from src.features.configuracion.descuentos.services.router     import router as descuentos_router

# ── Compras ──
from src.features.compras.insumos.services.router           import router as insumos_router
from src.features.compras.categoria_insumos.services.router import router as cat_insumos_router
from src.features.compras.proveedores.services.router       import router as proveedores_router

# ── Producción ──
from src.features.produccion.productos.services.router           import router as productos_router
from src.features.produccion.categoria_productos.services.router import router as cat_productos_router
from src.features.produccion.ordenes_produccion.services.router  import router as ordenes_router

# ── Ventas ──
from src.features.ventas.clientes.services.router       import router as clientes_router
from src.features.ventas.pedidos.services.router        import router as pedidos_router
from src.features.ventas.gestion_ventas.services.router import router as ventas_router
from src.features.ventas.devoluciones.services.router   import router as devoluciones_router
from src.features.ventas.domicilios.services.router     import router as domicilios_router

# ── Dashboard ──
from src.features.dashboard.services.router import router as dashboard_router


app = FastAPI(
    title="API Proyecto",
    version="1.0.0",
    description="API para gestión de producción y ventas"
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registro de routers ──
PREFIX = "/api"

app.include_router(auth_router,          prefix=PREFIX)
app.include_router(usuarios_router,      prefix=PREFIX)
app.include_router(roles_router,         prefix=PREFIX)
app.include_router(notificaciones_router, prefix=PREFIX)
app.include_router(descuentos_router,    prefix=PREFIX)
app.include_router(insumos_router,       prefix=PREFIX)
app.include_router(cat_insumos_router,   prefix=PREFIX)
app.include_router(proveedores_router,   prefix=PREFIX)
app.include_router(productos_router,     prefix=PREFIX)
app.include_router(cat_productos_router, prefix=PREFIX)
app.include_router(ordenes_router,       prefix=PREFIX)
app.include_router(clientes_router,      prefix=PREFIX)
app.include_router(pedidos_router,       prefix=PREFIX)
app.include_router(ventas_router,        prefix=PREFIX)
app.include_router(devoluciones_router,  prefix=PREFIX)
app.include_router(domicilios_router,    prefix=PREFIX)
app.include_router(dashboard_router,     prefix=PREFIX)


@app.get("/")
def root():
    return {"mensaje": "API funcionando ✅"}

