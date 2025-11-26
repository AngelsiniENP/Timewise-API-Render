# app/routes/metas.py → VERSIÓN FINAL, LIMPIA Y SIN 422
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Meta, Usuario
from app.routes.auth import get_current_user
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/metas", tags=["Metas"])

# === Modelos ===
class MetaCreate(BaseModel):
    descripcion: str
    frecuencia: str
    objetivo: int

    @validator('frecuencia')
    def validar_frecuencia(cls, v):
        v = v.strip().lower()
        if v not in ['diaria', 'semanal', 'mensual']:
            raise ValueError("Frecuencia debe ser: diaria, semanal o mensual")
        return v

class MetaUpdate(BaseModel):
    descripcion: Optional[str] = None
    frecuencia: Optional[str] = None
    objetivo: Optional[int] = None

    @validator('frecuencia')
    def validar_frecuencia(cls, v):
        if v is None:
            return v
        v = v.strip().lower()
        if v not in ['diaria', 'semanal', 'mensual']:
            raise ValueError("Frecuencia inválida")
        return v

class ProgresoUpdate(BaseModel):
    progreso: int

class MetaOut(BaseModel):
    id_meta: int
    descripcion: str
    frecuencia: str
    objetivo: int
    progreso: int
    fecha_inicio: datetime
    completada: bool

    class Config:
        from_attributes = True

# === Endpoints ===
@router.post("/", response_model=MetaOut, status_code=status.HTTP_201_CREATED)
def crear_meta(meta: MetaCreate, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    nueva = Meta(
        id_usuario=user.id_usuario,
        descripcion=meta.descripcion,
        frecuencia=meta.frecuencia,
        objetivo=meta.objetivo,
        progreso=0,
        fecha_inicio=datetime.now().date(),
        completada=False
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.get("/", response_model=List[MetaOut])
def listar_metas(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Meta).filter(Meta.id_usuario == user.id_usuario).all()

@router.get("/{id_meta}", response_model=MetaOut)
def obtener_meta(id_meta: int, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    meta = db.query(Meta).filter(Meta.id_meta == id_meta, Meta.id_usuario == user.id_usuario).first()
    if not meta: raise HTTPException(404, "Meta no encontrada")
    return meta

@router.put("/{id_meta}", response_model=MetaOut)
def actualizar_meta(id_meta: int, datos: MetaUpdate, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    meta = db.query(Meta).filter(Meta.id_meta == id_meta, Meta.id_usuario == user.id_usuario).first()
    if not meta: raise HTTPException(404, "Meta no encontrada")

    update_data = datos.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(meta, key, value)

    db.commit()
    db.refresh(meta)
    return meta

@router.delete("/{id_meta}")
def eliminar_meta(id_meta: int, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    meta = db.query(Meta).filter(Meta.id_meta == id_meta, Meta.id_usuario == user.id_usuario).first()
    if not meta: raise HTTPException(404, "Meta no encontrada")
    db.delete(meta)
    db.commit()
    return {"msg": "Meta eliminada"}

@router.put("/{id_meta}/progreso", response_model=MetaOut)
def actualizar_progreso(id_meta: int, datos: ProgresoUpdate, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    meta = db.query(Meta).filter(Meta.id_meta == id_meta, Meta.id_usuario == user.id_usuario).first()
    if not meta: raise HTTPException(404, "Meta no encontrada")
    if datos.progreso < 0: raise HTTPException(400, "Progreso no puede ser negativo")

    meta.progreso = datos.progreso
    meta.completada = meta.progreso >= meta.objetivo
    db.commit()
    db.refresh(meta)
    return meta