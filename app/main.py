# app/app.py → VERSIÓN FINAL 100% FUNCIONAL (con logros y todo perfecto)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# === TODOS TUS ROUTERS (ordenados y sin duplicados) ===
from app.routes.auth import router as auth_router
from app.routes.tareas import router as tareas_router
from app.routes.perfil import router as perfil_router
from app.routes.admin import router as admin_router
from app.routes.modos import router as modos_router          # Solo una vez
from app.routes.estadisticas import router as stats_router
from app.routes.metas import router as metas_router
from app.routes.ayuda import router as ayuda_router
from app.routes.categorias import router as categorias_router
from app.routes.logros import router as logros_router       # ¡AQUÍ ESTABA FALTANDO!

# Crear la app
app = FastAPI(
    title="TimeWise API",
    description="Gestión de tareas, metas, estadísticas, modos, perfil, logros motivacionales y más",
    version="2.0.0",
    contact={
        "name": "Ángel Gaviria, Luisa Ospino, Sara Hoyos",
        "email": "timewiseenterprise.sas@gmail.com"
    }
)

# CORS: Permitir todo en desarrollo (Flutter, web, móvil)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === INCLUIR TODOS LOS ROUTERS (sin duplicados) ===
app.include_router(auth_router)
app.include_router(tareas_router)
app.include_router(perfil_router)
app.include_router(admin_router)
app.include_router(modos_router)        # Solo una vez
app.include_router(stats_router)
app.include_router(metas_router)
app.include_router(ayuda_router)
app.include_router(categorias_router)
app.include_router(logros_router)       # ¡AHORA SÍ APARECE!

# Crear carpeta database al iniciar
@app.on_event("startup")
def startup():
    os.makedirs("app/database", exist_ok=True)
    print("Carpeta 'database' asegurada")

# Ruta raíz
@app.get("/")
def home():
    return {
        "message": "TimeWise API v2 - ¡COMPLETA, MOTIVACIONAL Y LISTA PARA LA DEFENSA!",
        "integrantes": [
            {"nombres": "Ángel Manuel", "apellidos": "Gaviria Ramírez"},
            {"nombres": "Luisa Fernanda", "apellidos": "Gómez Ospino"},
            {"nombres": "Sara Sofía", "apellidos": "Romero Hoyos"}
        ],
        "docs": "/docs",
        "redoc": "/redoc",
        "nuevo": "¡Ahora tienes logros motivacionales y trofeos!"
    }