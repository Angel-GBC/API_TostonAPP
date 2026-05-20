from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import ClienteCreate, ClienteUpdate, ClienteEstado, ClienteResponse, ClienteListResponse
from .service import (
    obtener_clientes, obtener_cliente, crear_cliente,
    editar_cliente, cambiar_estado, subir_foto, obtener_foto, eliminar_cliente
)

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/", response_model=ClienteListResponse)
def listar_clientes(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_usuarios"))
):
    return obtener_clientes(db, pagina, por_pagina, busqueda)


@router.get("/{id_usuario}", response_model=ClienteResponse)
def ver_cliente(
    id_usuario: int,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("ver_usuarios"))
):
    return obtener_cliente(db, id_usuario)


@router.get("/{id_usuario}/foto")
def ver_foto(
    id_usuario: int,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("ver_usuarios"))
):
    foto = obtener_foto(db, id_usuario)
    return Response(content=foto, media_type="image/jpeg")


@router.post("/", response_model=ClienteResponse, status_code=201)
def agregar_cliente(
    datos: ClienteCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_usuarios"))
):
    return crear_cliente(db, datos)


@router.put("/{id_usuario}", response_model=ClienteResponse)
def actualizar_cliente(
    id_usuario: int,
    datos:      ClienteUpdate,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("editar_usuarios"))
):
    return editar_cliente(db, id_usuario, datos)


@router.patch("/{id_usuario}/estado", response_model=ClienteResponse)
def toggle_estado(
    id_usuario: int,
    datos:      ClienteEstado,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("editar_usuarios"))
):
    return cambiar_estado(db, id_usuario, datos.Estado)


@router.post("/{id_usuario}/foto", response_model=ClienteResponse)
def actualizar_foto(
    id_usuario: int,
    foto:       UploadFile = File(...),
    db:         Session    = Depends(get_db),
    _:          dict       = Depends(requiere_permiso("editar_usuarios"))
):
    return subir_foto(db, id_usuario, foto)


@router.delete("/{id_usuario}")
def borrar_cliente(
    id_usuario: int,
    db:         Session = Depends(get_db),
    _:          dict    = Depends(requiere_permiso("eliminar_usuarios"))
):
    return eliminar_cliente(db, id_usuario)