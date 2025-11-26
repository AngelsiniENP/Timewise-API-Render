# app/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.routes.models import Usuario
from pydantic import BaseModel, validator
from app.routes.auth import get_current_user, pwd_context
from app.routes.auth_utils import validar_id, validar_email, validar_contrasena, validar_string, validar_edad

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

    @validator('nombres')
    def validar_nombres(cls, v):
        es_valido, msg = validar_string(v, min_len=2, max_len=50, nombre_campo="Nombres")
        if not es_valido:
            raise ValueError(msg)
        return v.strip()

    @validator('apellidos')
    def validar_apellidos(cls, v):
        es_valido, msg = validar_string(v, min_len=2, max_len=50, nombre_campo="Apellidos")
        if not es_valido:
            raise ValueError(msg)
        return v.strip()

    @validator('edad')
    def validar_age(cls, v):
        es_valida, mensaje = validar_edad(v)
        if not es_valida:
            raise ValueError(mensaje)
        return v

    @validator('correo')
    def validar_correo(cls, v):
        if not validar_email(v):
            raise ValueError("Email inválido")
        return v.lower()

    @validator('contrasena')
    def validar_pass(cls, v):
        es_valida, mensaje = validar_contrasena(v)
        if not es_valida:
            raise ValueError(mensaje)
        return v

    @validator('id_rol')
    def validar_rol(cls, v):
        if not validar_id(v):
            raise ValueError("ID de rol inválido")
        return v

class UsuarioUpdate(UsuarioCreate):
    pass

@router.get("/usuarios")
def listar_usuarios(user = Depends(get_current_user), db: Session = Depends(get_db)):
    # ✅ Validación: Solo admin
    if user.id_rol != 1:
        raise HTTPException(403, "Solo administradores pueden listar usuarios")
    return db.query(Usuario).all()

@router.post("/usuarios")
def crear_usuario(usuario: UsuarioCreate, user = Depends(get_current_user), db: Session = Depends(get_db)):
    # ✅ Validación: Solo admin
    if user.id_rol != 1:
        raise HTTPException(403, "Solo administradores pueden crear usuarios")
    
    # ✅ Validación: Email no duplicado
    existe = db.query(Usuario).filter(Usuario.correo == usuario.correo.lower()).first()
    if existe:
        raise HTTPException(400, "El email ya está registrado")
    
    hashed = pwd_context.hash(usuario.contrasena)
    new_user = Usuario(
        nombre=usuario.nombres,
        apellido=usuario.apellidos,
        edad=usuario.edad,
        correo=usuario.correo.lower(),
        contrasena=hashed,
        id_rol=usuario.id_rol
    )
    db.add(new_user)
    db.commit()
    return {"msg": "Usuario creado correctamente", "id": new_user.id_usuario}

@router.put("/usuarios/{id}")
def actualizar_usuario(id: int, update: UsuarioUpdate, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not validar_id(id):
        raise HTTPException(400, "ID de usuario inválido")
    if user.id_rol != 1:
        raise HTTPException(403, "Solo administradores")
    
    db_user = db.query(Usuario).filter(Usuario.id_usuario == id).first()
    if not db_user:
        raise HTTPException(404, "Usuario no encontrado")
    
    # ✅ Validación: Email no duplicado
    if update.correo != db_user.correo:
        existe = db.query(Usuario).filter(
            Usuario.correo == update.correo.lower(),
            Usuario.id_usuario != id
        ).first()
        if existe:
            raise HTTPException(400, "El email ya está registrado")
    
    db_user.nombre = update.nombres
    db_user.apellido = update.apellidos
    db_user.edad = update.edad
    db_user.correo = update.correo.lower()
    db_user.contrasena = pwd_context.hash(update.contrasena)
    db_user.id_rol = update.id_rol
    
    db.commit()
    return {"msg": "Usuario actualizado correctamente"}

@router.delete("/usuarios/{id}")
def eliminar_usuario(id: int, user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not validar_id(id):
        raise HTTPException(400, "ID de usuario inválido")
    if user.id_rol != 1:
        raise HTTPException(403, "Solo administradores")
    
    # ✅ Validación: No eliminar a sí mismo
    if id == user.id_usuario:
        raise HTTPException(400, "No puedes eliminar tu propia cuenta")
    
    db_user = db.query(Usuario).filter(Usuario.id_usuario == id).first()
    if not db_user:
        raise HTTPException(404, "Usuario no encontrado")
    db.delete(db_user)
    db.commit()
    return {"msg": "Usuario eliminado correctamente"}