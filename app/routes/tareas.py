# app/routes/tareas.py → TU VERSIÓN ORIGINAL + NUEVA RUTA DE FILTROS
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Tarea, Usuario, TipoTarea, Meta
from app.routes.auth import get_current_user
from app.routes.auth_utils import validar_id, validar_string, validar_prioridad, validar_estado_tarea, validar_color_hex, validar_hora
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time as datetime_time, datetime
import datetime as dt

router = APIRouter(prefix="/tareas", tags=["Tareas"])

# === Modelos ===
class TareaCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha: date
    hora: Optional[str] = None
    id_categoria: Optional[int] = None
    id_meta: Optional[int] = None
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
    id_meta: Optional[int] = None
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

# === RUTAS ===

@router.post("/", response_model=TareaOut)
def crear_tarea(tarea: TareaCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    # ✅ Validación: Título no vacío
    es_valido, msg = validar_string(tarea.titulo, min_len=3, max_len=200, nombre_campo="Título")
    if not es_valido:
        raise HTTPException(400, msg)
    
    # ✅ Validación: Prioridad válida
    if not validar_prioridad(tarea.prioridad):
        raise HTTPException(400, "Prioridad inválida. Válidas: baja, media, alta")
    
    # ✅ Validación: Fecha no en el pasado
    if tarea.fecha < date.today():
        raise HTTPException(400, "No se pueden crear tareas en fechas pasadas")
    
    # ✅ Validación: Hora válida
    hora_obj = None
    if tarea.hora:
        if not validar_hora(tarea.hora):
            raise HTTPException(400, "Formato de hora inválido. Use HH:MM (ej: 14:30)")
        try:
            hora_obj = dt.datetime.strptime(tarea.hora, "%H:%M").time()
        except:
            raise HTTPException(400, "Hora inválida")
    
    # ✅ Validación: Categoría existe
    if tarea.id_categoria:
        if not validar_id(tarea.id_categoria):
            raise HTTPException(400, "ID de categoría inválido")
        cat_existe = db.query(TipoTarea).filter(TipoTarea.id_categoria == tarea.id_categoria).first()
        if not cat_existe:
            raise HTTPException(404, f"Categoría con ID {tarea.id_categoria} no existe")
    
    # ✅ Validación: Meta existe (si la proporciona)
    if tarea.id_meta:
        if not validar_id(tarea.id_meta):
            raise HTTPException(400, "ID de meta inválido")
        meta_existe = db.query(Meta).filter(Meta.id_meta == tarea.id_meta, Meta.id_usuario == user.id_usuario).first()
        if not meta_existe:
            raise HTTPException(404, f"Meta con ID {tarea.id_meta} no existe")
    
    # ✅ Validación: Duración positiva
    if tarea.duracion_estimada and tarea.duracion_estimada <= 0:
        raise HTTPException(400, "Duración estimada debe ser mayor a 0 minutos")
    if tarea.duracion_estimada and tarea.duracion_estimada > 1440:
        raise HTTPException(400, "Duración estimada no puede exceder 1440 minutos (24 horas)")
    
    # ✅ Validación: Color válido
    if tarea.etiqueta_color and not validar_color_hex(tarea.etiqueta_color):
        raise HTTPException(400, "Color debe ser hexadecimal válido (ej: #FF5733 o #F57)")
    
    # ✅ Validación: Repetición válida
    if tarea.repeticion.lower() not in ['ninguna', 'diaria', 'semanal', 'mensual']:
        raise HTTPException(400, "Repetición inválida. Válidas: ninguna, diaria, semanal, mensual")
    
    # ✅ Validación: Recordatorio válido
    if tarea.recordatorio_minutos and tarea.recordatorio_minutos <= 0:
        raise HTTPException(400, "Recordatorio debe ser mayor a 0 minutos")
    if tarea.recordatorio_minutos and tarea.recordatorio_minutos > 10080:
        raise HTTPException(400, "Recordatorio no puede exceder 10080 minutos (7 días)")

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
        raise HTTPException(404, f"Tarea con ID {id_tarea} no encontrada")

    # ✅ Validación: Título no vacío
    if datos.titulo is not None:
        es_valido, msg = validar_string(datos.titulo, min_len=3, max_len=200, nombre_campo="Título")
        if not es_valido:
            raise HTTPException(400, msg)
    
    # ✅ Validación: Prioridad válida
    if datos.prioridad and not validar_prioridad(datos.prioridad):
        raise HTTPException(400, "Prioridad inválida. Válidas: baja, media, alta")
    
    # ✅ Validación: Estado válido
    if datos.estado and not validar_estado_tarea(datos.estado):
        raise HTTPException(400, "Estado inválido. Válidos: pendiente, en_progreso, completada, pausada")
    
    # ✅ Validación: Fecha válida
    if datos.fecha and datos.fecha < date.today():
        raise HTTPException(400, "No se pueden asignar fechas en el pasado")
    
    # ✅ Validación: Hora válida
    if datos.hora and not validar_hora(datos.hora):
        raise HTTPException(400, "Formato de hora inválido. Use HH:MM")
    
    # ✅ Validación: Categoría existe
    if datos.id_categoria is not None:
        if datos.id_categoria and not validar_id(datos.id_categoria):
            raise HTTPException(400, "ID de categoría inválido")
        if datos.id_categoria:
            cat_existe = db.query(TipoTarea).filter(TipoTarea.id_categoria == datos.id_categoria).first()
            if not cat_existe:
                raise HTTPException(404, f"Categoría con ID {datos.id_categoria} no existe")
    
    # ✅ Validación: Meta existe
    if datos.id_meta is not None:
        if datos.id_meta and not validar_id(datos.id_meta):
            raise HTTPException(400, "ID de meta inválido")
        if datos.id_meta:
            meta_existe = db.query(Meta).filter(Meta.id_meta == datos.id_meta, Meta.id_usuario == user.id_usuario).first()
            if not meta_existe:
                raise HTTPException(404, f"Meta con ID {datos.id_meta} no existe")

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
        raise HTTPException(404, f"Tarea con ID {id_tarea} no encontrada")
    db.delete(tarea)
    db.commit()
    return {"msg": f"Tarea {id_tarea} eliminada correctamente"}

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
        raise HTTPException(400, "Estado inválido. Válidos: pendiente, en_progreso, completada, pausada")
    
    if prioridad and not validar_prioridad(prioridad):
        raise HTTPException(400, "Prioridad inválida. Válidas: baja, media, alta")
    
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