from typing import List
from pydantic import BaseModel, Field

class PacienteColaItem(BaseModel):
    id_triaje: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    nivel_urgencia: int = Field(..., ge=1, le=5, example=1)
    tiempo_espera_minutos: int = Field(..., ge=0, example=4)

class ColaResponse(BaseModel):
    especialidad: str = Field(..., example="Cardiologia")
    total_espera: int = Field(..., example=2)
    pacientes: List[PacienteColaItem] = []
