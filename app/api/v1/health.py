from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.services.fcm_service import fcm_service

router = APIRouter(tags=["Salud del Sistema"])

@router.get("/healthz", summary="Verificar estado de salud y dependencias del sistema (RF-14)")
def health_check(db: Session = Depends(get_db)):
    # 1. Base de datos
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. FCM
    fcm_status = "ok" if fcm_service.initialized else "mock_mode"

    overall_status = "healthy" if db_status == "ok" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "fcm": fcm_status,
        "version": "2.0.0"
    }
