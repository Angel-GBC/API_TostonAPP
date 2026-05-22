# TostonApp API — CLAUDE.md

Guía de contexto para Claude Code. Léela completa antes de tocar cualquier archivo.

---

## Stack

- Python 3.11 + FastAPI + SQLAlchemy ORM
- MySQL en Aiven.io (plan gratuito — se apaga solo, reactivar manualmente si hay errores de conexión)
- Deploy en Render.com (plan gratuito — se duerme tras 15 min de inactividad)
- Auth: JWT con python-jose + passlib[bcrypt==4.0.1]
- Docs: Swagger en /docs con HTTPBearer
- Prefijo global de rutas: `/api`

---

## Reglas inamovibles

- **NO actualizar bcrypt** — está fijado en 4.0.1 en requirements.txt, versiones superiores rompen el hashing
- **NO usar `solo_empleados()`** en routers nuevos — está deprecado, usar siempre `requiere_permiso("nombre_permiso")`
- **NO crear permisos `gestionar_X`** — solo existen `ver_`, `crear_`, `editar_`, `eliminar_`, algunos modulos pueden tener otros privilegios o menos
- **NO tocar el módulo `configuracion/descuentos`** — postergado para una fase futura
- **NO hardcodear contraseñas ni secrets** — usar variables de entorno via `python-dotenv`
- **CORS**: URL del frontend: https://frontend-ten-xi-31.vercel.app/

---

## Estructura de carpetas

```
raíz/
├── main.py               ← punto de entrada, NO está en src/
├── seed.py               ← rehashea Admin123@ para todos los usuarios en cada deploy
├── reset_transaccional.py
├── requirements.txt
└── src/
    ├── main.py           ← este NO se usa, el real es el de la raíz
    ├── shared/services/
    │   ├── database.py   ← SessionLocal, get_db
    │   ├── models.py     ← TODOS los modelos SQLAlchemy aquí
    │   └── dependencies.py  ← VACÍO intencionalmente
    └── features/
        ├── auth/services/
        │   ├── router.py
        │   ├── service.py
        │   ├── schemas.py
        │   └── dependencies.py  ← obtener_usuario_actual, requiere_permiso, solo_empleados
        ├── configuracion/
        │   ├── control_acceso/services/   ← módulo existente, no modificar sin consultar
        │   ├── roles/services/
        │   ├── usuarios/services/
        │   ├── notificaciones/services/
        │   └── descuentos/services/       ← POSTERGADO, no tocar
        ├── compras/
        │   ├── insumos/services/
        │   ├── categoria_insumos/services/
        │   └── proveedores/services/
        ├── produccion/
        │   ├── productos/services/
        │   ├── categoria_productos/services/
        │   └── ordenes_produccion/services/
        ├── ventas/
        │   ├── clientes/services/
        │   ├── pedidos/services/
        │   ├── gestion_ventas/services/
        │   ├── devoluciones/services/
        │   └── domicilios/services/
        └── dashboard/services/
```

Cada módulo tiene: `router.py`, `service.py`, `schemas.py`.

---

## Autenticación y permisos

### Dónde viven las dependencias
```
src/features/auth/services/dependencies.py
```
Contiene: `obtener_usuario_actual`, `requiere_permiso()`, `solo_empleados()`.  
`src/shared/services/dependencies.py` está vacío intencionalmente — no mover nada ahí.

### Roles
| ID | Nombre | Permisos |
|----|--------|----------|
| 1 | Admin | Todos — bypass total, no verificar permisos |
| 2 | Empleado | 25 permisos |
| 3 | Cliente | 6 permisos |
| 4 | Domiciliario | 3 permisos |

### Cómo se asigna el rol
- **Empleados**: campo `ID_Rol` directo en tabla `Empleados`
- **Clientes**: tabla `Usuario_x_Rol`
- Al registrarse un nuevo usuario → rol Cliente asignado automáticamente en `Usuario_x_Rol`

### Admin siempre tiene acceso total
```python
# En requiere_permiso(), el Admin hace bypass completo:
if id_rol == 1:
    return actual  # sin verificar Rol_x_Permiso
```

### Regla de permisos ver_
Si un rol tiene `editar_X` o `eliminar_X` pero NO `ver_X`, el sistema otorga `ver_X` automáticamente.

### Cómo proteger un endpoint
```python
# Correcto
from src.features.auth.services.dependencies import requiere_permiso

@router.get("/insumos")
def listar(_, db=Depends(get_db), actual=Depends(requiere_permiso("ver_insumos"))):
    ...

# Incorrecto — NO usar
from src.features.auth.services.dependencies import solo_empleados
```

---

## Base de datos

### Modelos críticos
- `Rol`: SIN columna `Fecha_creacion`. `Icono` es `VARCHAR(500)` — puede ser emoji o URL de Cloudinary
- `Usuario`: PK autoincremental (`ID_Usuario`). `Cedula`, `Telefono`, `Direccion`, `Municipio`, `Departamento`, `Foto_perfil` son opcionales (NULL)
- `Empleado`: PK autoincremental (`ID_Empleado`). Tiene `ID_Rol` directo
- `Domicilios.ID_Empleado` → apunta a `Empleados`, NO a `Usuarios`
- `Usuario_x_Rol`: asigna rol a clientes
- `CategoriaProducto.Icono`, `CategoriaInsumo.Icono`: `VARCHAR(500)` — emoji o URL
- `ProductoImagen.imagen`: `VARCHAR(500)` — URL de Cloudinary
- `Usuario.Foto_perfil`, `Empleado.Foto_perfil`: `VARCHAR(500)` — URL de Cloudinary

### Imágenes — Cloudinary
Los campos de imagen ya NO son LONGBLOB. Son `VARCHAR(500)` con una URL de Cloudinary o un emoji como string.
- El frontend sube la imagen directo a Cloudinary y solo envía la URL a la API
- La API guarda el string tal cual — sin conversión, sin base64
- Eliminar cualquier `base64.b64encode(...)` que quede en los services

```python
# Correcto
"icono": rol.Icono  # ya es string (emoji o URL)

# Incorrecto — eliminar si aparece
"icono": base64.b64encode(rol.Icono).decode() if rol.Icono else None
```

### Estados (tabla Estados)
```
1=Activo        2=Inactivo      3=Pendiente     4=Confirmado    5=Cancelado
6=Aprobada      7=Rechazada     8=Entregado     9=En camino     10=Asignado
11=Completada   12=Anulada      13=En proceso   14=Stock bajo   15=Agotado
```

### Estados automáticos de stock
```
Producto.Stock = 0              → Estado = 15 (Agotado)
0 < Stock <= Stock_Minimo       → Estado = 14 (Stock bajo)
Stock > Stock_Minimo            → Estado = 1  (Activo)

Insumo.Stock_Actual = 0         → Estado = 15 (Agotado)
0 < Stock_Actual <= Stock_Minimo → Estado = 14 (Stock bajo)
Stock_Actual > Stock_Minimo     → Estado = 1  (Activo)
```

---

## Reglas de negocio

- Si una venta incluye domicilio → el cliente DEBE tener `Telefono` en su perfil (validar antes de crear)
- Devolución aprobada → recargar crédito automáticamente en `CreditoCliente`
- Al completar una `OrdenProduccion` → incrementar `Stock` del `Producto`
- Al iniciar una `OrdenProduccion` → descontar `Stock_Actual` del `Insumo` usado, por eso es necesario que el producto tenga ficha tecnica
- Al confirmar una venta → descontar `Stock` del `Producto`
- Módulo Salidas (nuevo, aún no implementado): registra daños/vencimientos y descuenta stock directamente de `Insumos` o `Productos`
- Descuentos: postergados — no implementar
- Desactivar un rol causara que todos los usuarios con ese rol queden inactivos tambien
- Desactivar un categoria de insumo causara que todos sus insumos con esa categoria queden desactivados
- insumos provienen de compras de estado 11=`completadas`
- Desactivar un categoria de producto causara que todos sus productos con esa categoria queden desactivados

---

## Endpoints de Auth (todos implementados)

```
POST /api/auth/login                 Login unificado empleados y clientes
POST /api/auth/registro              Crea cliente (Nombre, Apellidos, Correo, Contrasena, Confirmar_contrasena)
POST /api/auth/recuperar-contrasena  Genera código 6 dígitos y lo envía al correo (Resend SMTP)
POST /api/auth/verificar-codigo      Valida código, retorna reset_token (10 min)
POST /api/auth/resetear-contrasena   Valida reset_token tipo="reset", actualiza contraseña
GET  /api/auth/me                    Perfil básico del usuario autenticado
GET  /api/auth/perfil                Perfil completo del cliente
PUT  /api/auth/perfil                Edita Telefono, Direccion, Municipio, Departamento
```

---

## Contexto del frontend (para saber qué debe devolver la API)

El frontend es React + Vite, desplegado en Vercel. La API debe estar lista para responder a tres tipos de usuario:

### 1. Invitado (sin sesión)
- Ve catálogo de productos públicamente → `GET /api/produccion/productos` debe funcionar sin token
- No puede confirmar pedidos

### 2. Cliente (rol ID=3)
- Confirma pedidos con: productos, dirección de entrega, método de pago (Transferencia/Efectivo), comprobante (URL Cloudinary si es transferencia), "A nombre de"
- Ve sus pedidos filtrados por estado
- Solicita devoluciones sobre pedidos entregados
- Edita su perfil (Telefono, Direccion, Municipio, Departamento, Foto_perfil)

### 3. Admin/Empleado/Otros
- Panel de gestión con sidebar dinámico según permisos
- El frontend consulta los permisos del usuario para mostrar/ocultar módulos
- Admin (ID=1) ve todo sin restricción

### Endpoint de permisos necesario para el sidebar
El frontend necesita saber qué permisos tiene el usuario autenticado. Verificar si existe un endpoint que los devuelva; si no existe, hay que crearlo:
```
GET /api/auth/mis-permisos   → retorna lista de nombres de permisos del usuario actual
```

---

## Convenciones de código

- Schemas: Pydantic v2 (`model_validator`, `model_dump`)
- Imports de dependencias siempre desde `src.features.auth.services.dependencies`
- Imports de modelos siempre desde `src.shared.services.models`
- Imports de DB siempre desde `src.shared.services.database`
- Contraseña universal de prueba: `Admin123@` (seed.py la aplica en cada deploy)
- Los errores de negocio van como `HTTPException`, no como excepciones genéricas

---

## Lo que NO está implementado aún

- `configuracion/salidas` — módulo nuevo para registrar daños/vencimientos (diseñar tabla SQL + modelo + CRUD)
- `GET /api/auth/mis-permisos` — verificar si existe, si no crearlo
- Foto de perfil: el campo existe en BD pero el endpoint PUT /auth/perfil puede no aceptarla aún
- Cambio de contraseña estando autenticado

---

## Antes de hacer cualquier cambio

1. Leer el archivo relevante completo antes de editarlo
2. Pedir `models.py` si vas a tocar lógica de BD
3. No asumir que un campo es NOT NULL — revisar el modelo
4. Si el cambio afecta stock, permisos o roles → revisar las reglas de negocio de este archivo primero
