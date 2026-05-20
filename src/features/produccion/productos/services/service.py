from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from datetime import datetime
from decimal import Decimal

from src.shared.services.models import Producto, CategoriaProducto, ProductoImagen, FichaTecnica
from .schemas import ProductoCreate, ProductoUpdate, FichaTecnicaInput


# IDs de estado en la tabla Estados (ajusta si difieren en tu BD)
ESTADO_DISPONIBLE     = 1
ESTADO_NO_DISPONIBLE  = 2


def _calcular_estado(stock: int, stock_minimo: int) -> tuple[int, str]:
    """Retorna el ID de estado y su etiqueta según el stock."""
    if stock > stock_minimo:
        return ESTADO_DISPONIBLE, "Disponible"
    return ESTADO_NO_DISPONIBLE, "No disponible"


def _formato_producto(producto: Producto, db: Session) -> dict:
    """Construye el dict de respuesta con categoría, imágenes y ficha técnica."""
    categoria = db.query(CategoriaProducto).filter(
        CategoriaProducto.ID_Categoria == producto.ID_Categoria
    ).first()

    imagenes = db.query(ProductoImagen).filter(
        ProductoImagen.ID_Producto == producto.ID_Producto
    ).all() if hasattr(ProductoImagen, "ID_Producto") else []

    ficha = db.query(FichaTecnica).filter(
        FichaTecnica.ID_Producto == producto.ID_Producto
    ).order_by(FichaTecnica.Fecha_Creacion.desc()).first()

    stock        = producto.Stock or 0
    stock_minimo = getattr(producto, "Stock_Minimo", 0) or 0
    estado_id, estado_label = _calcular_estado(stock, stock_minimo)

    return {
        "ID_Producto":      producto.ID_Producto,
        "nombre":           producto.nombre,
        "ID_Categoria":     producto.ID_Categoria,
        "nombre_categoria": categoria.Nombre_Categoria if categoria else None,
        "Precio_venta":     producto.Precio_venta,
        "Stock":            stock,
        "Stock_Minimo":     stock_minimo,
        "Estado":           estado_id,
        "estado_label":     estado_label,
        "imagenes": [
            {"ID_Producto_Img": img.ID_Producto_Img, "url": f"/imagenes/productos/{img.ID_Producto_Img}"}
            for img in imagenes
        ],
        "ficha_tecnica": {
            "ID_Ficha":      ficha.ID_Ficha,
            "Version":       ficha.Version,
            "Observaciones": ficha.Observaciones,
            "Procedimiento": ficha.Procedimiento,
            "Estado":        ficha.Estado,
            "Fecha_Creacion": ficha.Fecha_Creacion,
        } if ficha else None,
    }


def obtener_productos(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None
) -> dict:
    """Lista paginada. Busca por nombre o categoría."""
    query = db.query(Producto)

    if busqueda:
        termino = f"%{busqueda}%"
        query = query.join(
            CategoriaProducto,
            CategoriaProducto.ID_Categoria == Producto.ID_Categoria,
            isouter=True
        ).filter(
            Producto.nombre.ilike(termino) |
            CategoriaProducto.Nombre_Categoria.ilike(termino)
        )

    total     = query.count()
    offset    = (pagina - 1) * por_pagina
    productos = query.offset(offset).limit(por_pagina).all()

    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "productos":  [_formato_producto(p, db) for p in productos],
    }


def obtener_producto(db: Session, id_producto: int) -> dict:
    """Retorna un producto por ID o lanza 404."""
    producto = db.query(Producto).filter(Producto.ID_Producto == id_producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _formato_producto(producto, db)


def crear_producto(db: Session, datos: ProductoCreate) -> dict:
    """Crea el producto, calcula estado automático y crea ficha técnica si viene."""
    estado_id, _ = _calcular_estado(datos.Stock, datos.Stock_Minimo)

    nuevo = Producto(
        nombre       = datos.nombre,
        ID_Categoria = datos.ID_Categoria,
        Precio_venta = datos.Precio_venta,
        Stock        = datos.Stock,
        Stock_Minimo = datos.Stock_Minimo,
        Estado       = estado_id,
    )
    db.add(nuevo)
    db.flush()  # obtiene el ID sin hacer commit aún

    # Crea la ficha técnica si viene en el body
    if datos.ficha_tecnica:
        ficha = FichaTecnica(
            ID_Producto    = nuevo.ID_Producto,
            ID_Categoria   = datos.ID_Categoria,
            Version        = datos.ficha_tecnica.Version or "1.0",
            Observaciones  = datos.ficha_tecnica.Observaciones,
            Procedimiento  = datos.ficha_tecnica.Procedimiento,
            Estado         = estado_id,
            Fecha_Creacion = datetime.now(),
        )
        db.add(ficha)

    db.commit()
    db.refresh(nuevo)
    return _formato_producto(nuevo, db)


def editar_producto(db: Session, id_producto: int, datos: ProductoUpdate) -> dict:
    """Edita solo los campos enviados y recalcula el estado."""
    producto = db.query(Producto).filter(Producto.ID_Producto == id_producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(producto, campo, valor)

    # Recalcula estado automáticamente
    stock        = producto.Stock or 0
    stock_minimo = getattr(producto, "Stock_Minimo", 0) or 0
    producto.Estado, _ = _calcular_estado(stock, stock_minimo)

    db.commit()
    db.refresh(producto)
    return _formato_producto(producto, db)


def agregar_imagenes(db: Session, id_producto: int, imagenes: list[UploadFile]) -> dict:
    """
    Recibe una lista de archivos de imagen, los guarda como binario
    en Producto_Imagenes y los asocia al producto.
    """
    producto = db.query(Producto).filter(Producto.ID_Producto == id_producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for imagen in imagenes:
        contenido = imagen.file.read()
        nueva_img = ProductoImagen(
            ID_Producto = id_producto,
            imagen      = contenido,
        )
        db.add(nueva_img)

    db.commit()
    return _formato_producto(producto, db)


def eliminar_imagen(db: Session, id_imagen: int) -> dict:
    """Elimina una imagen por su ID."""
    imagen = db.query(ProductoImagen).filter(
        ProductoImagen.ID_Producto_Img == id_imagen
    ).first()
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    db.delete(imagen)
    db.commit()
    return {"mensaje": f"Imagen {id_imagen} eliminada"}


def eliminar_producto(db: Session, id_producto: int) -> dict:
    """Elimina el producto, sus imágenes y su ficha técnica."""
    producto = db.query(Producto).filter(Producto.ID_Producto == id_producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Elimina imágenes asociadas
    db.query(ProductoImagen).filter(
        ProductoImagen.ID_Producto == id_producto
    ).delete()

    # Elimina fichas técnicas asociadas
    db.query(FichaTecnica).filter(
        FichaTecnica.ID_Producto == id_producto
    ).delete()

    db.delete(producto)
    db.commit()
    return {"mensaje": f"Producto {id_producto} eliminado correctamente"}