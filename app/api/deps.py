from typing import List, Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_token, is_token_revoked
from app.models.models import Usuario

security_bearer = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Valida el Bearer Token RS256 y retorna los claims del usuario"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida. Proporcione un token Bearer válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado. Inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        rol: str = payload.get("rol")
        token_type: str = payload.get("type", "access")

        if username is None or rol is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o malformado.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return {
            "username": username,
            "rol": rol,
            "id_medico": payload.get("id_medico"),
            "token": token
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o firma inválida.",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(roles_permitidos: List[str]):
    """Dependencia de autorización RBAC declarativa por endpoint"""
    def rol_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_rol = current_user.get("rol")
        if user_rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: el rol '{user_rol}' no tiene permisos para este recurso."
            )
        return current_user
    return rol_checker
