# app/routes/categorias.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import List, Optional
from app.database.database import get_db
from app.routes.models import TipoTarea
from app.routes.auth_utils import validar_id, validar_string, validar_color_hex

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

    @validator('nombre')
    def validar_nombre(cls, v):
        es_valido, msg = validar_string(v, min_len=3, max_len=50, nombre_campo="Nombre")
        if not es_valido:
            raise ValueError(msg)
        return v.strip()

    @validator('descripcion')
    def validar_descripcion(cls, v):
        if v and len(v) > 500:
            raise ValueError("Descripción no puede exceder 500 caracteres")
        return v.strip() if v else None

    @validator('color_default')
    def validar_color(cls, v):
        if v and not validar_color_hex(v):
            raise ValueError("Color debe ser hexadecimal válido (#XXXXXX)")
        return v


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    color_default: Optional[str] = None

    @validator('nombre')
    def validar_nombre(cls, v):
        if v is None:
            return v
        es_valido, msg = validar_string(v, min_len=3, max_len=50, nombre_campo="Nombre")
        if not es_valido:
            raise ValueError(msg)
        return v.strip()

    @validator('descripcion')
    def validar_descripcion(cls, v):
        if v and len(v) > 500:
            raise ValueError("Descripción no puede exceder 500 caracteres")
        return v.strip() if v else None

    @validator('color_default')
    def validar_color(cls, v):
        if v and not validar_color_hex(v):
            raise ValueError("Color debe ser hexadecimal válido")
        return v


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
    if not validar_id(id_categoria):
        raise HTTPException(400, "ID de categoría inválido")
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
    existente = db.query(TipoTarea).filter(TipoTarea.nombre == data.nombre.lower()).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una categoría con este nombre")

    nueva = TipoTarea(
        nombre=data.nombre.lower(),
        descripcion=data.descripcion,
        color_default=data.color_default or "#3498db"
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
    if not validar_id(id_categoria):
        raise HTTPException(400, "ID de categoría inválido")
    categoria = db.query(TipoTarea).filter(TipoTarea.id_categoria == id_categoria).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Validar nombre duplicado (si se está cambiando)
    if data.nombre:
        duplicado = db.query(TipoTarea).filter(
            TipoTarea.nombre == data.nombre.lower(),
            TipoTarea.id_categoria != id_categoria
        ).first()
        if duplicado:
            raise HTTPException(status_code=400, detail="Ya existe otra categoría con ese nombre")

    if data.nombre is not None:
        categoria.nombre = data.nombre.lower()
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
    if not validar_id(id_categoria):
        raise HTTPException(400, "ID de categoría inválido")
    categoria = db.query(TipoTarea).filter(TipoTarea.id_categoria == id_categoria).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(categoria)
    db.commit()
