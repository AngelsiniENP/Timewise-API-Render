# app/routes/tareas.py → VERSIÓN ULTRA PROFESIONAL 2025
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Tarea, Usuario
from app.routes.auth import get_current_user
from app.routes.auth_utils import validar_string, validar_hora
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date

router = APIRouter(prefix="/tareas", tags=["Tareas"])


# ======================= MODELOS CON VALIDACIONES CLARAS =======================
class TareaCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha: date
    hora: Optional[str] = None
    id_categoria: Optional[int] = None
    prioridad: str = "media"
    etiqueta_color: Optional[str] = None
    recordatorio_minutos: Optional[int] = None

    @field_validator("titulo")
    def validar_titulo(cls, v):
        if not validar_string(v, min_len=3, max_len=200):
            raise ValueError("El título debe tener entre 3 y 200 caracteres")
        return v.strip()

    @field_validator("prioridad")
    def validar_prioridad(cls, v):
        valor = v.strip().lower()
        if valor not in ["baja", "media", "alta"]:
            raise ValueError("Prioridad inválida. Usa: 'baja', 'media' o 'alta'")
        return valor

    @field_validator("hora")
    def validar_formato_hora(cls, v):
        if v is None:
            return None
        v = v.strip()
        if not validar_hora(v):
            raise ValueError("Hora debe tener formato HH:MM (ejemplo: 14:30, 09:15)")
        return v

    @field_validator("fecha")
    def fecha_no_pasada(cls, v):
        if v < date.today():
            raise ValueError("No se permiten fechas del pasado")
        return v

    @field_validator("etiqueta_color")
    def validar_color(cls, v):
        if v and not v.strip().startswith("#"):
            raise ValueError("El color debe ser en formato hexadecimal (ej: #ff5733)")
        return v.strip() if v else None


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

    @field_validator("titulo")
    def validar_titulo(cls, v):
        if v is not None and not validar_string(v, min_len=3, max_len=200):
            raise ValueError("El título debe tener entre 3 y 200 caracteres")
        return v.strip() if v else None

    @field_validator("prioridad")
    def validar_prioridad(cls, v):
        if v is None:
            return None
        valor = v.strip().lower()
        if valor not in ["baja", "media", "alta"]:
            raise ValueError("Prioridad inválida. Valores permitidos: baja, media, alta")
        return valor

    @field_validator("estado")
    def validar_estado(cls, v):
        if v is None:
            return None
        valor = v.strip().lower()
        if valor not in ["pendiente", "en_progreso", "completada", "pausada"]:
            raise ValueError("Estado inválido. Usa: pendiente, en_progreso, completada o pausada")
        return valor

    @field_validator("hora")
    def validar_formato_hora(cls, v):
        if v is None:
            return None
        v = v.strip()
        if v and not validar_hora(v):
            raise ValueError("Hora inválida. Formato correcto: HH:MM (ej: 08:00)")
        return v

    @field_validator("fecha")
    def fecha_no_pasada(cls, v):
        if v is not None and v < date.today():
            raise ValueError("No puedes poner una fecha pasada")
        return v


class TareaOut(BaseModel):
    id_tarea: int
    titulo: str
    descripcion: Optional[str]
    fecha: date
    hora: Optional[str]
    prioridad: str
    estado: str
    id_categoria: Optional[int]
    etiqueta_color: Optional[str]
    recordatorio_minutos: Optional[int]

    model_config = {"from_attributes": True}


# ======================= ENDPOINTS =======================
@router.post("/", response_model=TareaOut, status_code=201)
def crear_tarea(tarea: TareaCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    nueva = Tarea(
        id_usuario=user.id_usuario,
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        fecha=tarea.fecha,
        hora=tarea.hora,
        id_categoria=tarea.id_categoria,
        prioridad=tarea.prioridad,
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
    q = db.query(Tarea).filter(Tarea.id_usuario == user.id_usuario)
    if id_categoria:
        q = q.filter(Tarea.id_categoria == id_categoria)
    return q.order_by(Tarea.fecha, Tarea.hora).all()


@router.put("/{id_tarea}", response_model=TareaOut)
def actualizar_tarea(
    id_tarea: int,
    datos: TareaUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea, Tarea.id_usuario == user.id_usuario).first()
    if not tarea:
        raise HTTPException(404, "Tarea no encontrada o no te pertenece")

    # Aplicar solo los campos que vengan
    update_data = datos.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(tarea, key, value)

    db.commit()
    db.refresh(tarea)
    return tarea


@router.delete("/{id_tarea}", status_code=200)
def eliminar_tarea(id_tarea: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea, Tarea.id_usuario == user.id_usuario).first()
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
    q = db.query(Tarea).filter(Tarea.id_usuario == user.id_usuario)

    if id_categoria is not None:
        q = q.filter(Tarea.id_categoria == id_categoria)
    if fecha:
        q = q.filter(Tarea.fecha == fecha)
    if desde:
        q = q.filter(Tarea.fecha >= desde)
    if hasta:
        q = q.filter(Tarea.fecha <= hasta)
    if estado:
        q = q.filter(Tarea.estado == estado.strip().lower())
    if prioridad:
        q = q.filter(Tarea.prioridad == prioridad.strip().lower())

    return q.order_by(Tarea.fecha, Tarea.hora).all()