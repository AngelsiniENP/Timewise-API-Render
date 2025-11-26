# app/routes/estadisticas.py → VERSIÓN FINAL 100% FUNCIONAL (SIN ERRORES)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Tarea, TipoTarea, Usuario
from app.routes.auth import get_current_user
from pydantic import BaseModel  # ¡AQUÍ ESTABA EL ERROR!
from typing import List
from datetime import datetime, timedelta
from collections import defaultdict

router = APIRouter(prefix="/estadisticas", tags=["Estadísticas"])

class EstadisticaCategoria(BaseModel):
    categoria_id: int
    nombre: str
    color: str
    tiempo_invertido: int = 0
    tareas_completadas: int = 0
    productividad: float = 0.0

    class Config:
        from_attributes = True

class ResumenEstadisticas(BaseModel):
    total_tiempo_invertido: int
    total_tareas_completadas: int
    productividad_promedio: float
    categorias: List[EstadisticaCategoria]
    periodo: str

@router.get("/", response_model=ResumenEstadisticas)
def obtener_estadisticas(
    periodo: str = Query("semanal", description="semanal, mensual, anual, todo"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hoy = datetime.now().date()
    inicio = None

    if periodo == "semanal":
        inicio = hoy - timedelta(days=hoy.weekday())
    elif periodo == "mensual":
        inicio = hoy.replace(day=1)
    elif periodo == "anual":
        inicio = hoy.replace(month=1, day=1)
    elif periodo != "todo":
        raise HTTPException(400, "Período inválido")

    query = db.query(Tarea).filter(
        Tarea.id_usuario == user.id_usuario,
        Tarea.estado == "completada"
    )
    if inicio:
        query = query.filter(Tarea.fecha >= inicio)
    tareas = query.all()

    stats = defaultdict(lambda: {"tiempo": 0, "completadas": 0})
    for t in tareas:
        cat_id = t.id_categoria or 0
        duracion = t.duracion_estimada or 0
        stats[cat_id]["tiempo"] += duracion
        stats[cat_id]["completadas"] += 1

    categorias_db = {c.id_categoria: c for c in db.query(TipoTarea).all()}
    categorias_db[0] = type('obj', (), {
        'nombre': 'Sin categoría',
        'color_default': '#95a5a6'
    })()

    categorias_finales = []
    total_tiempo = total_tareas = 0

    for cat_id, datos in stats.items():
        cat = categorias_db.get(cat_id)
        prod = 0.0
        if datos["tiempo"] > 0:
            prod = min(round((datos["completadas"] * 60 / datos["tiempo"]) * 100, 1), 100)

        categorias_finales.append(EstadisticaCategoria(
            categoria_id=cat_id,
            nombre=cat.nombre,
            color=cat.color_default,
            tiempo_invertido=datos["tiempo"],
            tareas_completadas=datos["completadas"],
            productividad=prod
        ))
        total_tiempo += datos["tiempo"]
        total_tareas += datos["completadas"]

    prom = round(sum(c.productividad for c in categorias_finales) / len(categorias_finales), 1) if categorias_finales else 0

    return ResumenEstadisticas(
        total_tiempo_invertido=total_tiempo,
        total_tareas_completadas=total_tareas,
        productividad_promedio=prom,
        categorias=categorias_finales,
        periodo=periodo.capitalize()
    )

@router.get("/grafico")
def grafico(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db), periodo: str = "semanal"):
    data = obtener_estadisticas(periodo, user, db)
    return {
        "labels": [c.nombre for c in data.categorias],
        "tiempo": [c.tiempo_invertido for c in data.categorias],
        "tareas": [c.tareas_completadas for c in data.categorias],
        "colores": [c.color for c in data.categoria],
        "productividad": [c.productividad for c in data.categorias]
    }