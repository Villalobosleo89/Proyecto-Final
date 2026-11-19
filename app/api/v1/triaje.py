from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.api.deps import require_role
from app.schemas.triaje import TriajeAnalizarRequest, TriajeResponse
from app.models.models import Paciente, Triaje, EntidadClinica, Medico, DispositivoWearable, Especialidad
from app.ml.triage_engine import triage_engine
from app.services.fcm_service import fcm_service
from app.core.logging import registrar_auditoria

router = APIRouter(prefix="/triaje", tags=["Triaje Clínico"])

@router.post(
    "/analizar",
    response_model=TriajeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analizar texto clínico con IA, calcular triaje y derivar a cola hospitalaria"
)
def analizar_triaje(
    payload: TriajeAnalizarRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    # 1. Validación de longitud de texto (RF-02)
    texto = payload.texto_sintomas.strip()
    if len(texto) < 30 or len(texto) > 10000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{
                "loc": ["body", "texto_sintomas"],
                "msg": "El texto clínico debe tener entre 30 y 10.000 caracteres.",
                "type": "value_error.length"
            }]
        )

    # 2. Idempotencia y control de duplicados (Sección 8.5 / 409 Conflict)
    paciente_existente = db.query(Paciente).filter(
        Paciente.id_origen_clinica == payload.id_origen_clinica
    ).first()
    
    if paciente_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El caso con id_origen_clinica '{payload.id_origen_clinica}' ya fue registrado previamente."
        )

    # 3. Ejecutar Pipeline de Inferencia IA (RF-03, RF-04, RF-05, RF-06)
    try:
        resultado_ia = triage_engine.procesar(texto)
    except Exception as e:
        registrar_auditoria(db, current_user["username"], "ANALIZAR_TRIAJE", "triajes", "FAILED", f"Error motor IA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el procesamiento del motor de inferencia clínica."
        )

    # Asegurar que la especialidad exista en catálogo
    esp_nombre = resultado_ia["especialidad_asignada"]
    esp_db = db.query(Especialidad).filter(Especialidad.nombre == esp_nombre).first()
    if not esp_db:
        # Fallback seguro
        esp_nombre = "Medicina general"

    # 4. Persistencia Transaccional ACID en PostgreSQL (RF-07)
    try:
        # Crear Paciente
        nuevo_paciente = Paciente(id_origen_clinica=payload.id_origen_clinica)
        db.add(nuevo_paciente)
        db.flush()

        # Determinar si requiere alerta push
        nivel = resultado_ia["nivel_urgencia"]
        alerta_enviada = False

        nuevo_triaje = Triaje(
            id_paciente=nuevo_paciente.id_paciente,
            texto_anonimizado=resultado_ia["texto_anonimizado"],
            nivel_urgencia=nivel,
            puntaje_severidad=resultado_ia["puntaje_severidad"],
            especialidad_asignada=esp_nombre,
            alerta_push_enviada=False
        )
        db.add(nuevo_triaje)
        db.flush()

        # Guardar Entidades Clínicas (Medical NER)
        for ent in resultado_ia["entidades"]:
            entidad_db = EntidadClinica(
                id_triaje=nuevo_triaje.id_triaje,
                tipo=ent["tipo"],
                valor=ent["valor"],
                confianza=ent["confianza"]
            )
            db.add(entidad_db)

        # 5. Notificación Push a Wearables si es Nivel 1 o 2 (RF-09, Sección 10)
        if nivel in [1, 2]:
            # Buscar tokens de médicos activos de esa especialidad
            tokens_query = db.query(DispositivoWearable.fcm_token).join(
                Medico, Medico.id_medico == DispositivoWearable.id_medico
            ).join(
                Especialidad, Especialidad.id_especialidad == Medico.id_especialidad
            ).filter(
                Especialidad.nombre == esp_nombre,
                Medico.activo == True
            ).all()

            tokens = [t[0] for t in tokens_query]
            fcm_result = fcm_service.enviar_alerta_critica(
                tokens_dispositivos=tokens,
                id_triaje=nuevo_triaje.id_triaje,
                nivel_urgencia=nivel,
                especialidad=esp_nombre
            )
            alerta_enviada = fcm_result.get("enviados", 0) > 0
            nuevo_triaje.alerta_push_enviada = alerta_enviada

        db.commit()
        db.refresh(nuevo_triaje)

        registrar_auditoria(
            db,
            current_user["username"],
            "ANALIZAR_TRIAJE",
            f"triaje:{nuevo_triaje.id_triaje}",
            "SUCCESS",
            f"Nivel: {nivel}, Puntaje: {nuevo_triaje.puntaje_severidad}, Esp: {esp_nombre}, Alerta: {alerta_enviada}"
        )

        return {
            "id_triaje": nuevo_triaje.id_triaje,
            "especialidad_asignada": nuevo_triaje.especialidad_asignada,
            "nivel_urgencia": nuevo_triaje.nivel_urgencia,
            "puntaje_severidad": float(nuevo_triaje.puntaje_severidad),
            "alerta_push_enviada": nuevo_triaje.alerta_push_enviada
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # Detectar violación de unicidad (ID duplicado) y devolver 409 en lugar de 500
        err_str = str(e).lower()
        if "unique constraint" in err_str or "unique" in err_str or "id_origen_clinica" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El caso con id_origen_clinica '{payload.id_origen_clinica}' ya fue registrado. Use un ID diferente."
            )
        registrar_auditoria(db, current_user["username"], "ANALIZAR_TRIAJE", "triajes", "FAILED", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la persistencia transaccional del triaje: {str(e)}"
        )
