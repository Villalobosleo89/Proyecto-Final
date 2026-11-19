from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.models.models import Triaje, Especialidad

def obtener_cola_especialidad(
    db: Session,
    especialidad: str,
    limite: int = 20
) -> Dict[str, Any]:
    """
    Consulta optimizada de la cola dinámica de atención hospitalaria (Sección 6.4).
    Orden: nivel_urgencia ASC, puntaje_severidad DESC, creado_en ASC.
    """
    # 1. Validar que la especialidad exista en el catálogo
    esp = db.query(Especialidad).filter(
        Especialidad.nombre == especialidad,
        Especialidad.activa == True
    ).first()
    
    if not esp:
        return {"error": "especialidad_no_encontrada"}

    # 2. Consultar triajes no asignados
    query = db.query(Triaje).filter(
        Triaje.especialidad_asignada == especialidad,
        Triaje.id_medico_asignado.is_(None)
    ).order_by(
        asc(Triaje.nivel_urgencia),
        desc(Triaje.puntaje_severidad),
        asc(Triaje.creado_en)
    )

    total_espera = query.count()
    triajes = query.limit(limite).all()

    ahora = datetime.now(timezone.utc)
    pacientes_cola: List[Dict[str, Any]] = []

    for t in triajes:
        creado = t.creado_en
        # Manejo de timezone
        if creado.tzinfo is None:
            creado = creado.replace(tzinfo=timezone.utc)
        
        tiempo_espera = max(0, int((ahora - creado).total_seconds() / 60))

        pacientes_cola.append({
            "id_triaje": t.id_triaje,
            "nivel_urgencia": t.nivel_urgencia,
            "tiempo_espera_minutos": tiempo_espera
        })

    return {
        "especialidad": especialidad,
        "total_espera": total_espera,
        "pacientes": pacientes_cola
    }
