from pydantic import BaseModel, Field, field_validator

class DispositivoRegistrarRequest(BaseModel):
    sistema_operativo: str = Field(..., example="WearOS")
    fcm_token: str = Field(..., min_length=1, max_length=255, example="abc123xyz_token_largo_de_firebase")

    @field_validator("sistema_operativo")
    def validar_so(cls, v: str) -> str:
        sistemas_validos = {"WearOS", "watchOS", "otro"}
        if v not in sistemas_validos:
            raise ValueError(f"sistema_operativo debe ser uno de: {', '.join(sorted(sistemas_validos))}")
        return v

class DispositivoRegistrarResponse(BaseModel):
    mensaje: str = "Dispositivo vinculado correctamente."
