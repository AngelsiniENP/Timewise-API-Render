# app/routes/perfil.py → VERSIÓN FINAL CON CAMBIO DE CONTRASEÑA Y CORREO
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Usuario
from app.routes.auth import get_current_user, pwd_context
from app.routes.auth_utils import validar_email, validar_contrasena, validar_string, validar_edad
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
    # ✅ Validación: Nombres válidos
    if update.nombres:
        es_valido, msg = validar_string(update.nombres, min_len=2, max_len=50, nombre_campo="Nombres")
        if not es_valido:
            raise HTTPException(400, msg)
    
    # ✅ Validación: Apellidos válidos
    if update.apellidos:
        es_valido, msg = validar_string(update.apellidos, min_len=2, max_len=50, nombre_campo="Apellidos")
        if not es_valido:
            raise HTTPException(400, msg)
    
    # ✅ Validación: Edad válida
    if update.edad:
        es_valida, mensaje = validar_edad(update.edad)
        if not es_valida:
            raise HTTPException(400, mensaje)
    
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
    # ✅ Validación 1: Contraseña actual correcta
    if not pwd_context.verify(datos.contrasena_actual, user.contrasena):
        raise HTTPException(400, detail="Contraseña actual incorrecta")

    # ✅ Validación 2: Nuevas coinciden
    if datos.nueva_contrasena != datos.confirmar_contrasena:
        raise HTTPException(400, detail="Las nuevas contraseñas no coinciden")

    # ✅ Validación 3: No usar contraseña anterior
    if pwd_context.verify(datos.nueva_contrasena, user.contrasena):
        raise HTTPException(400, detail="La nueva contraseña debe ser diferente a la actual")

    # ✅ Validación 4: Fortaleza de contraseña
    es_valida, mensaje = validar_contrasena(datos.nueva_contrasena)
    if not es_valida:
        raise HTTPException(400, detail=mensaje)

    user.contrasena = pwd_context.hash(datos.nueva_contrasena)
    db.commit()
    
    return {"msg": "Contraseña cambiada exitosamente"}

@router.put("/cambiar-correo")
def cambiar_correo(
    datos: CambiarCorreo,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ✅ Validación 1: Email válido
    if not validar_email(datos.nuevo_correo):
        raise HTTPException(400, detail="Email inválido")
    
    # ✅ Validación 2: Contraseña correcta
    if not pwd_context.verify(datos.contrasena_actual, user.contrasena):
        raise HTTPException(400, detail="Contraseña incorrecta")

    # ✅ Validación 3: Email no duplicado
    existe = db.query(Usuario).filter(
        Usuario.correo == datos.nuevo_correo,
        Usuario.id_usuario != user.id_usuario
    ).first()
    if existe:
        raise HTTPException(400, detail="Este correo ya está registrado")

    # ✅ Validación 4: Email diferente al actual
    if datos.nuevo_correo == user.correo:
        raise HTTPException(400, detail="El nuevo correo debe ser diferente al actual")

    user.correo = datos.nuevo_correo
    db.commit()
    
    return {"msg": "Correo actualizado correctamente", "nuevo_correo": datos.nuevo_correo}

@router.post("/foto")
def subir_foto(
    foto: UploadFile = File(...),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ✅ Validación: Tipo de archivo
    tipos_permitidos = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if foto.content_type not in tipos_permitidos:
        raise HTTPException(400, "Solo se permiten imágenes (JPEG, PNG, GIF, WebP)")
    
    # ✅ Validación: Tamaño máximo (5MB)
    MAX_SIZE = 5 * 1024 * 1024
    contenido = foto.file.read()
    if len(contenido) > MAX_SIZE:
        raise HTTPException(400, "La imagen no puede exceder 5MB")
    
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{user.id_usuario}_{foto.filename}"
    with open(file_path, "wb") as f:
        f.write(contenido)
    
    user.foto_perfil = file_path
    db.commit()
    return {"msg": "Foto de perfil actualizada", "ruta": f"/uploads/{user.id_usuario}_{foto.filename}"}