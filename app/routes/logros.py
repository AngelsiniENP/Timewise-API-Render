# app/routes/logros.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Logro, Usuario
from app.routes.auth import get_current_user
from pydantic import BaseModel
from typing import List
from datetime import datetime
import random

router = APIRouter(prefix="/logros", tags=["Logros y Motivación"])

# Mensajes motivacionales (puedes agregar más cuando quieras)
MENSAJES_TAREA = [
    "¡Tarea completada! Eres una máquina",
    "¡Otro paso más cerca de la grandeza!",
    "¡Crack! Así se hace",
    "¡Boom! Tarea destruida",
    "¡Vas imparable hoy!",
    "¡Productividad nivel dios activado!",
    "¡Check! Otra victoria en tu historial"
]

MENSAJES_META = [
    "¡META CUMPLIDA! Eres una LEYENDA",
    "¡LO LOGRASTE! Este es tu momento",
    "¡ORGULLO MÁXIMO! Completaste una meta épica",
    "¡ERES IMPARABLE! Otra meta conquistada",
    "¡TROFEO DESBLOQUEADO! Eres un campeón",
    "¡WOW! Acabas de hacer historia en tu vida",
    "¡EL MUNDO ES TUYO! Meta lograda con éxito"
]

class LogroOut(BaseModel):
    id_logro: int
    mensaje: str
    tipo: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[LogroOut])
def mis_logros(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Logro).filter(Logro.id_usuario == user.id_usuario).order_by(Logro.fecha_creacion.desc()).all()