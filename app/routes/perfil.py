# app/routes/perfil.py → VERSIÓN FINAL CON CAMBIO DE CONTRASEÑA Y CORREO
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Usuario
from app.routes.auth import get_current_user, pwd_context  # ← pwd_context para hashear
from pydantic import BaseModel, EmailStr
from typing import Optional
import os

router = APIRouter(prefix="/perfil", tags=["Perfil"])

# === Modelos Pydantic ===
class PerfilUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    edad: Optional[int] = None

class CambiarContrasena(BaseModel):
    contrasena_actual: str
    nueva_contrasena: str
    confirmar_contrasena: str

class CambiarCorreo(BaseModel):
    nuevo_correo: EmailStr
    contrasena_actual: str  # Para seguridad

# === Endpoints ===

@router.get("/")
def ver_perfil(user: Usuario = Depends(get_current_user)):
    return {
        "nombres": user.nombres,
        "apellidos": user.apellidos,
        "edad": user.edad,
        "correo": user.correo,
        "foto_perfil": user.foto_perfil
    }

@router.put("/")
def actualizar_perfil(
    update: PerfilUpdate,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_data = update.dict(exclude_unset=True)
    
    if "nombres" in update_data:
        user.nombre = update_data.pop("nombres")
    if "apellidos" in update_data:
        user.apellido = update_data.pop("apellidos")
    
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return {"msg": "Perfil actualizado correctamente"}

@router.put("/cambiar-contrasena")
def cambiar_contrasena(
    datos: CambiarContrasena,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Verificar contraseña actual
    if not pwd_context.verify(datos.contrasena_actual, user.contrasena):
        raise HTTPException(400, detail="Contraseña actual incorrecta")

    # 2. Verificar que las nuevas coincidan
    if datos.nueva_contrasena != datos.confirmar_contrasena:
        raise HTTPException(400, detail="Las nuevas contraseñas no coinciden")

    # 3. Validar fortaleza (opcional, puedes mejorar esto)
    if len(datos.nueva_contrasena) < 6:
        raise HTTPException(400, detail="La nueva contraseña debe tener al menos 6 caracteres")

    # 4. Actualizar
    user.contrasena = pwd_context.hash(datos.nueva_contrasena)
    db.commit()
    
    return {"msg": "Contraseña cambiada exitosamente"}

@router.put("/cambiar-correo")
def cambiar_correo(
    datos: CambiarCorreo,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Verificar contraseña actual
    if not pwd_context.verify(datos.contrasena_actual, user.contrasena):
        raise HTTPException(400, detail="Contraseña incorrecta")

    # 2. Verificar que el nuevo correo no exista
    existe = db.query(Usuario).filter(
        Usuario.correo == datos.nuevo_correo,
        Usuario.id_usuario != user.id_usuario
    ).first()
    if existe:
        raise HTTPException(400, detail="Este correo ya está registrado")

    # 3. Actualizar correo
    user.correo = datos.nuevo_correo
    db.commit()
    
    return {"msg": "Correo actualizado correctamente", "nuevo_correo": datos.nuevo_correo}

@router.post("/foto")
def subir_foto(
    foto: UploadFile = File(...),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{user.id_usuario}_{foto.filename}"
    with open(file_path, "wb") as f:
        f.write(foto.file.read())
    
    user.foto_perfil = file_path
    db.commit()
    return {"msg": "Foto de perfil actualizada", "ruta": f"/uploads/{user.id_usuario}_{foto.filename}"}