# app/routes/auth_utils.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re

load_dotenv()

# Configuración de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Variables JWT
SECRET_KEY = os.getenv("SECRET_KEY", "tu_super_secreto_aqui_cambia_en_produccion")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Crear token JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Verificar token JWT
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def validar_id(id_value):
    """Valida que un ID sea válido (mayor a 0)."""
    try:
        id_int = int(id_value)
        return id_int > 0
    except (ValueError, TypeError):
        return False

def validar_email(email: str) -> bool:
    """Valida formato de email."""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_contrasena(contrasena: str) -> tuple[bool, str]:
    """Valida fortaleza de contraseña. Retorna (es_valida, mensaje)"""
    if len(contrasena) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    if not any(c.isupper() for c in contrasena):
        return False, "Debe contener al menos una mayúscula"
    if not any(c.isdigit() for c in contrasena):
        return False, "Debe contener al menos un número"
    return True, "Contraseña válida"

def validar_string(valor: str, min_len: int = 1, max_len: int = 255, nombre_campo: str = "Campo") -> tuple[bool, str]:
    """Valida strings. Retorna (es_valido, mensaje)"""
    if not valor or not isinstance(valor, str):
        return False, f"{nombre_campo} no puede estar vacío"
    valor = valor.strip()
    if len(valor) < min_len:
        return False, f"{nombre_campo} debe tener al menos {min_len} caracteres"
    if len(valor) > max_len:
        return False, f"{nombre_campo} no puede exceder {max_len} caracteres"
    return True, "Válido"

def validar_edad(edad: int) -> tuple[bool, str]:
    """Valida que la edad sea realista."""
    if not isinstance(edad, int):
        return False, "La edad debe ser un número entero"
    if edad < 13:
        return False, "Debes tener al menos 13 años"
    if edad > 120:
        return False, "La edad no es válida"
    return True, "Edad válida"

def validar_prioridad(prioridad: str) -> bool:
    """Valida que la prioridad sea válida."""
    return prioridad.lower() in ['baja', 'media', 'alta']

def validar_estado_tarea(estado: str) -> bool:
    """Valida estados válidos de tareas."""
    return estado.lower() in ['pendiente', 'en_progreso', 'completada', 'pausada']

def validar_color_hex(color: str) -> bool:
    """Valida que sea un color hexadecimal válido."""
    patron = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return re.match(patron, color) is not None if color else True

def validar_hora(hora: str) -> bool:
    """Valida formato de hora HH:MM."""
    try:
        import datetime as dt
        dt.datetime.strptime(hora, "%H:%M")
        return True
    except ValueError:
        return False