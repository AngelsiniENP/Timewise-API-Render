# app/database/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# RUTA BASE CORREGIDA
BASE_DIR = Path(__file__).resolve().parent.parent  # → TimeWise-API/
DB_PATH = BASE_DIR / "database" / "timewise.db"
SQL_FILE = BASE_DIR / "database" / "create-timewise.sql"  # ← CORREGIDO

# Crear directorio
DB_PATH.parent.mkdir(exist_ok=True)

# Solo crear si no existe
if not DB_PATH.exists():
    print("Creando base de datos desde SQL...")
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.close()
    print(f"Base de datos creada: {DB_PATH}")
else:
    print(f"Base de datos ya existe: {DB_PATH} → Datos preservados")

# Motor SQLAlchemy
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()