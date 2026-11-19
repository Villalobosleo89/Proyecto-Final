import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, SmallInteger, Numeric, Boolean, DateTime, ForeignKey, Text, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Especialidad(Base):
    __tablename__ = "especialidades"
    
    id_especialidad = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(80), nullable=False, unique=True)
    activa = Column(Boolean, nullable=False, default=True)
    
    medicos = relationship("Medico", back_populates="especialidad")

class Medico(Base):
    __tablename__ = "medicos"
    
    id_medico = Column(String(36), primary_key=True, default=generate_uuid)
    nombre_completo = Column(String(120), nullable=False)
    correo = Column(String(120), nullable=False, unique=True)
    id_especialidad = Column(Integer, ForeignKey("especialidades.id_especialidad"), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    
    especialidad = relationship("Especialidad", back_populates="medicos")
    dispositivos = relationship("DispositivoWearable", back_populates="medico", cascade="all, delete-orphan")
    triajes = relationship("Triaje", back_populates="medico_asignado")

class DispositivoWearable(Base):
    __tablename__ = "dispositivos_wearable"
    
    id_dispositivo = Column(String(36), primary_key=True, default=generate_uuid)
    id_medico = Column(String(36), ForeignKey("medicos.id_medico", ondelete="CASCADE"), nullable=False)
    sistema_operativo = Column(String(20), nullable=False)
    fcm_token = Column(String(255), nullable=False)
    registrado_en = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    
    medico = relationship("Medico", back_populates="dispositivos")

class Paciente(Base):
    __tablename__ = "pacientes"
    
    id_paciente = Column(String(36), primary_key=True, default=generate_uuid)
    id_origen_clinica = Column(String(40), nullable=False, unique=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    
    triajes = relationship("Triaje", back_populates="paciente")

class Triaje(Base):
    __tablename__ = "triajes"
    
    id_triaje = Column(String(36), primary_key=True, default=generate_uuid)
    id_paciente = Column(String(36), ForeignKey("pacientes.id_paciente", ondelete="RESTRICT"), nullable=False)
    texto_anonimizado = Column(Text, nullable=False)
    nivel_urgencia = Column(SmallInteger, nullable=False)  # 1 a 5
    puntaje_severidad = Column(Numeric(5, 2), nullable=False)  # 0.00 a 100.00
    especialidad_asignada = Column(String(80), ForeignKey("especialidades.nombre"), nullable=False)
    id_medico_asignado = Column(String(36), ForeignKey("medicos.id_medico"), nullable=True)
    alerta_push_enviada = Column(Boolean, nullable=False, default=False)
    creado_en = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    
    paciente = relationship("Paciente", back_populates="triajes")
    medico_asignado = relationship("Medico", back_populates="triajes")
    entidades = relationship("EntidadClinica", back_populates="triaje", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('nivel_urgencia >= 1 AND nivel_urgencia <= 5', name='chk_nivel_urgencia'),
        CheckConstraint('puntaje_severidad >= 0.0 AND puntaje_severidad <= 100.0', name='chk_puntaje_severidad'),
        Index('idx_triajes_cola', 'id_medico_asignado', 'nivel_urgencia', 'puntaje_severidad', 'creado_en'),
    )

class EntidadClinica(Base):
    __tablename__ = "entidades_clinicas"
    
    id_entidad = Column(Integer, primary_key=True, autoincrement=True)
    id_triaje = Column(String(36), ForeignKey("triajes.id_triaje", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(20), nullable=False)
    valor = Column(String(160), nullable=False)
    confianza = Column(Numeric(4, 3), nullable=True)
    
    triaje = relationship("Triaje", back_populates="entidades")
    
    __table_args__ = (
        Index('idx_entidades_triaje', 'id_triaje'),
    )

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id_usuario = Column(String(36), primary_key=True, default=generate_uuid)
    nombre_usuario = Column(String(80), nullable=False, unique=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)  # 'admin' o 'medico'
    id_medico = Column(String(36), ForeignKey("medicos.id_medico"), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)

class AuditoriaEvento(Base):
    __tablename__ = "auditoria_eventos"
    
    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    usuario = Column(String(80), nullable=True)
    accion = Column(String(80), nullable=False)
    entidad_afectada = Column(String(80), nullable=True)
    correlation_id = Column(String(36), nullable=False)
    resultado = Column(String(20), nullable=False)
    detalle = Column(Text, nullable=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, default=utc_now)
