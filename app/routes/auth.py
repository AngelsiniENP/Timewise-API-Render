# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routes.models import Usuario
from app.routes.auth_utils import pwd_context, create_access_token, verify_token
from datetime import datetime, timedelta
import secrets
import string
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from fastapi import Depends
from app.routes.auth_utils import verify_token
from pathlib import Path
from dotenv import load_dotenv

# CARGAR .env DESDE LA RAÍZ
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# DEBUG: Verificar carga
print(f"Cargando .env desde: {env_path}")
print(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")

# Configuración de FastMail
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "TimeWise"),
    MAIL_STARTTLS=os.getenv("MAIL_TLS", "True").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL", "False").lower() == "true",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)

router = APIRouter(prefix="/auth", tags=["Autenticación"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Modelos Pydantic
class RegisterUser(BaseModel):
    correo: str
    contrasena: str
    nombres: str
    apellidos: str
    edad: int
    id_rol: int = 2  # Default: usuario estándar

class RecoverPassword(BaseModel):
    correo: str

class ResetPassword(BaseModel):
    token: str
    nueva_contrasena: str

# Generar token aleatorio
def generar_token() -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

# --- RUTAS ---

@router.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):
    # Verificar si el correo ya existe
    if db.query(Usuario).filter(Usuario.correo == user.correo).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # Hash de la contraseña
    hashed_password = pwd_context.hash(user.contrasena)

    # Crear usuario
    nuevo_usuario = Usuario(
        correo=user.correo,
        contrasena=hashed_password,
        nombres=user.nombres,
        apellidos=user.apellidos,
        edad=user.edad,
        id_rol=user.id_rol,
        fecha_registro=datetime.now()
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return {"msg": "Usuario creado exitosamente"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.correo == form_data.username).first()
    if not usuario or not pwd_context.verify(form_data.password, usuario.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Actualizar último login
    usuario.ultimo_login = datetime.now()
    db.commit()

    # Generar token JWT
    access_token = create_access_token(
        data={"sub": str(usuario.id_usuario)},
        expires_delta=timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/recover-password")
async def recover_password(data: RecoverPassword, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.correo == data.correo).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Generar y guardar token
    token = generar_token()
    usuario.token_reset = token
    usuario.token_reset_expiry = datetime.now() + timedelta(minutes=15)
    db.commit()

    # Enviar email
    message = MessageSchema(
        subject="Recuperación de contraseña - TimeWise",
        recipients=[usuario.correo],
        body=f"""
        <h2>Recuperación de contraseña</h2>
        <p>Hola <strong>{usuario.nombres}</strong>,</p>
        <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
        <p><strong>Tu token de recuperación es:</strong></p>
        <h3 style="background:#f0f0f0;padding:10px;border-radius:5px;">{token}</h3>
        <p>Este token expira en <strong>15 minutos</strong>.</p>
        <p>Si no solicitaste esto, ignora este mensaje.</p>
        <br>
        <p>Saludos,<br><strong>Equipo TimeWise</strong></p>
        """,
        subtype="html"
    )

    try:
        await fm.send_message(message)
        return {"msg": "Email enviado con token para recuperación"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando email: {str(e)}")

@router.post("/reset-password")
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.token_reset == data.token).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Token inválido")

    if usuario.token_reset_expiry < datetime.now():
        raise HTTPException(status_code=400, detail="Token expirado")

    # Actualizar contraseña
    usuario.contrasena = pwd_context.hash(data.nueva_contrasena)
    usuario.token_reset = None
    usuario.token_reset_expiry = None
    db.commit()

    return {"msg": "Contraseña actualizada exitosamente"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    usuario = db.query(Usuario).filter(Usuario.id_usuario == int(user_id)).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return usuario