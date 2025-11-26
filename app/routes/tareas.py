# app/routes/tareas.py → TU VERSIÓN ORIGINAL + NUEVA RUTA DE FILTROS
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Tarea, Usuario
from app.routes.auth import get_current_user
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time as datetime_time
import datetime

router = APIRouter(prefix="/tareas", tags=["Tareas"])

# === Modelos (igual que antes) ===
class TareaCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha: date
    hora: Optional[str] = None
    id_categoria: Optional[int] = None
    prioridad: str = "media"
    duracion_estimada: Optional[int] = None
    etiqueta_color: Optional[str] = None
    repeticion: str = "ninguna"
    recordatorio_minutos: Optional[int] = None

class TareaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    hora: Optional[str] = None
    id_categoria: Optional[int] = None
    prioridad: Optional[str] = None
    duracion_estimada: Optional[int] = None
    etiqueta_color: Optional[str] = None
    repeticion: Optional[str] = None
    recordatorio_minutos: Optional[int] = None
    estado: Optional[str] = None

class TareaOut(BaseModel):
    id_tarea: int
    titulo: str
    descripcion: Optional[str]
    fecha: date
    hora: Optional[str]
    prioridad: str
    estado: str
    id_categoria: Optional[int]

# === RUTAS ORIGINALES (SIN TOCAR NADA) ===

@router.post("/", response_model=TareaOut)
def crear_tarea(tarea: TareaCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    hora_obj = None
    if tarea.hora:
        try:
            hora_obj = datetime.datetime.strptime(tarea.hora, "%H:%M").time()
        except:
            pass

    nueva = Tarea(
        id_usuario=user.id_usuario,
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        fecha=tarea.fecha,
        hora=hora_obj,
        id_categoria=tarea.id_categoria,
        prioridad=tarea.prioridad,
        duracion_estimada=tarea.duracion_estimada,
        estado="pendiente",
        etiqueta_color=tarea.etiqueta_color,
        repeticion=tarea.repeticion,
        recordatorio_minutos=tarea.recordatorio_minutos
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

# ← TU GET ORIGINAL (se queda igual)
@router.get("/", response_model=List[TareaOut])
def listar_tareas(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
    categoria: Optional[int] = Query(None, alias="id_categoria")
):
    query = db.query(Tarea).filter(Tarea.id_usuario == user.id_usuario)
    if categoria:
        query = query.filter(Tarea.id_categoria == categoria)
    tareas = query.all()
    return tareas

@router.put("/{id_tarea}", response_model=TareaOut)
def actualizar_tarea(id_tarea: int, datos: TareaUpdate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea, Tarea.id_usuario == user.id_usuario).first()
    if not tarea:
        raise HTTPException(404, "Tarea no encontrada")

    update_data = datos.dict(exclude_unset=True)
    if "hora" in update_data and update_data["hora"]:
        try:
            update_data["hora"] = datetime.datetime.strptime(update_data["hora"], "%H:%M").time()
        except:
            update_data["hora"] = None

    for key, value in update_data.items():
        setattr(tarea, key, value)

    db.commit()
    db.refresh(tarea)
    return tarea

@router.delete("/{id_tarea}")
def eliminar_tarea(id_tarea: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea, Tarea.id_usuario == user.id_usuario).first()
    if not tarea:
        raise HTTPException(404, "Tarea no encontrada")
    db.delete(tarea)
    db.commit()
    return {"msg": "Tarea eliminada"}

# === NUEVA RUTA: FILTROS AVANZADOS ===
@router.get("/filtrar", response_model=List[TareaOut])
def filtrar_tareas(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
    categoria: Optional[int] = Query(None, alias="id_categoria"),
    fecha: Optional[date] = Query(None, description="Fecha exacta (YYYY-MM-DD)"),
    desde: Optional[date] = Query(None, description="Desde fecha"),
    hasta: Optional[date] = Query(None, description="Hasta fecha"),
    estado: Optional[str] = Query(None, description="pendiente/en_progreso/completada/pausada"),
    prioridad: Optional[str] = Query(None, description="baja/media/alta")
):
    """
    Filtra tareas con múltiples criterios.
    Ejemplos:
    - /tareas/filtrar?categoria=2
    - /tareas/filtrar?fecha=2025-11-21
    - /tareas/filtrar?desde=2025-11-01&hasta=2025-11-30&estado=pendiente
    """
    query = db.query(Tarea).filter(Tarea.id_usuario == user.id_usuario)

    if categoria is not None:
        query = query.filter(Tarea.id_categoria == categoria)
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

    query = query.order_by(Tarea.fecha.asc(), Tarea.hora.asc())
    return query.all()