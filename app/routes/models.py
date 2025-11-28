# app/routes/models.py → VERSIÓN FINAL LIMPIA Y FUNCIONAL (2025)
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Boolean, Text, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


# ==================== TABLAS PRINCIPALES ====================

class Rol(Base):
    __tablename__ = "Roles"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)


class TipoTarea(Base):
    __tablename__ = "Tipos_de_tareas"
    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)
    color_default = Column(String, default="#3788d8")
    creada_por_admin = Column(Boolean, default=True)

    tareas = relationship("Tarea", back_populates="categoria")


class ModoTarea(Base):
    __tablename__ = "Modos_de_tareas"
    id_modo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)


class Usuario(Base):
    __tablename__ = "Usuario"
    id_usuario = Column(Integer, primary_key=True, index=True)
    id_rol = Column(Integer, ForeignKey("Roles.id_rol"), default=2)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    edad = Column(Integer)
    correo = Column(String, unique=True, index=True, nullable=False)
    contrasena = Column(String, nullable=False)
    foto_perfil = Column(String)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    ultimo_login = Column(DateTime)
    token_reset = Column(String)
    token_reset_expiry = Column(DateTime)

    # Relaciones
    tareas = relationship("Tarea", back_populates="usuario", cascade="all, delete-orphan")
    logros = relationship("Logro", back_populates="usuario", cascade="all, delete-orphan")


class UsuarioModo(Base):
    __tablename__ = "Usuario_Modos"
    id_usuario_modo = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"), nullable=False)
    id_modo = Column(Integer, ForeignKey("Modos_de_tareas.id_modo"), nullable=False)
    fecha_activacion = Column(DateTime, default=datetime.utcnow)


# ==================== TAREA → SIN CAMPOS FANTASMA ====================
class Tarea(Base):
    __tablename__ = "Tareas"

    id_tarea = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"), nullable=False)
    id_categoria = Column(Integer, ForeignKey("Tipos_de_tareas.id_categoria"), nullable=True)

    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha = Column(Date, nullable=False)
    hora = Column(String, nullable=True)        # ← CAMBIADO A STRING
    prioridad = Column(String, default="media")
    estado = Column(String, default="pendiente")
    etiqueta_color = Column(String, nullable=True)
    recordatorio_minutos = Column(Integer, nullable=True)

    # relaciones...
    usuario = relationship("Usuario", back_populates="tareas")
    categoria = relationship("TipoTarea", back_populates="tareas")


class Meta(Base):
    __tablename__ = "Metas"
    id_meta = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"), nullable=False)
    descripcion = Column(Text, nullable=False)
    frecuencia = Column(String, nullable=False)
    objetivo = Column(Integer, nullable=False)
    progreso = Column(Integer, default=0)
    fecha_inicio = Column(Date)
    completada = Column(Boolean, default=False)


class Estadistica(Base):
    __tablename__ = "Estadisticas"
    id_estadistica = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"), nullable=False)
    id_categoria = Column(Integer, ForeignKey("Tipos_de_tareas.id_categoria"), nullable=False)
    tiempo_invertido = Column(Integer, default=0)
    tareas_completadas = Column(Integer, default=0)
    periodo = Column(String, default="semanal")
    fecha_inicio = Column(Date)
    productividad = Column(Float, default=0.0)


class Cronometro(Base):
    __tablename__ = "Cronometros"
    id_cronometro = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"), nullable=False)
    id_tarea = Column(Integer, ForeignKey("Tareas.id_tarea"), nullable=True)
    inicio = Column(DateTime, nullable=False)
    fin = Column(DateTime)
    duracion_segundos = Column(Integer)
    

class Logro(Base):
    __tablename__ = "logros"
    id_logro = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="logros")