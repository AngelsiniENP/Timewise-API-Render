# app/routes/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Boolean, Text, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime   # ← ¡ESTA LÍNEA FALTABA!
from sqlalchemy.orm import relationship   # ← ESTA LÍNEA FALTABA

Base = declarative_base()

# Tabla: Roles
class Rol(Base):
    __tablename__ = "Roles"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String, unique=True)
    descripcion = Column(Text)

# Tabla: Tipos_de_tareas (Categorías)
class TipoTarea(Base):
    __tablename__ = "Tipos_de_tareas"
    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    descripcion = Column(Text)
    color_default = Column(String)
    creada_por_admin = Column(Boolean, default=True)

# Tabla: Modos_de_tareas
class ModoTarea(Base):
    __tablename__ = "Modos_de_tareas"
    id_modo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    descripcion = Column(Text)

class Usuario(Base):
    __tablename__ = "Usuario"
    id_usuario = Column(Integer, primary_key=True, index=True)
    id_rol = Column(Integer, ForeignKey("Roles.id_rol"))
    logros = relationship("Logro", back_populates="usuario", cascade="all, delete-orphan")  
    
    # ¡¡CAMBIADOS!! → coinciden con la tabla real
    nombre = Column(String, name="nombre")           # ← singular
    apellido = Column(String, name="apellido")       # ← singular
    
    edad = Column(Integer)
    correo = Column(String, unique=True, index=True)
    contrasena = Column(String)
    foto_perfil = Column(String)
    fecha_registro = Column(DateTime)
    ultimo_login = Column(DateTime)
    token_reset = Column(String)
    token_reset_expiry = Column(DateTime)

    # Para seguir usando .nombres y .apellidos en el código (opcional pero cómodo)
    @property
    def nombres(self):
        return self.nombre

    @property
    def apellidos(self):
        return self.apellido

    @nombres.setter
    def nombres(self, value):
        self.nombre = value

    @apellidos.setter
    def apellidos(self, value):
        self.apellido = value
# Tabla: Usuario_Modos (relación muchos-a-muchos)

class UsuarioModo(Base):
    __tablename__ = "Usuario_Modos"
    id_usuario_modo = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"))
    id_modo = Column(Integer, ForeignKey("Modos_de_tareas.id_modo"))
    fecha_activacion = Column(DateTime)

# Tabla: Tareas
class Tarea(Base):
    __tablename__ = "Tareas"
    id_tarea = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"))
    id_categoria = Column(Integer, ForeignKey("Tipos_de_tareas.id_categoria"))
    titulo = Column(String)
    descripcion = Column(Text)
    fecha = Column(Date)
    hora = Column(Time)
    prioridad = Column(String)
    duracion_estimada = Column(Integer)
    estado = Column(String)
    etiqueta_color = Column(String)
    repeticion = Column(String)
    recordatorio_minutos = Column(Integer)

# Tabla: Repeticiones_Tareas
class RepeticionTarea(Base):
    __tablename__ = "Repeticiones_Tareas"
    id_repeticion = Column(Integer, primary_key=True, index=True)
    id_tarea = Column(Integer, ForeignKey("Tareas.id_tarea"))
    dia_semana = Column(String)
    fecha_fin = Column(Date)

# Tabla: Notificaciones
class Notificacion(Base):
    __tablename__ = "Notificaciones"
    id_notificacion = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"))
    id_tarea = Column(Integer, ForeignKey("Tareas.id_tarea"))
    tipo = Column(String)
    mensaje = Column(Text)
    fecha_envio = Column(DateTime)
    enviada = Column(Boolean, default=False)

# Tabla: Estadisticas
class Estadistica(Base):
    __tablename__ = "Estadisticas"
    id_estadistica = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"))
    id_categoria = Column(Integer, ForeignKey("Tipos_de_tareas.id_categoria"))
    tiempo_invertido = Column(Integer, default=0)
    tareas_completadas = Column(Integer, default=0)
    periodo = Column(String)
    fecha_inicio = Column(Date)
    productividad = Column(Float)

# Tabla: Metas
class Meta(Base):
    __tablename__ = "Metas"
    id_meta = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"))
    descripcion = Column(Text)
    frecuencia = Column(String)
    objetivo = Column(Integer)
    progreso = Column(Integer, default=0)
    fecha_inicio = Column(Date)
    completada = Column(Boolean, default=False)

# Tabla: Cronometros
class Cronometro(Base):
    __tablename__ = "Cronometros"
    id_cronometro = Column(Integer, primary_key=True, index=True)
    id_tarea = Column(Integer, ForeignKey("Tareas.id_tarea"))
    inicio = Column(DateTime)
    fin = Column(DateTime)
    duracion_real = Column(Integer)
    pausado = Column(Boolean, default=False)

# Tabla: Sync_Externo
class SyncExterno(Base):
    __tablename__ = "Sync_Externo"
    id_sync = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"))
    tipo_calendario = Column(String)
    token_api = Column(String)
    ultima_sync = Column(DateTime)

# Tabla: Tutoriales
class Tutorial(Base):
    __tablename__ = "Tutoriales"
    id_tutorial = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    contenido = Column(Text)

# app/routes/models.py → AÑADE ESTO AL FINAL

class Logro(Base):
    __tablename__ = "logros"

    id_logro = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario"), nullable=False)  # ¡¡ASÍ!!
    mensaje = Column(Text, nullable=False)
    tipo = Column(String(20), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario", back_populates="logros")

# Y agrega esto en la clase Usuario (si no lo tienes):
Usuario.logros = relationship("Logro", back_populates="usuario", cascade="all, delete-orphan")