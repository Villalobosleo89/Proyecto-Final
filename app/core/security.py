import os
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set
from jose import jwt, JWTError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from app.config import settings

# Revocación de refresh tokens en memoria (RF-15)
REVOKED_TOKENS: Set[str] = set()

def ensure_rsa_keys():
    """Genera llaves RSA para firma RS256 si no existen en disco"""
    settings.CERTS_DIR.mkdir(parents=True, exist_ok=True)
    if not settings.JWT_PRIVATE_KEY_PATH.exists() or not settings.JWT_PUBLIC_KEY_PATH.exists():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(settings.JWT_PRIVATE_KEY_PATH, "wb") as f:
            f.write(private_pem)
        with open(settings.JWT_PUBLIC_KEY_PATH, "wb") as f:
            f.write(public_pem)

# Asegurar existencia de llaves al importar
ensure_rsa_keys()

def get_private_key() -> str:
    with open(settings.JWT_PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
        return f.read()

def get_public_key() -> str:
    with open(settings.JWT_PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
        return f.read()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)  # costo >= 12 (RN-04)
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())
    })
    return jwt.encode(to_encode, get_private_key(), algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "refresh"
    })
    return jwt.encode(to_encode, get_private_key(), algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, get_public_key(), algorithms=[settings.JWT_ALGORITHM])

def revoke_token(token: str):
    REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    return token in REVOKED_TOKENS
