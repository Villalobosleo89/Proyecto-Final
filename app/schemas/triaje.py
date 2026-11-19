from typing import List, Optional
from pydantic import BaseModel, Field

class TriajeAnalizarRequest(BaseModel):
    id_origen_clinica: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Identificador del paciente en el sistema de la IPS (ej: DOC-9982)",
        example="DOC-9982"
    )
    texto_sintomas: str = Field(
        ...,
        min_length=30,
        max_length=10000,
        description="Texto no estructurado de la historia clínica o descripción de síntomas (30 - 10.000 caracteres)",
        example="Paciente masculino de 45 anos ingresa con dolor toracico opresivo, sudoracion fria y dificultad para respirar..."
    )

class EntidadClinicaSchema(BaseModel):
    tipo: str
    valor: str
    confianza: Optional[float] = 1.0

class TriajeResponse(BaseModel):
    id_triaje: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    especialidad_asignada: str = Field(..., example="Cardiologia")
    nivel_urgencia: int = Field(..., ge=1, le=5, example=1)
    puntaje_severidad: float = Field(..., ge=0.0, le=100.0, example=85.0)
    alerta_push_enviada: bool = Field(..., example=True)

class TriajeDetalleResponse(TriajeResponse):
    id_paciente: str
    texto_anonimizado: str
    creado_en: str
    entidades: List[EntidadClinicaSchema] = []
