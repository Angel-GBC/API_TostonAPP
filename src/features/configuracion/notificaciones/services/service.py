from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.shared.services.models import Notificacion


def obtener_notificaciones(db: Session) -> dict:
    notificaciones = (
        db.query(Notificacion)
        .order_by(Notificacion.Leida.asc(), Notificacion.Fecha.desc())
        .all()
    )
    total_no_leidas = sum(1 for n in notificaciones if not n.Leida)
    return {
        "total":           len(notificaciones),
        "total_no_leidas": total_no_leidas,
        "notificaciones":  notificaciones,
    }


def marcar_leida(db: Session, id_notificacion: int):
    notif = db.query(Notificacion).filter(
        Notificacion.ID_Notificacion == id_notificacion
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    notif.Leida = True
    db.commit()
    db.refresh(notif)
    return notif


def eliminar_notificacion(db: Session, id_notificacion: int) -> dict:
    notif = db.query(Notificacion).filter(
        Notificacion.ID_Notificacion == id_notificacion
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    db.delete(notif)
    db.commit()
    return {"mensaje": f"Notificación {id_notificacion} eliminada"}


def limpiar_leidas(db: Session) -> dict:
    eliminadas = db.query(Notificacion).filter(Notificacion.Leida == True).delete()
    db.commit()
    return {"mensaje": f"{eliminadas} notificaciones eliminadas"}
