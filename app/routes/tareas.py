# app/routes/tareas.py → TU VERSIÓN ORIGINAL + NUEVA RUTA DE FILTROS
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Tarea, Usuario, TipoTarea
from app.routes.auth import get_current_user
from app.routes.auth_utils import validar_id, validar_string, validar_prioridad, validar_estado_tarea, validar_color_hex, validar_hora
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time as datetime_time, datetime
import datetime as dt

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

    class Config:
        from_attributes = True

# === RUTAS ORIGINALES (SIN TOCAR NADA) ===

@router.post("/", response_model=TareaOut)
def crear_tarea(tarea: TareaCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    # ✅ Validación: Título no vacío
    es_valido, msg = validar_string(tarea.titulo, min_len=3, max_len=200, nombre_campo="Título")
    if not es_valido:
        raise HTTPException(400, msg)
    
    # ✅ Validación: Prioridad válida
    if not validar_prioridad(tarea.prioridad):
        raise HTTPException(400, "Prioridad debe ser: baja, media o alta")
    
    # ✅ Validación: Fecha no en el pasado
    if tarea.fecha < date.today():
        raise HTTPException(400, "No se pueden crear tareas en el pasado")
    
    # ✅ Validación: Hora válida
    hora_obj = None
    if tarea.hora:
        if not validar_hora(tarea.hora):
            raise HTTPException(400, "Formato de hora inválido. Use HH:MM")
        try:
            hora_obj = dt.datetime.strptime(tarea.hora, "%H:%M").time()
        except:
            raise HTTPException(400, "Hora inválida")
    
    # ✅ Validación: Categoría existe
    if tarea.id_categoria and not validar_id(tarea.id_categoria):
        raise HTTPException(400, "ID de categoría inválido")
    if tarea.id_categoria:
        cat_existe = db.query(TipoTarea).filter(TipoTarea.id_categoria == tarea.id_categoria).first()
        if not cat_existe:
            raise HTTPException(404, "Categoría no encontrada")
    
    # ✅ Validación: Duración positiva
    if tarea.duracion_estimada and tarea.duracion_estimada <= 0:
        raise HTTPException(400, "Duración estimada debe ser mayor a 0")
    
    # ✅ Validación: Color válido
    if tarea.etiqueta_color and not validar_color_hex(tarea.etiqueta_color):
        raise HTTPException(400, "Color debe ser en formato hexadecimal válido (#XXXXXX)")
    
    # ✅ Validación: Repetición válida
    if tarea.repeticion.lower() not in ['ninguna', 'diaria', 'semanal', 'mensual']:
        raise HTTPException(400, "Repetición inválida")
    
    # ✅ Validación: Recordatorio válido
    if tarea.recordatorio_minutos and tarea.recordatorio_minutos <= 0:
        raise HTTPException(400, "Recordatorio debe ser mayor a 0 minutos")

    nueva = Tarea(
        id_usuario=user.id_usuario,
        titulo=tarea.titulo.strip(),
        descripcion=tarea.descripcion.strip() if tarea.descripcion else None,
        fecha=tarea.fecha,
        hora=hora_obj,
        id_categoria=tarea.id_categoria,
        prioridad=tarea.prioridad.lower(),
        duracion_estimada=tarea.duracion_estimada,
        estado="pendiente",
        etiqueta_color=tarea.etiqueta_color,
        repeticion=tarea.repeticion.lower(),
        recordatorio_minutos=tarea.recordatorio_minutos
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.get("/", response_model=List[TareaOut])
def listar_tareas(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
    categoria: Optional[int] = Query(None, alias="id_categoria")
):
    # ✅ Validación: Categoría válida
    if categoria and not validar_id(categoria):
        raise HTTPException(400, "ID de categoría inválido")
    
    query = db.query(Tarea).filter(Tarea.id_usuario == user.id_usuario)
    if categoria:
        query = query.filter(Tarea.id_categoria == categoria)
    tareas = query.all()
    return tareas

@router.put("/{id_tarea}", response_model=TareaOut)
def actualizar_tarea(id_tarea: int, datos: TareaUpdate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    if not validar_id(id_tarea):
        raise HTTPException(400, "ID de tarea inválido")
    
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea, Tarea.id_usuario == user.id_usuario).first()
    if not tarea:
        raise HTTPException(404, "Tarea no encontrada")

    # ✅ Validación: Título no vacío
    if datos.titulo is not None:
        es_valido, msg = validar_string(datos.titulo, min_len=3, max_len=200, nombre_campo="Título")
        if not es_valido:
            raise HTTPException(400, msg)
    
    # ✅ Validación: Prioridad válida
    if datos.prioridad and not validar_prioridad(datos.prioridad):
        raise HTTPException(400, "Prioridad inválida")
    
    # ✅ Validación: Estado válido
    if datos.estado and not validar_estado_tarea(datos.estado):
        raise HTTPException(400, "Estado debe ser: pendiente, en_progreso, completada o pausada")
    
    # ✅ Validación: Fecha válida
    if datos.fecha and datos.fecha < date.today():
        raise HTTPException(400, "No se pueden asignar fechas en el pasado")
    
    # ✅ Validación: Hora válida
    if datos.hora and not validar_hora(datos.hora):
        raise HTTPException(400, "Formato de hora inválido")
    
    # ✅ Validación: Categoría existe
    if datos.id_categoria and not validar_id(datos.id_categoria):
        raise HTTPException(400, "ID de categoría inválido")
    if datos.id_categoria:
        cat_existe = db.query(TipoTarea).filter(TipoTarea.id_categoria == datos.id_categoria).first()
        if not cat_existe:
            raise HTTPException(404, "Categoría no encontrada")

    update_data = datos.dict(exclude_unset=True)
    if "hora" in update_data and update_data["hora"]:
        try:
            update_data["hora"] = dt.datetime.strptime(update_data["hora"], "%H:%M").time()
        except:
            update_data["hora"] = None

    for key, value in update_data.items():
        setattr(tarea, key, value)

    db.commit()
    db.refresh(tarea)
    return tarea

@router.delete("/{id_tarea}")
def eliminar_tarea(id_tarea: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    if not validar_id(id_tarea):
        raise HTTPException(400, "ID de tarea inválido")
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
    # ✅ Validaciones de query parameters
    if categoria and not validar_id(categoria):
        raise HTTPException(400, "ID de categoría inválido")
    
    if estado and not validar_estado_tarea(estado):
        raise HTTPException(400, "Estado inválido")
    
    if prioridad and not validar_prioridad(prioridad):
        raise HTTPException(400, "Prioridad inválida")
    
    if desde and hasta and desde > hasta:
        raise HTTPException(400, "Fecha 'desde' no puede ser mayor a 'hasta'")

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