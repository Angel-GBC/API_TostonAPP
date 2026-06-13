from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from .database import Base


# ─────────────────────────────────────────
# ESTADOS
# ─────────────────────────────────────────

class Estado(Base):
    __tablename__ = "Estados"

    ID_Estados = Column(Integer, primary_key=True, index=True)
    Codigo     = Column(Integer)
    Estado     = Column(String(25))


# ─────────────────────────────────────────
# ROLES Y PERMISOS
# ─────────────────────────────────────────

class Rol(Base):
    __tablename__ = "Roles"

    ID_Rol = Column(Integer, primary_key=True, index=True)
    Rol    = Column(String(25))
    Estado = Column(Integer, ForeignKey("Estados.ID_Estados"))
    Icono = Column(String(500), nullable=True)

    empleados = relationship("Empleado", back_populates="rol")
    permisos  = relationship("RolXPermiso", back_populates="rol")
    usuarios  = relationship("UsuarioXRol", back_populates="rol")


class Permiso(Base):
    __tablename__ = "Permisos"

    ID_Permiso  = Column(Integer, primary_key=True, index=True)
    Permiso     = Column(String(25))
    Descripcion = Column(Text)

    roles = relationship("RolXPermiso", back_populates="permiso")


class RolXPermiso(Base):
    __tablename__ = "Rol_x_Permiso"

    ID_Rol     = Column(Integer, ForeignKey("Roles.ID_Rol"), primary_key=True)
    ID_Permiso = Column(Integer, ForeignKey("Permisos.ID_Permiso"), primary_key=True)

    rol     = relationship("Rol", back_populates="permisos")
    permiso = relationship("Permiso", back_populates="roles")


# ─────────────────────────────────────────
# USUARIOS Y EMPLEADOS
# ─────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "Usuarios"

    ID_Usuario     = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ← PK autoincremental
    Cedula         = Column(String(20), nullable=True)                                   # ← campo normal
    Tipo_Documento = Column(String(5), nullable=True)                                    # ← CC, CE, NIT, etc.
    Nombre         = Column(String(50))
    Apellidos      = Column(String(50))
    Correo         = Column(String(255), unique=True, index=True)
    Direccion      = Column(String(50))
    Municipio      = Column(String(25))
    Departamento   = Column(String(60))
    Telefono       = Column(String(20))
    Foto_perfil    = Column(String(500), nullable=True)
    Fecha_creacion = Column(DateTime)
    Contrasena     = Column(String(255))
    Estado         = Column(Integer, ForeignKey("Estados.ID_Estados"))

    roles        = relationship("UsuarioXRol", back_populates="usuario")
    ventas       = relationship("Venta", back_populates="usuario")
    devoluciones = relationship("Devolucion", back_populates="usuario")


class Empleado(Base):
    __tablename__ = "Empleados"

    ID_Empleado    = Column(Integer, primary_key=True, index=True, autoincrement=True)   # ← PK autoincremental
    Cedula         = Column(String(20), nullable=True)                                    # ← campo normal
    Tipo_Documento = Column(String(5), nullable=True)                                     # ← CC, CE, NIT, etc.
    ID_Rol         = Column(Integer, ForeignKey("Roles.ID_Rol"))
    Nombre         = Column(String(50))
    Apellidos      = Column(String(50))
    Correo         = Column(String(255), unique=True, index=True)
    Direccion      = Column(String(50))
    Municipio      = Column(String(25))
    Departamento   = Column(String(60))
    Telefono       = Column(String(20))
    Foto_perfil    = Column(String(500), nullable=True)
    Fecha_creacion = Column(DateTime)
    Contrasena     = Column(String(255))
    Estado         = Column(Integer, ForeignKey("Estados.ID_Estados"))

    rol = relationship("Rol", back_populates="empleados")
    domicilios = relationship("Domicilio", back_populates="empleado")


class UsuarioXRol(Base):
    __tablename__ = "Usuario_x_Rol"

    ID_Rol     = Column(Integer, ForeignKey("Roles.ID_Rol"), primary_key=True)
    ID_Usuario = Column(Integer, ForeignKey("Usuarios.ID_Usuario"), primary_key=True)   # ← actualizado

    rol     = relationship("Rol", back_populates="usuarios")
    usuario = relationship("Usuario", back_populates="roles")


class VerificacionEmail(Base):
    __tablename__ = "Verificaciones_Email"

    ID_Verificacion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ID_Usuario      = Column(Integer, ForeignKey("Usuarios.ID_Usuario"))
    Token           = Column(String(36), unique=True, index=True)
    Expira_En       = Column(DateTime)
    Usado           = Column(Boolean, default=False)

    usuario = relationship("Usuario", foreign_keys=[ID_Usuario])


# ─────────────────────────────────────────
# CATEGORIAS
# ─────────────────────────────────────────

class CategoriaProducto(Base):
    __tablename__ = "Categoria_Producto"

    ID_Categoria     = Column(Integer, primary_key=True, index=True)
    Nombre_Categoria = Column(String(100))
    Descripcion      = Column(Text)
    Estado           = Column(Integer, ForeignKey("Estados.ID_Estados"))
    Icono            = Column(String(500), nullable=True)
    Fecha_Creacion   = Column(DateTime, nullable=True)

    productos       = relationship("Producto", back_populates="categoria")
    fichas_tecnicas = relationship("FichaTecnica", back_populates="categoria")


class CategoriaInsumo(Base):
    __tablename__ = "Categoria_Insumos"

    ID_Categoria     = Column(Integer, primary_key=True, index=True)
    Nombre_Categoria = Column(String(100))
    Descripcion      = Column(Text)
    Estado           = Column(Integer, ForeignKey("Estados.ID_Estados"))
    Icono            = Column(String(500), nullable=True)
    Fecha_Creacion   = Column(DateTime)

    insumos = relationship("Insumo", back_populates="categoria")


# ─────────────────────────────────────────
# INSUMOS
# ─────────────────────────────────────────

class UnidadMedida(Base):
    __tablename__ = "Unidad_Medida"

    ID_Unidad_Medida = Column(Integer, primary_key=True, index=True)
    Simbolo          = Column(String(5))
    Unidad_Medida    = Column(String(25))

    insumos = relationship("Insumo", back_populates="unidad_medida")


class Insumo(Base):
    __tablename__ = "Insumos"

    ID_Insumo      = Column(Integer, primary_key=True, index=True)
    ID_Categoria   = Column(Integer, ForeignKey("Categoria_Insumos.ID_Categoria"))
    ID_Lote_Compra = Column(Integer, ForeignKey("Lote_Compra.ID_Lote_Compra"))
    Nombre         = Column(String(100))
    Unidad_Medida  = Column(Integer, ForeignKey("Unidad_Medida.ID_Unidad_Medida"))
    Stock_Actual   = Column(Integer)
    Stock_Minimo   = Column(Integer)
    Estado         = Column(Integer, ForeignKey("Estados.ID_Estados"))

    categoria       = relationship("CategoriaInsumo", back_populates="insumos")
    unidad_medida   = relationship("UnidadMedida", back_populates="insumos")
    lotes_compra    = relationship("LoteCompra", back_populates="insumo", foreign_keys="LoteCompra.ID_Insumo")
    detalle_compras = relationship("DetalleCompra", back_populates="insumo")
    ordenes         = relationship("OrdenProduccion", back_populates="insumo")


class LoteInsumo(Base):
    __tablename__ = "Lote_Insumos"

    ID_Lote           = Column(Integer, primary_key=True, index=True)
    Fecha_Vencimiento = Column(DateTime)
    Cantidad          = Column(Integer)


class LoteCompra(Base):
    __tablename__ = "Lote_Compra"

    ID_Lote_Compra    = Column(Integer, primary_key=True, index=True)
    ID_Insumo         = Column(Integer, ForeignKey("Insumos.ID_Insumo"))
    Fecha_Vencimiento = Column(DateTime)
    Cantidad_Inicial  = Column(Integer)
    Estado            = Column(Integer, ForeignKey("Estados.ID_Estados"))

    insumo          = relationship("Insumo", back_populates="lotes_compra", foreign_keys="[LoteCompra.ID_Insumo]")
    detalle_compras = relationship("DetalleCompra", back_populates="lote_compra")


# ─────────────────────────────────────────
# PROVEEDORES Y COMPRAS
# ─────────────────────────────────────────

class SujetoDerecho(Base):
    __tablename__ = "Sujeto_Derecho"

    ID_Sujeto_Derecho = Column(Integer, primary_key=True, index=True)
    Sujeto_Derecho    = Column(String(25))

    proveedores = relationship("Proveedor", back_populates="sujeto_derecho")


class Proveedor(Base):
    __tablename__ = "Proveedores"

    ID_Proveedor   = Column(Integer, primary_key=True, index=True)
    Sujeto_Derecho = Column(Integer, ForeignKey("Sujeto_Derecho.ID_Sujeto_Derecho"))
    Responsable    = Column(String(100))
    Direccion      = Column(String(50))
    Municipio      = Column(String(25))
    Departamento   = Column(String(60))
    Telefono       = Column(String(20))
    Correo         = Column(String(255))

    sujeto_derecho = relationship("SujetoDerecho", back_populates="proveedores")
    compras        = relationship("Compra", back_populates="proveedor")


class Compra(Base):
    __tablename__ = "Compras"

    ID_Compra    = Column(Integer, primary_key=True, index=True)
    ID_Proveedor = Column(Integer, ForeignKey("Proveedores.ID_Proveedor"))
    Total_Pago   = Column(Numeric(30, 2))
    Fecha_Compra = Column(DateTime)
    Estado       = Column(Integer, ForeignKey("Estados.ID_Estados"))
    Metodo_Pago  = Column(String(20))

    proveedor = relationship("Proveedor", back_populates="compras")
    detalles  = relationship("DetalleCompra", back_populates="compra")


class DetalleCompra(Base):
    __tablename__ = "Detalle_Compra"

    ID_Detalle_Compra = Column(Integer, primary_key=True, index=True)
    ID_Compra         = Column(Integer, ForeignKey("Compras.ID_Compra"))
    ID_Insumo         = Column(Integer, ForeignKey("Insumos.ID_Insumo"))
    ID_Lote_Compra    = Column(Integer, ForeignKey("Lote_Compra.ID_Lote_Compra"))
    Notas             = Column(Text)
    Cantidad          = Column(Integer)
    Precio_Und        = Column(Numeric(30, 2))

    compra      = relationship("Compra", back_populates="detalles")
    insumo      = relationship("Insumo", back_populates="detalle_compras")
    lote_compra = relationship("LoteCompra", back_populates="detalle_compras")


# ─────────────────────────────────────────
# PRODUCTOS
# ─────────────────────────────────────────

class ProductoImagen(Base):
    __tablename__ = "Producto_Imagenes"

    ID_Producto_Img = Column(Integer, primary_key=True, index=True)
    ID_Producto     = Column(Integer, ForeignKey("Productos.ID_Producto"))
    imagen          = Column(String(500), nullable=True)


class Producto(Base):
    __tablename__ = "Productos"

    ID_Producto         = Column(Integer, primary_key=True, index=True)
    nombre              = Column(String(255))
    ID_Categoria        = Column(Integer, ForeignKey("Categoria_Producto.ID_Categoria"))
    Precio_venta        = Column(Numeric(30, 2))
    Stock               = Column(Integer)
    Stock_Minimo        = Column(Integer)
    Estado              = Column(Integer, ForeignKey("Estados.ID_Estados"))
    ID_Orden_Produccion = Column(Integer, ForeignKey("Orden_Produccion.ID_Orden_Produccion"))
    Imagen              = Column(Integer, ForeignKey("Producto_Imagenes.ID_Producto_Img"))

    categoria       = relationship("CategoriaProducto", back_populates="productos")
    fichas_tecnicas = relationship("FichaTecnica", back_populates="producto")
    ventas          = relationship("VentaXProducto", back_populates="producto")
    devoluciones    = relationship("DevolucionDetalle", back_populates="producto")


# ─────────────────────────────────────────
# PRODUCCION
# ─────────────────────────────────────────

class FichaTecnica(Base):
    __tablename__ = "Ficha_Tecnica"

    ID_Ficha       = Column(Integer, primary_key=True, index=True)
    ID_Producto    = Column(Integer, ForeignKey("Productos.ID_Producto"))
    Version        = Column(String(25))
    ID_Categoria   = Column(Integer, ForeignKey("Categoria_Producto.ID_Categoria"))
    Estado         = Column(Integer, ForeignKey("Estados.ID_Estados"))
    Observaciones  = Column(Text)
    Procedimiento  = Column(Text)
    Fecha_Creacion = Column(DateTime)

    producto  = relationship("Producto", back_populates="fichas_tecnicas")
    categoria = relationship("CategoriaProducto", back_populates="fichas_tecnicas")
    ordenes   = relationship("OrdenProduccion", back_populates="ficha")


class OrdenProduccion(Base):
    __tablename__ = "Orden_Produccion"

    ID_Orden_Produccion = Column(Integer, primary_key=True, index=True)
    ID_Producto         = Column(Integer, ForeignKey("Productos.ID_Producto"))
    ID_Insumo           = Column(Integer, ForeignKey("Insumos.ID_Insumo"))
    ID_Ficha            = Column(Integer, ForeignKey("Ficha_Tecnica.ID_Ficha"))
    Cantidad            = Column(Integer)
    Fecha_inicio        = Column(DateTime)
    Fecha_Entrega       = Column(DateTime)
    Estado              = Column(Integer, ForeignKey("Estados.ID_Estados"))
    Costo               = Column(Numeric(30, 2))

    insumo = relationship("Insumo", back_populates="ordenes")
    ficha  = relationship("FichaTecnica", back_populates="ordenes")


# ─────────────────────────────────────────
# VENTAS
# ─────────────────────────────────────────

class Venta(Base):
    __tablename__ = "Ventas"

    ID_Venta          = Column(Integer, primary_key=True, index=True)
    ID_Usuario        = Column(Integer, ForeignKey("Usuarios.ID_Usuario"))
    Total             = Column(Numeric(30, 2))
    Estado            = Column(Integer, ForeignKey("Estados.ID_Estados"))
    Metodo_Pago       = Column(String(20))
    Fecha_Venta       = Column(DateTime)
    Fecha_pedido      = Column(DateTime)
    Comprobante_Pago  = Column(LONGTEXT, nullable=True)

    usuario      = relationship("Usuario", back_populates="ventas")
    productos    = relationship("VentaXProducto", back_populates="venta")
    detalle      = relationship("DetalleVenta", back_populates="venta")
    domicilios   = relationship("Domicilio", back_populates="venta")
    devoluciones = relationship("Devolucion", back_populates="venta")


class VentaXProducto(Base):
    __tablename__ = "Venta_x_Producto"

    ID_Venta    = Column(Integer, ForeignKey("Ventas.ID_Venta"), primary_key=True)
    ID_Producto = Column(Integer, ForeignKey("Productos.ID_Producto"), primary_key=True)
    Cantidad    = Column(Integer)

    venta    = relationship("Venta", back_populates="productos")
    producto = relationship("Producto", back_populates="ventas")


class DetalleVenta(Base):
    __tablename__ = "Detalle_Venta"

    ID_DetalleVenta = Column(Integer, primary_key=True, index=True)
    ID_Venta        = Column(Integer, ForeignKey("Ventas.ID_Venta"))
    A_Nombre_De     = Column(String(100))
    IVA             = Column(Numeric(30, 2))
    Descuento       = Column(Numeric(30, 2))
    SubTotal        = Column(Numeric(30, 2))

    venta        = relationship("Venta", back_populates="detalle")
    devoluciones = relationship("Devolucion", back_populates="detalle_venta")


# ─────────────────────────────────────────
# LOGISTICA Y DEVOLUCIONES
# ─────────────────────────────────────────

class Domicilio(Base):
    __tablename__ = "Domicilios"

    ID_Domicilio         = Column(Integer, primary_key=True, index=True)
    ID_Venta             = Column(Integer, ForeignKey("Ventas.ID_Venta"))
    ID_Empleado          = Column(Integer, ForeignKey("Empleados.ID_Empleado"))     # ← actualizado
    Fecha_asignacion     = Column(DateTime)
    Fecha_entrega        = Column(DateTime)
    Observaciones        = Column(Text)
    Estado               = Column(Integer, ForeignKey("Estados.ID_Estados"))
    Direccion_entrega    = Column(String(50))
    Municipio_entrega    = Column(String(25))
    Departamento_entrega = Column(String(60))

    venta    = relationship("Venta", back_populates="domicilios")
    empleado = relationship("Empleado", foreign_keys=[ID_Empleado])


class Devolucion(Base):
    __tablename__ = "Devoluciones"

    ID_Devolucion   = Column(Integer, primary_key=True, index=True)
    ID_Venta        = Column(Integer, ForeignKey("Ventas.ID_Venta"))
    ID_Usuario      = Column(Integer, ForeignKey("Usuarios.ID_Usuario"))            # ← actualizado
    ID_DetalleVenta = Column(Integer, ForeignKey("Detalle_Venta.ID_DetalleVenta"))
    FechaDevolucion = Column(DateTime)
    Motivo          = Column(Text)
    Estado          = Column(Integer, ForeignKey("Estados.ID_Estados"))
    TotalDevuelto   = Column(Numeric(30, 2))
    FechaAprobacion = Column(DateTime)
    FechaReembolso  = Column(DateTime)
    UsuarioAprueba  = Column(Boolean)
    Comentario      = Column(Text)

    venta         = relationship("Venta", back_populates="devoluciones")
    usuario       = relationship("Usuario", back_populates="devoluciones")
    detalle_venta = relationship("DetalleVenta", back_populates="devoluciones")
    detalles      = relationship("DevolucionDetalle", back_populates="devolucion")


class DevolucionDetalle(Base):
    __tablename__ = "Devolucion_Detalle"

    ID_Devolucion_Detalle = Column(Integer, primary_key=True, index=True)
    ID_Devolucion         = Column(Integer, ForeignKey("Devoluciones.ID_Devolucion"))
    ID_Producto           = Column(Integer, ForeignKey("Productos.ID_Producto"))
    Cantidad              = Column(Integer)
    PrecioUnitario        = Column(Numeric(30, 2))
    Subtotal              = Column(Numeric(30, 2))

    devolucion = relationship("Devolucion", back_populates="detalles")
    producto   = relationship("Producto", back_populates="devoluciones")


# ─────────────────────────────────────────
# CREDITOS DE CLIENTE
# ─────────────────────────────────────────

class CreditoCliente(Base):
    __tablename__ = "Credito_Cliente"

    ID_Credito   = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ID_Usuario   = Column(Integer, ForeignKey("Usuarios.ID_Usuario"), unique=True)
    Saldo        = Column(Numeric(30, 2), default=0)
    Fecha_Update = Column(DateTime)

    usuario      = relationship("Usuario", foreign_keys=[ID_Usuario])
    movimientos  = relationship("MovimientoCredito", back_populates="credito")


class MovimientoCredito(Base):
    __tablename__ = "Movimiento_Credito"

    ID_Movimiento = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ID_Credito    = Column(Integer, ForeignKey("Credito_Cliente.ID_Credito"))
    ID_Devolucion = Column(Integer, ForeignKey("Devoluciones.ID_Devolucion"), nullable=True)
    ID_Venta      = Column(Integer, ForeignKey("Ventas.ID_Venta"), nullable=True)
    Tipo          = Column(String(20))      # "recarga" o "uso"
    Monto         = Column(Numeric(30, 2))
    Fecha         = Column(DateTime)

    credito    = relationship("CreditoCliente", back_populates="movimientos")


# ─────────────────────────────────────────
# SALIDAS (daños, vencimientos, ajustes)
# ─────────────────────────────────────────

class Salida(Base):
    __tablename__ = "Salidas"

    ID_Salida   = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Tipo        = Column(String(20))          # 'vencimiento','daño','ajuste','consumo','devolución'
    ID_Insumo   = Column(Integer, ForeignKey("Insumos.ID_Insumo"),    nullable=True)
    ID_Producto = Column(Integer, ForeignKey("Productos.ID_Producto"), nullable=True)
    Cantidad    = Column(Integer)
    Motivo      = Column(Text, nullable=True)
    ID_Empleado = Column(Integer, ForeignKey("Empleados.ID_Empleado"), nullable=True)
    Fecha       = Column(DateTime)
    Estado      = Column(Integer, ForeignKey("Estados.ID_Estados"))

    insumo   = relationship("Insumo",   foreign_keys=[ID_Insumo])
    producto = relationship("Producto", foreign_keys=[ID_Producto])
    empleado = relationship("Empleado", foreign_keys=[ID_Empleado])


# ─────────────────────────────────────────
# NOTIFICACIONES
# ─────────────────────────────────────────

class Notificacion(Base):
    __tablename__ = "Notificaciones"

    ID_Notificacion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Tipo            = Column(String(30))
    Titulo          = Column(String(100))
    Mensaje         = Column(Text, nullable=True)
    Referencia_ID   = Column(Integer, nullable=True)
    Ruta            = Column(String(200), nullable=True)
    Fecha           = Column(DateTime)
    Leida           = Column(Boolean, default=False)


# ─────────────────────────────────────────
# DESCUENTOS
# ─────────────────────────────────────────

class Descuento(Base):
    __tablename__ = "Descuentos"

    ID_Descuento   = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Nombre         = Column(String(100))
    Tipo           = Column(String(20))         # "cupon", "antiguedad", "emision"
    Codigo         = Column(String(50), nullable=True, unique=True)  # solo cupones
    Porcentaje     = Column(Numeric(5, 2))
    Meses_Minimos  = Column(Integer, nullable=True)     # solo antigüedad
    Fecha_Inicio   = Column(DateTime)
    Fecha_Fin      = Column(DateTime, nullable=True)    # null = sin vencimiento
    Usos_Max       = Column(Integer, nullable=True)     # null = ilimitado
    Usos_Actuales  = Column(Integer, default=0)
    Estado         = Column(Integer, ForeignKey("Estados.ID_Estados"))

    asignaciones   = relationship("DescuentoXUsuario", back_populates="descuento")
    ventas         = relationship("DescuentoXVenta", back_populates="descuento")


class DescuentoXUsuario(Base):
    """Tabla de ruptura para descuentos de emisión asignados a usuarios específicos."""
    __tablename__ = "Descuento_x_Usuario"

    ID_Descuento      = Column(Integer, ForeignKey("Descuentos.ID_Descuento"), primary_key=True)
    ID_Usuario        = Column(Integer, ForeignKey("Usuarios.ID_Usuario"), primary_key=True)
    Usado             = Column(Boolean, default=False)
    Fecha_Asignacion  = Column(DateTime)

    descuento = relationship("Descuento", back_populates="asignaciones")
    usuario   = relationship("Usuario", foreign_keys=[ID_Usuario])


class DescuentoXVenta(Base):
    """Registra qué descuento se aplicó en cada venta y cuánto."""
    __tablename__ = "Descuento_x_Venta"

    ID_Venta        = Column(Integer, ForeignKey("Ventas.ID_Venta"), primary_key=True)
    ID_Descuento    = Column(Integer, ForeignKey("Descuentos.ID_Descuento"), primary_key=True)
    Monto_Aplicado  = Column(Numeric(30, 2))

    descuento = relationship("Descuento", back_populates="ventas")
    venta     = relationship("Venta", foreign_keys=[ID_Venta])