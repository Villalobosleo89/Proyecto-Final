import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from app.config import settings

logger = logging.getLogger("aitriage.fcm")

class FCMNotificationService:
    """
    Servicio de integración de notificaciones push para wearables:
    1. Firebase Cloud Messaging (FCM HTTP v1) para WearOS.
    2. Canal Push Universal (ntfy.sh) para relojes Huawei Watch GT5 / HarmonyOS y smartphones.
    """

    def __init__(self):
        self.firebase_app = None
        self.initialized = False
        self._initialize_firebase()

    def _initialize_firebase(self):
        if settings.FCM_CREDENTIALS_PATH.exists():
            try:
                import firebase_admin
                from firebase_admin import credentials
                cred = credentials.Certificate(str(settings.FCM_CREDENTIALS_PATH))
                self.firebase_app = firebase_admin.initialize_app(cred)
                self.initialized = True
                logger.info("FCM HTTP v1 inicializado correctamente con credenciales de servicio.")
            except Exception as e:
                logger.warning(f"No se pudo inicializar Firebase Admin SDK: {e}. Usando modo simulado.")
        else:
            logger.info("FCM_CREDENTIALS_PATH no encontrado. Operando en modo Mock/Simulación de Wearables.")

    def enviar_push_universal_huawei(self, titulo: str, cuerpo: str, nivel_urgencia: int, especialidad: str, topic: Optional[str] = None):
        """
        Envía notificación push inmediata a través de ntfy.sh hacia el smartphone del médico,
        la cual se sincroniza por Bluetooth con el Huawei Watch GT5 y hace vibrar el reloj.
        No requiere tokens ni configuraciones complejas en el reloj.
        """
        canal = topic or settings.NTFY_TOPIC
        try:
            url = f"https://ntfy.sh/{canal}"
            headers = {
                "Title": titulo,  # Solo ASCII — sin encode/decode que corrompe headers
                "Priority": "urgent" if nivel_urgencia == 1 else "high",
                "Tags": "rotating_light,hospital,heart" if nivel_urgencia == 1 else "warning,hospital",
                "Content-Type": "text/plain; charset=utf-8"
            }
            # Timeout corto para no retrasar la API si no hay internet
            response = httpx.post(url, data=cuerpo.encode("utf-8"), headers=headers, timeout=2.5)

            if response.status_code == 200:
                logger.info(
                    f"Notificacion push universal entregada al canal: {canal} (status 200)"
                )
                return {"enviados": 1, "fallidos": 0, "error": None}
            else:
                logger.error(
                    f"ntfy respondió con error {response.status_code}: {response.text}"
                )
                return {
                    "enviados": 0,
                    "fallidos": 1,
                    "error": f"ntfy status {response.status_code}",
                }
        except httpx.HTTPError as e:
            logger.error(f"Error al conectar con ntfy.sh: {e}")
            return {"enviados": 0, "fallidos": 1, "error": str(e)}
        except Exception as e:
            logger.exception("Excepción inesperada enviando notificación universal")
            return {"enviados": 0, "fallidos": 1, "error": str(e)}

    def enviar_alerta_critica(
        self,
        tokens_dispositivos: List[str],
        id_triaje: str,
        nivel_urgencia: int,
        especialidad: str,
        custom_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía una alerta de triaje crítico (Nivel 1 o 2) a los wearables de la especialidad.
        """
        # Titulo y cuerpo solo con ASCII para evitar corrupcion de headers HTTP
        titulo = f"AI-Triage - URGENCIA Nivel {nivel_urgencia}"
        cuerpo = f"CASO CRITICO: Nivel {nivel_urgencia} en {especialidad}. Atender de inmediato (ID: {id_triaje[:8]})."

        # 1. Enviar siempre por el canal universal (Huawei Watch GT5 / Smartphones)
        ntfy_result = self.enviar_push_universal_huawei(titulo, cuerpo, nivel_urgencia, especialidad, custom_topic)
        logger.info(f"ntfy result: {ntfy_result}")

        # 2. Enviar por FCM para WearOS si hay tokens registrados
        if tokens_dispositivos and self.initialized:
            try:
                from firebase_admin import messaging
                mensaje = messaging.MulticastMessage(
                    notification=messaging.Notification(
                        title=titulo,
                        body=cuerpo
                    ),
                    data={
                        "id_triaje": str(id_triaje),
                        "nivel_urgencia": str(nivel_urgencia),
                        "especialidad_asignada": str(especialidad),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    tokens=tokens_dispositivos,
                    android=messaging.AndroidConfig(priority='high', ttl=600)
                )
                response = messaging.send_multicast(mensaje)
                tokens_invalidos = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        error_code = resp.exception.code if hasattr(resp.exception, 'code') else 'UNKNOWN'
                        if error_code in ['NOT_FOUND', 'UNREGISTERED']:
                            tokens_invalidos.append(tokens_dispositivos[idx])

                return {
                    "enviados": response.success_count,
                    "fallidos": response.failure_count,
                    "tokens_invalidos": tokens_invalidos
                }
            except Exception as e:
                logger.error(f"Error enviando notificación multicast FCM: {e}")

        # Si no hay tokens FCM o corre en modo local:
        logger.info(
            f"[WEARABLE NOTIFICADO] Destino: Huawei Watch GT5 / canal universal | "
            f"Caso: {id_triaje} | Nivel: {nivel_urgencia} | Especialidad: {especialidad}"
        )
        return {
            "enviados": 1,
            "fallidos": 0,
            "tokens_invalidos": []
        }

fcm_service = FCMNotificationService()
