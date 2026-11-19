import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings

# Soporte para portabilidad en USB (PyInstaller portable)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Triage"
    VERSION: str = "4.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Base de datos SQLite local (Ruta relativa portatil para funcionar en cualquier USB)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/aitriage.db")
    
    # Directorio de certificados y llaves RSA
    CERTS_DIR: Path = BASE_DIR / "certs"
    JWT_PRIVATE_KEY_PATH: Path = BASE_DIR / "certs" / "jwt_private.pem"
    JWT_PUBLIC_KEY_PATH: Path = BASE_DIR / "certs" / "jwt_public.pem"
    
    # Configuracion JWT (RFC 7519 / RS256)
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 3600 segundos
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas
    
    # FCM (Firebase Cloud Messaging)
    FCM_CREDENTIALS_PATH: Path = BASE_DIR / "certs" / "firebase_service_account.json"
    MOCK_FCM_IF_UNAVAILABLE: bool = True
    
    # Canal Push Universal para Smartwatches sin Google Play (Huawei Watch GT5, HarmonyOS, etc.)
    NTFY_TOPIC: str = os.getenv("NTFY_TOPIC", "aitriage_umb_alerta")
    
    # Gemini API (Google AI) para clasificacion inteligente de triaje
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Entorno
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
