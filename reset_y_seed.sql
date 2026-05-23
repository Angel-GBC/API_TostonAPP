-- ============================================================
-- reset_y_seed.sql
-- Limpia TODA la base de datos y siembra datos de ejemplo.
--
-- ANTES DE EJECUTAR:
--   1. Corre en la terminal del proyecto (venv activado):
--        python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('Admin123@'))"
--   2. Copia el hash resultante ($2b$12$...)
--   3. En Workbench haz Ctrl+H y reemplaza HASH_AQUI por ese hash
--   4. Ejecuta este script completo
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ── LIMPIEZA TOTAL ────────────────────────────────────────
TRUNCATE TABLE Notificaciones;
TRUNCATE TABLE Salidas;
TRUNCATE TABLE Devolucion_Detalle;
TRUNCATE TABLE Movimiento_Credito;
TRUNCATE TABLE Devoluciones;
TRUNCATE TABLE Descuento_x_Venta;
TRUNCATE TABLE Descuento_x_Usuario;
TRUNCATE TABLE Descuentos;
TRUNCATE TABLE Domicilios;
TRUNCATE TABLE Detalle_Venta;
TRUNCATE TABLE Venta_x_Producto;
TRUNCATE TABLE Ventas;
TRUNCATE TABLE Credito_Cliente;
TRUNCATE TABLE Orden_Produccion;
TRUNCATE TABLE Ficha_Tecnica;
TRUNCATE TABLE Detalle_Compra;
TRUNCATE TABLE Lote_Compra;
TRUNCATE TABLE Compras;
TRUNCATE TABLE Lote_Insumos;
TRUNCATE TABLE Insumos;
TRUNCATE TABLE Producto_Imagenes;
TRUNCATE TABLE Productos;
TRUNCATE TABLE Categoria_Producto;
TRUNCATE TABLE Categoria_Insumos;
TRUNCATE TABLE Proveedores;
TRUNCATE TABLE Sujeto_Derecho;
TRUNCATE TABLE Unidad_Medida;
TRUNCATE TABLE Usuario_x_Rol;
TRUNCATE TABLE Rol_x_Permiso;
TRUNCATE TABLE Empleados;
TRUNCATE TABLE Usuarios;
TRUNCATE TABLE Permisos;
TRUNCATE TABLE Roles;
TRUNCATE TABLE Estados;

SET FOREIGN_KEY_CHECKS = 1;

-- ── ESTADOS ───────────────────────────────────────────────
INSERT INTO Estados (ID_Estados, Codigo, Estado) VALUES
(1,  1,  'Activo'),
(2,  2,  'Inactivo'),
(3,  3,  'Pendiente'),
(4,  4,  'Confirmado'),
(5,  5,  'Cancelado'),
(6,  6,  'Aprobada'),
(7,  7,  'Rechazada'),
(8,  8,  'Entregado'),
(9,  9,  'En camino'),
(10, 10, 'Asignado'),
(11, 11, 'Completada'),
(12, 12, 'Anulada'),
(13, 13, 'En proceso'),
(14, 14, 'Stock bajo'),
(15, 15, 'Agotado');

-- ── UNIDADES DE MEDIDA ────────────────────────────────────
INSERT INTO Unidad_Medida (ID_Unidad_Medida, Simbolo, Unidad_Medida) VALUES
(1, 'kg', 'Kilogramo'),
(2, 'g',  'Gramo'),
(3, 'L',  'Litro'),
(4, 'mL', 'Mililitro'),
(5, 'u',  'Unidad'),
(6, 'lb', 'Libra');

-- ── SUJETO DE DERECHO ─────────────────────────────────────
INSERT INTO Sujeto_Derecho (ID_Sujeto_Derecho, Sujeto_Derecho) VALUES
(1, 'Natural'),
(2, 'Jurídico');

-- ── ROLES ─────────────────────────────────────────────────
INSERT INTO Roles (ID_Rol, Rol, Estado, Icono) VALUES
(1, 'Admin',        1, NULL),
(2, 'Empleado',     1, NULL),
(3, 'Cliente',      1, NULL),
(4, 'Domiciliario', 1, NULL);

-- ── PERMISOS (59) ─────────────────────────────────────────
INSERT INTO Permisos (ID_Permiso, Permiso, Descripcion) VALUES
(1,  'ver_dashboard',             'Ver el panel de métricas y estadísticas'),
(2,  'ver_roles',                 'Ver listado y detalle de roles'),
(3,  'crear_roles',               'Crear nuevos roles'),
(4,  'editar_roles',              'Editar roles y asignar permisos'),
(5,  'eliminar_roles',            'Eliminar roles'),
(6,  'ver_usuarios',              'Ver listado y detalle de usuarios'),
(7,  'crear_usuarios',            'Crear nuevos usuarios'),
(8,  'editar_usuarios',           'Editar información de usuarios'),
(9,  'eliminar_usuarios',         'Eliminar usuarios'),
(10, 'ver_salidas',               'Ver listado y detalle de salidas de inventario'),
(11, 'crear_salidas',             'Registrar nuevas salidas'),
(12, 'editar_salidas',            'Editar salidas registradas'),
(13, 'eliminar_salidas',          'Eliminar salidas'),
(14, 'ver_cat_insumos',           'Ver categorías de insumos'),
(15, 'crear_cat_insumos',         'Crear categorías de insumos'),
(16, 'editar_cat_insumos',        'Editar categorías de insumos'),
(17, 'eliminar_cat_insumos',      'Eliminar categorías de insumos'),
(18, 'ver_insumos',               'Ver listado y detalle de insumos'),
(19, 'crear_insumos',             'Crear nuevos insumos'),
(20, 'editar_insumos',            'Editar insumos'),
(21, 'eliminar_insumos',          'Eliminar insumos'),
(22, 'generar_salida_insumo',     'Generar una salida directa desde un insumo'),
(23, 'ver_proveedores',           'Ver listado y detalle de proveedores'),
(24, 'crear_proveedores',         'Crear nuevos proveedores'),
(25, 'editar_proveedores',        'Editar proveedores'),
(26, 'eliminar_proveedores',      'Eliminar proveedores'),
(27, 'ver_compras',               'Ver listado y detalle de compras'),
(28, 'crear_compras',             'Registrar nuevas compras'),
(29, 'editar_compras',            'Editar compras'),
(30, 'anular_compras',            'Anular compras (cambia estado, no elimina)'),
(31, 'ver_cat_productos',         'Ver categorías de productos'),
(32, 'crear_cat_productos',       'Crear categorías de productos'),
(33, 'editar_cat_productos',      'Editar categorías de productos'),
(34, 'eliminar_cat_productos',    'Eliminar categorías de productos'),
(35, 'ver_productos',             'Ver listado y detalle de productos'),
(36, 'crear_productos',           'Crear nuevos productos'),
(37, 'editar_productos',          'Editar productos'),
(38, 'eliminar_productos',        'Eliminar productos'),
(39, 'generar_salida_producto',   'Generar una salida directa desde un producto'),
(40, 'ver_ordenes',               'Ver listado y detalle de órdenes de producción'),
(41, 'crear_ordenes',             'Crear nuevas órdenes de producción'),
(42, 'editar_ordenes',            'Editar órdenes de producción'),
(43, 'eliminar_ordenes',          'Eliminar órdenes de producción'),
(44, 'ver_pedidos',               'Ver listado y detalle de pedidos'),
(45, 'crear_pedidos',             'Crear nuevos pedidos'),
(46, 'editar_pedidos',            'Editar pedidos'),
(47, 'eliminar_pedidos',          'Eliminar pedidos'),
(48, 'ver_ventas',                'Ver listado y detalle de ventas'),
(49, 'crear_ventas',              'Registrar nuevas ventas'),
(50, 'editar_ventas',             'Editar ventas'),
(51, 'eliminar_ventas',           'Eliminar ventas'),
(52, 'ver_devoluciones',          'Ver listado y detalle de devoluciones'),
(53, 'crear_devoluciones',        'Registrar nuevas devoluciones'),
(54, 'editar_devoluciones',       'Editar devoluciones'),
(55, 'eliminar_devoluciones',     'Eliminar devoluciones'),
(56, 'aprobar_devoluciones',      'Aprobar o desaprobar solicitudes de devolución'),
(57, 'ver_domicilios',            'Ver listado de domicilios'),
(58, 'ver_detalle_domicilios',    'Ver el detalle completo de un domicilio'),
(59, 'cambiar_estado_domicilios', 'Cambiar el estado de un domicilio');

-- ── ROL X PERMISO ─────────────────────────────────────────
-- Empleado: 25 permisos
INSERT INTO Rol_x_Permiso (ID_Rol, ID_Permiso) VALUES
(2, 1),(2, 10),(2, 11),(2, 13),(2, 14),
(2, 18),(2, 19),(2, 20),(2, 22),(2, 23),
(2, 25),(2, 27),(2, 28),(2, 31),(2, 35),
(2, 36),(2, 37),(2, 40),(2, 41),(2, 42),
(2, 44),(2, 48),(2, 52),(2, 56),(2, 57);

-- Cliente: 6 permisos
INSERT INTO Rol_x_Permiso (ID_Rol, ID_Permiso) VALUES
(3, 35),(3, 44),(3, 45),(3, 48),(3, 52),(3, 53);

-- Domiciliario: 3 permisos
INSERT INTO Rol_x_Permiso (ID_Rol, ID_Permiso) VALUES
(4, 57),(4, 58),(4, 59);

-- ── EMPLEADOS ─────────────────────────────────────────────
-- contraseña: Admin123@  →  reemplazar HASH_AQUI con el hash bcrypt
INSERT INTO Empleados
  (ID_Rol, Nombre, Apellidos, Correo, Cedula, Tipo_Documento,
   Direccion, Municipio, Departamento, Telefono,
   Contrasena, Foto_perfil, Fecha_creacion, Estado)
VALUES
(1, 'Juan',   'Pérez García',  'admin@tostonapp.com',
 '10200300', 'CC', 'Calle 10 # 5-20',     'Medellín', 'Antioquia', '3001234567',
 'HASH_AQUI', NULL, NOW(), 1),

(2, 'Carlos', 'Ruiz López',    'empleado@tostonapp.com',
 '10400500', 'CC', 'Carrera 45 # 12-30',  'Medellín', 'Antioquia', '3109876543',
 'HASH_AQUI', NULL, NOW(), 1),

(4, 'Miguel', 'Torres Ríos',   'domiciliario@tostonapp.com',
 '10600700', 'CC', 'Circular 75 # 40-15', 'Medellín', 'Antioquia', '3204561230',
 'HASH_AQUI', NULL, NOW(), 1);

-- ── USUARIOS / CLIENTES ───────────────────────────────────
INSERT INTO Usuarios
  (Nombre, Apellidos, Correo, Cedula, Tipo_Documento,
   Direccion, Municipio, Departamento, Telefono,
   Contrasena, Foto_perfil, Fecha_creacion, Estado)
VALUES
('María',  'López Herrera', 'cliente1@tostonapp.com',
 '20300400', 'CC', 'Calle 50 # 70-90',   'Medellín', 'Antioquia', '3151112233',
 'HASH_AQUI', NULL, NOW(), 1),

('Andrés', 'Castro Gómez',  'cliente2@tostonapp.com',
 '30400500', 'CC', 'Avenida 33 # 81-20', 'Medellín', 'Antioquia', '3003334455',
 'HASH_AQUI', NULL, NOW(), 1);

-- ── USUARIO X ROL (asignar rol Cliente a todos los Usuarios) ──
INSERT INTO Usuario_x_Rol (ID_Rol, ID_Usuario)
SELECT 3, ID_Usuario FROM Usuarios;

-- ── CRÉDITO CLIENTE ───────────────────────────────────────
INSERT INTO Credito_Cliente (ID_Usuario, Saldo, Fecha_Update)
SELECT ID_Usuario, 0.00, NOW() FROM Usuarios;

-- ── CATEGORÍAS DE INSUMOS ─────────────────────────────────
INSERT INTO Categoria_Insumos
  (ID_Categoria, Nombre_Categoria, Descripcion, Estado, Icono, Fecha_Creacion)
VALUES
(1, 'Frutas y Verduras',      'Materia prima vegetal y frutal',        1, '🌿', NOW()),
(2, 'Aceites y Grasas',       'Aceites vegetales y grasas de cocción', 1, '🫙', NOW()),
(3, 'Condimentos y Especias', 'Sal, ajo, especias y sazonadores',      1, '🧂', NOW()),
(4, 'Empaque y Envases',      'Materiales de empaque y presentación',  1, '📦', NOW());

-- ── CATEGORÍAS DE PRODUCTOS ───────────────────────────────
INSERT INTO Categoria_Producto
  (ID_Categoria, Nombre_Categoria, Descripcion, Estado, Icono, Fecha_Creacion)
VALUES
(1, 'Tostones', 'Productos a base de plátano frito',     1, '🍌', NOW()),
(2, 'Combos',   'Porciones combinadas con acompañantes', 1, '🍱', NOW()),
(3, 'Salsas',   'Salsas y aderezos artesanales',         1, '🥣', NOW());

-- ── PROVEEDORES ───────────────────────────────────────────
INSERT INTO Proveedores
  (ID_Proveedor, Sujeto_Derecho, Responsable,
   Direccion, Municipio, Departamento, Telefono, Correo)
VALUES
(1, 2, 'Distribuidora El Campo',
 'Cra 80 # 30-15', 'Medellín', 'Antioquia', '3207891234', 'campo@distribuidora.com'),
(2, 2, 'Oleoproductos S.A.',
 'Cll 12 # 43-20', 'Medellín', 'Antioquia', '3116543210', 'ventas@oleoproductos.com'),
(3, 2, 'Empaques del Norte S.A.S.',
 'Cra 50 # 10-40', 'Bello',    'Antioquia', '6049876543', 'info@empaques.com');

-- ── INSUMOS (se crean sin lote; se actualizan después) ────
INSERT INTO Insumos
  (ID_Insumo, Nombre, ID_Categoria, Unidad_Medida,
   Stock_Actual, Stock_Minimo, ID_Lote_Compra, Estado)
VALUES
(1, 'Plátano Verde',       1, 1,    0,  10, NULL, 15),
(2, 'Aceite de Girasol',   2, 3,    0,   5, NULL, 15),
(3, 'Sal Marina',          3, 2,    0, 500, NULL, 15),
(4, 'Ajo en Polvo',        3, 2,    0, 200, NULL, 15),
(5, 'Papel Encerado',      4, 5,    0, 100, NULL, 15),
(6, 'Bolsas Compostables', 4, 5,    0,  50, NULL, 15);

-- ── COMPRA 1 — Distribuidora El Campo ─────────────────────
-- Plátano $75.000 + Sal $10.000 + Ajo $50.000 = $135.000
INSERT INTO Compras
  (ID_Compra, ID_Proveedor, Total_Pago, Fecha_Compra, Estado, Metodo_Pago)
VALUES (1, 1, 135000.00, DATE_SUB(NOW(), INTERVAL 15 DAY), 4, 'Transferencia');

INSERT INTO Lote_Compra
  (ID_Lote_Compra, ID_Insumo, Fecha_Vencimiento, Cantidad_Inicial, Estado)
VALUES
(1, 1, DATE_ADD(NOW(), INTERVAL  20 DAY), 50,   1),
(2, 3, DATE_ADD(NOW(), INTERVAL 365 DAY), 5000, 1),
(3, 4, DATE_ADD(NOW(), INTERVAL 365 DAY), 2000, 1);

INSERT INTO Detalle_Compra
  (ID_Compra, ID_Insumo, ID_Lote_Compra, Cantidad, Precio_Und, Notas)
VALUES
(1, 1, 1, 50,   1500.00, NULL),
(1, 3, 2, 5000,    2.00, NULL),
(1, 4, 3, 2000,   25.00, NULL);

-- ── COMPRA 2 — Oleoproductos ──────────────────────────────
-- Aceite 30L × $8.000 = $240.000
INSERT INTO Compras
  (ID_Compra, ID_Proveedor, Total_Pago, Fecha_Compra, Estado, Metodo_Pago)
VALUES (2, 2, 240000.00, DATE_SUB(NOW(), INTERVAL 10 DAY), 4, 'Efectivo');

INSERT INTO Lote_Compra
  (ID_Lote_Compra, ID_Insumo, Fecha_Vencimiento, Cantidad_Inicial, Estado)
VALUES (4, 2, DATE_ADD(NOW(), INTERVAL 180 DAY), 30, 1);

INSERT INTO Detalle_Compra
  (ID_Compra, ID_Insumo, ID_Lote_Compra, Cantidad, Precio_Und, Notas)
VALUES (2, 2, 4, 30, 8000.00, NULL);

-- ── COMPRA 3 — Empaques del Norte ─────────────────────────
-- Papel 500u × $200 + Bolsas 45u × $500 = $122.500
INSERT INTO Compras
  (ID_Compra, ID_Proveedor, Total_Pago, Fecha_Compra, Estado, Metodo_Pago)
VALUES (3, 3, 122500.00, DATE_SUB(NOW(), INTERVAL 5 DAY), 4, 'Transferencia');

INSERT INTO Lote_Compra
  (ID_Lote_Compra, ID_Insumo, Fecha_Vencimiento, Cantidad_Inicial, Estado)
VALUES
(5, 5, DATE_ADD(NOW(), INTERVAL 730 DAY), 500, 1),
(6, 6, DATE_ADD(NOW(), INTERVAL 730 DAY),  45, 1);

INSERT INTO Detalle_Compra
  (ID_Compra, ID_Insumo, ID_Lote_Compra, Cantidad, Precio_Und, Notas)
VALUES
(3, 5, 5, 500, 200.00, NULL),
(3, 6, 6,  45, 500.00, NULL);

-- ── ACTUALIZAR STOCK E ID_LOTE EN CADA INSUMO ────────────
-- Plátano Verde:       50 kg   > min 10  → Activo
UPDATE Insumos SET Stock_Actual = 50,   ID_Lote_Compra = 1, Estado = 1  WHERE ID_Insumo = 1;
-- Aceite de Girasol:   30 L    > min 5   → Activo
UPDATE Insumos SET Stock_Actual = 30,   ID_Lote_Compra = 4, Estado = 1  WHERE ID_Insumo = 2;
-- Sal Marina:          5000 g  > min 500 → Activo
UPDATE Insumos SET Stock_Actual = 5000, ID_Lote_Compra = 2, Estado = 1  WHERE ID_Insumo = 3;
-- Ajo en Polvo:        2000 g  > min 200 → Activo
UPDATE Insumos SET Stock_Actual = 2000, ID_Lote_Compra = 3, Estado = 1  WHERE ID_Insumo = 4;
-- Papel Encerado:      500 u   > min 100 → Activo
UPDATE Insumos SET Stock_Actual = 500,  ID_Lote_Compra = 5, Estado = 1  WHERE ID_Insumo = 5;
-- Bolsas Compostables: 45 u   <= min 50  → Stock bajo
UPDATE Insumos SET Stock_Actual = 45,   ID_Lote_Compra = 6, Estado = 14 WHERE ID_Insumo = 6;

-- ── PRODUCTOS ─────────────────────────────────────────────
INSERT INTO Productos
  (ID_Producto, nombre, ID_Categoria, Precio_venta,
   Stock, Stock_Minimo, Estado, ID_Orden_Produccion, Imagen)
VALUES
(1, 'Tostones Clásicos', 1, 8000.00,  30, 10, 1, NULL, NULL),
(2, 'Tostones con Ajo',  1, 9500.00,  20,  8, 1, NULL, NULL),
(3, 'Combo Familiar',    2, 22000.00, 10,  5, 1, NULL, NULL),
(4, 'Salsa Hogao',       3, 5000.00,  25, 10, 1, NULL, NULL);

-- ── FICHAS TÉCNICAS ───────────────────────────────────────
INSERT INTO Ficha_Tecnica
  (ID_Producto, ID_Categoria, Version, Estado, Observaciones, Procedimiento, Fecha_Creacion)
VALUES
(1, 1, '1.0', 1,
 'Usar plátano verde firme. Temperatura crítica para textura crocante.',
 '1. Pelar plátano verde y cortar en rodajas de 2 cm.\n2. Freír en aceite a 160°C durante 3 min.\n3. Retirar y aplanar con tostonera.\n4. Volver al aceite a 180°C por 2 min adicionales.\n5. Escurrir sobre papel absorbente y salar al gusto.\n6. Empacar en bolsa compostable.',
 NOW()),

(2, 1, '1.0', 1,
 'No exceder 5 g de ajo por porción. Revisar alergia en clientes.',
 '1. Seguir pasos 1-5 de Tostones Clásicos.\n2. Mezclar con 3 g de ajo en polvo por porción mientras están calientes.\n3. Empacar en bolsa compostable.',
 NOW()),

(3, 2, '1.0', 1,
 'Para 3-4 personas. Verificar disponibilidad de salsa antes de armar.',
 '1. Preparar 2 porciones de Tostones Clásicos (ver ficha).\n2. Preparar 1 porción de Salsa Hogao (ver ficha).\n3. Empacar en caja ecológica con servilletas.',
 NOW()),

(4, 3, '1.0', 1,
 'Vida útil refrigerada: 5 días. No congelar.',
 '1. Sofreír 100 g de tomate y cebolla picados en 10 mL aceite.\n2. Agregar sal y ajo al gusto.\n3. Cocinar 15 min a fuego medio, revolver ocasionalmente.\n4. Envasar en recipiente hermético y refrigerar.',
 NOW());

-- ── VERIFICACIÓN FINAL ────────────────────────────────────
SELECT 'Estados'          AS Tabla, COUNT(*) AS Filas FROM Estados
UNION ALL SELECT 'Roles',        COUNT(*) FROM Roles
UNION ALL SELECT 'Permisos',     COUNT(*) FROM Permisos
UNION ALL SELECT 'Empleados',    COUNT(*) FROM Empleados
UNION ALL SELECT 'Usuarios',     COUNT(*) FROM Usuarios
UNION ALL SELECT 'Insumos',      COUNT(*) FROM Insumos
UNION ALL SELECT 'Compras',      COUNT(*) FROM Compras
UNION ALL SELECT 'Lote_Compra',  COUNT(*) FROM Lote_Compra
UNION ALL SELECT 'Productos',    COUNT(*) FROM Productos
UNION ALL SELECT 'Ficha_Tecnica',COUNT(*) FROM Ficha_Tecnica;
