from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.api.deps import require_role
from app.schemas.colas import ColaResponse
from app.services.queue_service import obtener_cola_especialidad
from app.core.logging import registrar_auditoria

router = APIRouter(prefix="/colas", tags=["Colas de Atención"])

@router.get(
    "",
    response_model=ColaResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar cola de atención hospitalaria por especialidad (orden dinámico)"
)
def consultar_cola(
    especialidad: str = Query(..., description="Nombre de la especialidad clínica (ej: Cardiologia)", examples=["Cardiologia"]),
    limite: int = Query(20, ge=1, le=100, description="Cantidad máxima de casos a retornar (1 - 100)", examples=[10]),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role(["medico"]))
):
    resultado = obtener_cola_especialidad(db, especialidad, limite)
    
    if "error" in resultado and resultado["error"] == "especialidad_no_encontrada":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La especialidad '{especialidad}' no existe en el catálogo institucional o no está activa."
        )

    registrar_auditoria(
        db,
        current_user["username"],
        "CONSULTAR_COLA",
        f"especialidad:{especialidad}",
        "SUCCESS",
        f"Total en espera: {resultado['total_espera']}, Limite: {limite}"
    )

    return resultado
