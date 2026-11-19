from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.database import get_db
from app.api.deps import require_role
from app.schemas.dispositivo import DispositivoRegistrarRequest, DispositivoRegistrarResponse
from app.models.models import DispositivoWearable, Medico
from app.services.fcm_service import fcm_service
from app.core.logging import registrar_auditoria

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos Wearables"])

class ProbarAlertaRequest(BaseModel):
    canal: Optional[str] = Field("aitriage_umb_alerta", example="aitriage_umb_alerta")
    nivel_urgencia: int = Field(1, ge=1, le=5)
    especialidad: str = Field("Cardiologia", example="Cardiologia")

@router.post(
    "/registrar",
    response_model=DispositivoRegistrarResponse,
    status_code=status.HTTP_200_OK,
    summary="Registrar o actualizar token FCM del reloj inteligente WearOS del médico"
)
def registrar_dispositivo(
    payload: DispositivoRegistrarRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role(["medico"]))
):
    id_medico = current_user.get("id_medico")
    if not id_medico:
        medico_db = db.query(Medico).filter(Medico.correo.ilike(f"%{current_user['username']}%")).first()
        if medico_db:
            id_medico = medico_db.id_medico
        else:
            medico_db = Medico(
                nombre_completo=f"Dr(a). {current_user['username'].capitalize()}",
                correo=f"{current_user['username']}@ips-bogota.gov.co",
                id_especialidad=1,
                activo=True
            )
            db.add(medico_db)
            db.flush()
            id_medico = medico_db.id_medico

    disp = db.query(DispositivoWearable).filter(
        DispositivoWearable.id_medico == id_medico,
        DispositivoWearable.sistema_operativo == payload.sistema_operativo
    ).first()

    if disp:
        disp.fcm_token = payload.fcm_token
        disp.registrado_en = datetime.now(timezone.utc)
    else:
        disp = DispositivoWearable(
            id_medico=id_medico,
            sistema_operativo=payload.sistema_operativo,
            fcm_token=payload.fcm_token,
            registrado_en=datetime.now(timezone.utc)
        )
        db.add(disp)

    db.commit()

    registrar_auditoria(
        db,
        current_user["username"],
        "REGISTRAR_DISPOSITIVO",
        f"dispositivo:{disp.id_dispositivo}",
        "SUCCESS",
        f"SO: {payload.sistema_operativo}"
    )

    return DispositivoRegistrarResponse(mensaje="Dispositivo vinculado correctamente.")

@router.post(
    "/probar-alerta",
    status_code=status.HTTP_200_OK,
    summary="Enviar una alerta de prueba inmediata al Huawei Watch GT5 / Smartphone"
)
def probar_alerta_wearable(payload: ProbarAlertaRequest):
    """
    Envía una alerta de prueba háptica al reloj inteligente Huawei Watch GT5
    a través del smartphone sin requerir tokens FCM.
    """
    titulo = "AI-Triage — Alerta Médica"
    cuerpo = f"🚨 CASO CRÍTICO: Paciente clasificado en Nivel {payload.nivel_urgencia} ({payload.especialidad}). Favor acudir a urgencias."
    fcm_service.enviar_push_universal_huawei(
        titulo=titulo,
        cuerpo=cuerpo,
        nivel_urgencia=payload.nivel_urgencia,
        especialidad=payload.especialidad,
        topic=payload.canal
    )
    return {
        "status": "enviado",
        "canal": payload.canal,
        "mensaje": f"Alerta enviada al canal {payload.canal}. Si tienes la app ntfy o la web abierta en tu celular, tu Huawei Watch GT5 vibrará de inmediato."
    }
