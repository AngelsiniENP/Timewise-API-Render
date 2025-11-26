# app/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import SessionLocal  # ¡AÑADIR!
from app.routes.models import Usuario
from pydantic import BaseModel
from app.routes.auth import get_current_user, pwd_context  # pwd_context si lo usas

# --- Dependencia get_db ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/admin", tags=["Admin"])

class UsuarioCreate(BaseModel):
    nombres: str
    apellidos: str
    edad: int
    correo: str
    contrasena: str
    id_rol: int = 2

class UsuarioUpdate(UsuarioCreate):
    pass

@router.get("/usuarios")
def listar_usuarios(user = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.id_rol != 1:
        raise HTTPException(403, "Solo admin")
    return db.query(Usuario).all()

@router.post("/usuarios")
def crear_usuario(usuario: UsuarioCreate, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.id_rol != 1:
        raise HTTPException(403, "Solo admin")
    hashed = pwd_context.hash(usuario.contrasena)
    data = usuario.dict()
    data["contrasena"] = hashed  # ← Reemplazamos el valor
    new_user = Usuario(**data)
    db.add(new_user)
    db.commit()
    return {"msg": "Usuario creado"}

@router.put("/usuarios/{id}")
def actualizar_usuario(id: int, update: UsuarioUpdate, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.id_rol != 1:
        raise HTTPException(403, "Solo admin")
    db_user = db.query(Usuario).filter(Usuario.id_usuario == id).first()
    if not db_user:
        raise HTTPException(404, "Usuario no encontrado")
    for key, value in update.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    return {"msg": "Usuario actualizado"}

@router.delete("/usuarios/{id}")
def eliminar_usuario(id: int, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.id_rol != 1:
        raise HTTPException(403, "Solo admin")
    db_user = db.query(Usuario).filter(Usuario.id_usuario == id).first()
    if not db_user:
        raise HTTPException(404, "Usuario no encontrado")
    db.delete(db_user)
    db.commit()
    return {"msg": "Usuario eliminado"}