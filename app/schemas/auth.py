from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    usuario: str = Field(..., min_length=3, max_length=80, example="recepcion1")
    contrasena: str = Field(..., min_length=4, max_length=128, example="admin123")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
