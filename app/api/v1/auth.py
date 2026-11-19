from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.models.models import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    is_token_revoked
)
from app.core.logging import registrar_auditoria

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión y obtener tokens JWT RS256")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.nombre_usuario == payload.usuario).first()
    
    if not usuario or not verify_password(payload.contrasena, usuario.contrasena_hash):
        registrar_auditoria(db, payload.usuario, "LOGIN", "usuarios", "FAILED", "Credenciales invalidas")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not usuario.activo:
        registrar_auditoria(db, payload.usuario, "LOGIN", "usuarios", "FAILED", "Usuario inactivo")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta se encuentra inactiva.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = {
        "sub": usuario.nombre_usuario,
        "rol": usuario.rol,
        "id_medico": usuario.id_medico,
        "id_usuario": usuario.id_usuario,
        "type": "access"
    }

    access_token = create_access_token(claims)
    refresh_token = create_refresh_token({
        "sub": usuario.nombre_usuario,
        "rol": usuario.rol,
        "id_usuario": usuario.id_usuario
    })

    registrar_auditoria(db, usuario.nombre_usuario, "LOGIN", "usuarios", "SUCCESS", f"Rol: {usuario.rol}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 900,
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=TokenResponse, summary="Renovar access_token con refresh_token")
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    token = payload.refresh_token
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revocado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        decoded = decode_token(token)
        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token proporcionado no es un refresh token.",
            )

        username = decoded.get("sub")
        usuario = db.query(Usuario).filter(Usuario.nombre_usuario == username).first()
        if not usuario or not usuario.activo:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario invalido")

        # Rotar tokens
        revoke_token(token)
        new_access_token = create_access_token({
            "sub": usuario.nombre_usuario,
            "rol": usuario.rol,
            "id_medico": usuario.id_medico,
            "id_usuario": usuario.id_usuario,
            "type": "access"
        })
        new_refresh_token = create_refresh_token({
            "sub": usuario.nombre_usuario,
            "rol": usuario.rol,
            "id_usuario": usuario.id_usuario
        })

        registrar_auditoria(db, username, "REFRESH_TOKEN", "usuarios", "SUCCESS")

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 900,
            "refresh_token": new_refresh_token
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado o inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
