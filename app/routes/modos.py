# app/routes/modos.py → 100% compatible con tu proyecto actual
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import ModoTarea, UsuarioModo, Usuario
from app.routes.auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/modos", tags=["Modos de Tareas"])

class ModoOut(BaseModel):
    id_modo: int
    nombre: str
    descripcion: str | None = None

class ModoActivar(BaseModel):
    id_modo: int

@router.get("/", response_model=List[ModoOut])
def obtener_todos_los_modos(db: Session = Depends(get_db)):
    """Devuelve todos los modos disponibles (predefinidos)"""
    return db.query(ModoTarea).all()

@router.get("/mis-modos")
def mis_modos_activos(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    """Devuelve los modos que el usuario tiene activados"""
    modos = db.query(ModoTarea).join(UsuarioModo).filter(UsuarioModo.id_usuario == user.id_usuario).all()
    return [{"id_modo": m.id_modo, "nombre": m.nombre, "descripcion": m.descripcion} for m in modos]

@router.post("/activar")
def activar_modo(modo: ModoActivar, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    """Activa un modo para el usuario"""
    existe = db.query(ModoTarea).filter(ModoTarea.id_modo == modo.id_modo).first()
    if not existe:
        raise HTTPException(404, "Modo no encontrado")
    
    ya_tiene = db.query(UsuarioModo).filter(
        UsuarioModo.id_usuario == user.id_usuario,
        UsuarioModo.id_modo == modo.id_modo
    ).first()
    if ya_tiene:
        return {"msg": "Modo ya activado"}
    
    nuevo = UsuarioModo(id_usuario=user.id_usuario, id_modo=modo.id_modo)
    db.add(nuevo)
    db.commit()
    return {"msg": f"Modo '{existe.nombre}' activado correctamente"}

@router.delete("/desactivar/{id_modo}")
def desactivar_modo(id_modo: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    relacion = db.query(UsuarioModo).filter(
        UsuarioModo.id_usuario == user.id_usuario,
        UsuarioModo.id_modo == id_modo
    ).first()
    if not relacion:
        raise HTTPException(404, "Modo no activado")
    db.delete(relacion)
    db.commit()
    return {"msg": "Modo desactivado"}