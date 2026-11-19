import logging
import json
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import AuditoriaEvento

# ContextVar para propagar correlation_id a través de peticiones asíncronas
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "correlation_id": correlation_id_ctx.get() or "-"
        }
        if hasattr(record, "props"):
            log_obj.update(record.props)
        return json.dumps(log_obj)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

def registrar_auditoria(
    db: Session,
    usuario: Optional[str],
    accion: str,
    entidad: Optional[str],
    resultado: str,
    detalle: Optional[str] = None
):
    """Escribe evento en tabla auditoria_eventos en modo solo-apéndice (RF-12, RN-07)"""
    try:
        corr_id = correlation_id_ctx.get() or "system-event"
        evento = AuditoriaEvento(
            usuario=usuario,
            accion=accion,
            entidad_afectada=entidad,
            correlation_id=corr_id,
            resultado=resultado,
            detalle=detalle,
            creado_en=datetime.now(timezone.utc)
        )
        db.add(evento)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.getLogger("aitriage.auditoria").error(f"Error registrando auditoria: {e}")
