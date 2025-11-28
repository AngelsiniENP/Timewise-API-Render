# app/routes/tareas.py → VERSIÓN 100% FUNCIONAL Y DEFINITIVA (2025)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Tarea, Usuario, TipoTarea
from app.routes.auth import get_current_user
from app.routes.auth_utils import (
    validar_string,
    validar_prioridad,
    validar_hora,
)
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

router = APIRouter(prefix="/tareas", tags=["Tareas"])


# ======================= MODELOS PYDANTIC =======================
class TareaCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha: date
    hora: Optional[str] = None                # ← string "14:30"
    id_categoria: Optional[int] = None
    prioridad: str = "media"
    etiqueta_color: Optional[str] = None
    recordatorio_minutos: Optional[int] = None


class TareaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    hora: Optional[str] = None
    id_categoria: Optional[int] = None
    prioridad: Optional[str] = None
    etiqueta_color: Optional[str] = None
    recordatorio_minutos: Optional[int] = None
    estado: Optional[str] = None


class TareaOut(BaseModel):
    id_tarea: int
    titulo: str
    descripcion: Optional[str] = None
    fecha: date
    hora: Optional[str] = None
    prioridad: str
    estado: str
    id_categoria: Optional[int] = None
    etiqueta_color: Optional[str] = None
    recordatorio_minutos: Optional[int] = None

    model_config = {"from_attributes": True}


# ======================= ENDPOINTS =======================
@router.post("/", response_model=TareaOut)
def crear_tarea(
    tarea: TareaCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    # Validaciones
    if not validar_string(tarea.titulo, 3, 200):
        raise HTTPException(400, "Título debe tener entre 3 y 200 caracteres")
    if not validar_prioridad(tarea.prioridad):
        raise HTTPException(400, "Prioridad inválida (baja/media/alta)")
    if tarea.fecha < date.today():
        raise HTTPException(400, "No se permiten fechas pasadas")
    if tarea.hora and not validar_hora(tarea.hora):
        raise HTTPException(400, "Hora debe tener formato HH:MM")

    nueva = Tarea(
        id_usuario=user.id_usuario,               # ← CORREGIDO
        titulo=tarea.titulo.strip(),
        descripcion=tarea.descripcion,
        fecha=tarea.fecha,
        hora=tarea.hora,                          # ← string directo
        id_categoria=tarea.id_categoria,
        prioridad=tarea.prioridad.lower(),
        estado="pendiente",
        etiqueta_color=tarea.etiqueta_color,
        recordatorio_minutos=tarea.recordatorio_minutos,
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/", response_model=List[TareaOut])
def listar_tareas(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
    id_categoria: Optional[int] = Query(None, alias="categoria"),
):
    query = db.query(Tarea).filter(Tarea.id_usuario == user.id_usuario)
    if id_categoria:
        query = query.filter(Tarea.id_categoria == id_categoria)
    return query.order_by(Tarea.fecha, Tarea.hora).all()


@router.put("/{id_tarea}", response_model=TareaOut)
def actualizar_tarea(
    id_tarea: int,
    datos: TareaUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    tarea = (
        db.query(Tarea)
        .filter(Tarea.id_tarea == id_tarea, Tarea.id_usuario == user.id_usuario)
        .first()
    )
    if not tarea:
        raise HTTPException(404, "Tarea no encontrada")

    update_data = datos.dict(exclude_unset=True)

    if "hora" in update_data and update_data["hora"]:
        if not validar_hora(update_data["hora"]):
            raise HTTPException(400, "Formato de hora inválido (HH:MM)")

    for key, value in update_data.items():
        setattr(tarea, key, value)

    db.commit()
    db.refresh(tarea)
    return tarea


@router.delete("/{id_tarea}")
def eliminar_tarea(
    id_tarea: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    tarea = (
        db.query(Tarea)
        .filter(Tarea.id_tarea == id_tarea, Tarea.id_usuario == user.id_usuario)
        .first()
    )
    if not tarea:
        raise HTTPException(404, "Tarea no encontrada")

    db.delete(tarea)
    db.commit()
    return {"msg": "Tarea eliminada correctamente"}


@router.get("/filtrar", response_model=List[TareaOut])
def filtrar_tareas(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
    id_categoria: Optional[int] = Query(None, alias="categoria"),
    fecha: Optional[date] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
):
    query = db.query(Tarea).filter(Tarea.id_usuario == user.id_usuario)

    if id_categoria is not None:
        query = query.filter(Tarea.id_categoria == id_categoria)
    if fecha:
        query = query.filter(Tarea.fecha == fecha)
    if desde:
        query = query.filter(Tarea.fecha >= desde)
    if hasta:
        query = query.filter(Tarea.fecha <= hasta)
    if estado:
        query = query.filter(Tarea.estado == estado.lower())
    if prioridad:
        query = query.filter(Tarea.prioridad == prioridad.lower())

    return query.order_by(Tarea.fecha, Tarea.hora).all()