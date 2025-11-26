# app/routes/categorias.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database.database import get_db
from app.routes.models import TipoTarea

router = APIRouter(prefix="/categorias", tags=["Categorías"])


# -----------------------------
# SCHEMAS
# -----------------------------
class CategoriaOut(BaseModel):
    id_categoria: int
    nombre: str
    descripcion: Optional[str] = None
    color_default: Optional[str] = None

    class Config:
        orm_mode = True


class CategoriaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    color_default: Optional[str] = None


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    color_default: Optional[str] = None


# -----------------------------
# GET - Todas las categorías
# -----------------------------
@router.get("/", response_model=List[CategoriaOut])
def obtener_categorias(db: Session = Depends(get_db)):
    return db.query(TipoTarea).all()


# -----------------------------
# GET - Una categoría por ID
# -----------------------------
@router.get("/{id_categoria}", response_model=CategoriaOut)
def obtener_categoria(id_categoria: int, db: Session = Depends(get_db)):
    cat = db.query(TipoTarea).filter(TipoTarea.id_categoria == id_categoria).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat


# -----------------------------
# POST - Crear categoría
# -----------------------------
@router.post("/", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def crear_categoria(data: CategoriaCreate, db: Session = Depends(get_db)):

    # Validación de duplicado
    existente = db.query(TipoTarea).filter(TipoTarea.nombre == data.nombre).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una categoría con este nombre")

    nueva = TipoTarea(
        nombre=data.nombre,
        descripcion=data.descripcion,
        color_default=data.color_default
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return nueva


# -----------------------------
# PUT - Actualizar categoría
# -----------------------------
@router.put("/{id_categoria}", response_model=CategoriaOut)
def actualizar_categoria(
    id_categoria: int,
    data: CategoriaUpdate,
    db: Session = Depends(get_db)
):

    categoria = db.query(TipoTarea).filter(TipoTarea.id_categoria == id_categoria).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Validar nombre duplicado (si se está cambiando)
    if data.nombre:
        duplicado = db.query(TipoTarea).filter(
            TipoTarea.nombre == data.nombre,
            TipoTarea.id_categoria != id_categoria
        ).first()
        if duplicado:
            raise HTTPException(status_code=400, detail="Ya existe otra categoría con ese nombre")

    # Actualizar solo campos enviados
    if data.nombre is not None:
        categoria.nombre = data.nombre
    if data.descripcion is not None:
        categoria.descripcion = data.descripcion
    if data.color_default is not None:
        categoria.color_default = data.color_default

    db.commit()
    db.refresh(categoria)

    return categoria


# -----------------------------
# DELETE - Eliminar categoría
# -----------------------------
@router.delete("/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(id_categoria: int, db: Session = Depends(get_db)):

    categoria = db.query(TipoTarea).filter(TipoTarea.id_categoria == id_categoria).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(categoria)
    db.commit()

    return {"message": "Categoría eliminada correctamente"}
