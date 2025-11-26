from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/ayuda", tags=["Ayuda"])

class Soporte(BaseModel):
    mensaje: str

@router.get("/")
def tutoriales():
    return [
        {"titulo": "Cómo crear una tarea", "contenido": "Ve a Crear nueva tarea..."},
        {"titulo": "Cómo usar el cronómetro", "contenido": "Selecciona Cronometrar en una tarea..."},
        # Añadir más del PDF
    ]

@router.post("/soporte")
def reportar_problema(soporte: Soporte):
    # Simulado: enviar email o guardar en DB
    return {"msg": "Sugerencia recibida, gracias!"}