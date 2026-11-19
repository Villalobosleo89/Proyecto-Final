import re
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Tuple
import yaml
from app.ml.normalizer import normalizar_texto
from app.ml.anonymizer import anonimizador
from app.ml.ner_extractor import ner_extractor

def get_config_path() -> Path:
    if hasattr(sys, '_MEIPASS'):
        p = Path(sys._MEIPASS) / "app" / "ml" / "rules_config.yaml"
        if p.exists():
            return p
    return Path(__file__).resolve().parent / "rules_config.yaml"

CONFIG_PATH = get_config_path()

# Mapa exacto a las especialidades del catalogo de la base de datos
MAP_ESPECIALIDADES = {
    "cardiologia": "Cardiologia",
    "cardiólogía": "Cardiologia",
    "neurologia": "Neurologia",
    "neurología": "Neurologia",
    "neumologia": "Neumologia",
    "neumología": "Neumologia",
    "cirugia general": "Cirugia general",
    "cirugía general": "Cirugia general",
    "cirugia": "Cirugia general",
    "cirugía": "Cirugia general",
    "medicina interna": "Medicina interna",
    "gastroenterologia": "Gastroenterologia",
    "gastroenterología": "Gastroenterologia",
    "pediatria": "Pediatria",
    "pediatría": "Pediatria",
    "medicina general": "Medicina general",
}

class MotorInferenciaTriaje:
    """
    Motor de Inferencia de Triaje Clinico (Resolucion 5596 de 2015).
    Pipeline de 5 etapas:
    1. Normalizacion
    2. Anonimizacion
    3. Medical NER
    4. Clasificacion con IA (Google Gemini con fallback a Reglas)
    5. Veredicto: Nivel de Triaje (1-5) + Especialidad Destino
    """

    def __init__(self):
        self.config = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

        # Cargar API key de Gemini desde variable de entorno
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        try:
            from app.config import settings
            key = getattr(settings, 'GEMINI_API_KEY', None)
            if key and len(key) > 10:
                self.gemini_api_key = key
        except Exception:
            pass

    # ================================================================
    #  CLASIFICACION CON IA (GEMINI)
    # ================================================================
    def clasificar_con_gemini(self, texto: str) -> Dict[str, Any]:
        """Clasifica cualquier caso clinico usando la API de Google Gemini."""
        if not self.gemini_api_key:
            return None

        prompt = (
            "Eres un medico especialista en triaje clinico de urgencias hospitalarias "
            "regido por la Resolucion 5596 de 2015 del Ministerio de Salud de Colombia.\n\n"
            "Tu tarea es analizar el siguiente caso clinico y emitir la clasificacion de triaje.\n\n"
            "Debes responder en formato JSON con los siguientes campos obligatorios:\n"
            "- nivel_urgencia: entero entre 1 y 5\n"
            "- puntaje_severidad: decimal entre 0.0 y 100.0\n"
            "- especialidad_asignada: una de ['Cardiologia', 'Neurologia', 'Neumologia', 'Cirugia general', 'Medicina interna', 'Gastroenterologia', 'Pediatria', 'Medicina general']\n"
            "- justificacion: breve explicacion clinica\n\n"
            "Escala de Triaje (Resolucion 5596/2015):\n"
            "* Nivel 1 (Resucitacion / Reanimacion inmediata, puntaje 80-100): Paciente con riesgo vital inminente. "
            "Ejemplos: Paro cardiorrespiratorio, sin pulso, apnea, inconsciencia profunda, shock grave, hemorragia exanguinante o masiva, herida por arma blanca/fuego con shock.\n"
            "* Nivel 2 (Emergencia / Muy urgente, puntaje 60-79.9): Alto riesgo o dolor extremo. "
            "Ejemplos: Dolor toracico anginoso/IAM, deficit neurologico agudo/ACV, disnea severa, heridas traumaticas profundas/apunalado con signos de alarma, fracturas expuestas.\n"
            "* Nivel 3 (Urgente, puntaje 35-59.9): Paciente clinicamente estable pero que puede deteriorarse sin atencion. "
            "Ejemplos: Dolor abdominal agudo, fiebre alta > 39, vomito persistente, deshidratacion moderada, fracturas cerradas.\n"
            "* Nivel 4 (Prioritario / Menos urgente, puntaje 15-34.9): Condiciones medicas menores, estables, sin riesgo vital. "
            "Ejemplos: Amigdalitis, gastroenteritis leve, cefalea leve/moderada, lumbalgia cronica.\n"
            "* Nivel 5 (No urgente, puntaje 0-14.9): Sin sintomas agudos o consultas administrativas. "
            "Ejemplos: Renovacion de formulas, retiro de puntos, certificados, chequeos generales.\n\n"
            f'Caso clinico a clasificar:\n"{texto}"'
        )

        modelos_disponibles = [
            "gemini-3.1-flash-lite",
            "gemini-3-flash-preview",
            "gemini-3.8-flash"
        ]

        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
                "maxOutputTokens": 1000
            }
        }).encode("utf-8")

        for modelo in modelos_disponibles:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{modelo}:generateContent?key={self.gemini_api_key}"
            )
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json"}
            )

            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                parsed = json.loads(text)

                nivel = int(parsed.get("nivel_urgencia", 5))
                if nivel < 1 or nivel > 5:
                    nivel = 5

                puntaje = float(parsed.get("puntaje_severidad", 5.0))
                puntaje = max(0.0, min(100.0, puntaje))

                # Mapear especialidad de forma robusta
                esp_raw = str(parsed.get("especialidad_asignada", "Medicina general")).strip().lower()
                especialidad = MAP_ESPECIALIDADES.get(esp_raw, "Medicina general")

                print(f"[AI-Triage] Google Gemini ({modelo}) clasifico con exito:")
                print(f"            Nivel: {nivel} | Puntaje: {puntaje} | Especialidad: {especialidad}")
                print(f"            Justificacion: {parsed.get('justificacion', '')}")

                return {
                    "nivel_urgencia": nivel,
                    "puntaje_severidad": round(puntaje, 2),
                    "especialidad_asignada": especialidad
                }
            except Exception as e:
                print(f"[AI-Triage] Info: Fallo modelo {modelo} ({e}), intentando siguiente...")

        print("[AI-Triage] Alerta: No se pudo conectar a Gemini, aplicando motor de reglas local.")
        return None

    # ================================================================
    #  MOTOR DE REGLAS (FALLBACK LOCAL)
    # ================================================================
    def calcular_severidad(self, texto_anon: str, entidades: List[Dict[str, Any]]) -> float:
        texto_lower = texto_anon.lower()
        score = float(self.config.get("base_score", 5.0))
        rules = self.config.get("rules", {})

        # 1. Compromiso vital extremo (+40, tope 40)
        p1 = rules.get("compromiso_vital_extremo", {})
        pts1 = 0.0
        for pat in p1.get("patterns", []):
            if pat in texto_lower:
                pts1 = p1.get("points", 40.0)
                break
        score += min(pts1, p1.get("cap", 40.0))

        # 2. Emergencia mayor (+30, tope 30)
        p2 = rules.get("emergencia_mayor", {})
        pts2 = 0.0
        for pat in p2.get("patterns", []):
            if pat in texto_lower:
                pts2 = p2.get("points", 30.0)
                break
        score += min(pts2, p2.get("cap", 30.0))

        # 3. Signos vitales inestables (+25, tope 25)
        p3 = rules.get("signos_vitales_inestables", {})
        pts3 = 0.0
        for pat in p3.get("patterns", []):
            if pat in texto_lower:
                pts3 = p3.get("points", 25.0)
                break

        if pts3 == 0.0:
            sat_match = re.search(r'sat(?:uracion)?\s*(?:o2)?\s*[:=]?\s*(\d{2,3})', texto_lower)
            if sat_match and int(sat_match.group(1)) < 90:
                pts3 = 25.0
            fc_match = re.search(r'f(?:c|recuencia\s+cardiaca)\s*[:=]?\s*(\d{2,3})', texto_lower)
            if fc_match and (int(fc_match.group(1)) > 130 or int(fc_match.group(1)) < 40):
                pts3 = 25.0
            ta_match = re.search(r't(?:a|ension)(?:\s+sistolica)?\s*[:=]?\s*(\d{2,3})', texto_lower)
            if ta_match and int(ta_match.group(1)) < 80:
                pts3 = 25.0

        score += min(pts3, p3.get("cap", 25.0))

        # 4. Antecedentes de riesgo (+15, tope 15)
        p4 = rules.get("antecedentes_riesgo", {})
        pts4 = 0.0
        for pat in p4.get("patterns", []):
            if pat in texto_lower:
                pts4 = p4.get("points", 15.0)
                break
        score += min(pts4, p4.get("cap", 15.0))

        # 5. Diagnostico CIE-10 urgente (+10, tope 10)
        p5 = rules.get("diagnostico_urgente_cie10", {})
        pts5 = 0.0
        for pat in p5.get("patterns", []):
            if pat in texto_lower:
                pts5 = p5.get("points", 10.0)
                break
        score += min(pts5, p5.get("cap", 10.0))

        # 6. Sintomas moderados (+8, tope 16)
        p6 = rules.get("sintomas_moderados", {})
        pts6 = 0.0
        for pat in p6.get("patterns", []):
            if pat in texto_lower:
                pts6 += p6.get("points", 8.0)
        temp_match = re.search(r'temp(?:eratura)?\s*[:=]?\s*(\d{2}(?:\.\d)?)', texto_lower)
        if temp_match and float(temp_match.group(1)) > 38.5:
            pts6 += 8.0
        if "fiebre" in texto_lower:
            pts6 += 8.0
        score += min(pts6, p6.get("cap", 16.0))

        return round(min(max(score, 0.0), 100.0), 2)

    def determinar_nivel_triaje(self, puntaje: float) -> Tuple[int, bool]:
        if puntaje >= 80.0:
            return 1, True
        elif puntaje >= 60.0:
            return 2, True
        elif puntaje >= 35.0:
            return 3, False
        elif puntaje >= 15.0:
            return 4, False
        else:
            return 5, False

    def derivar_especialidad(self, texto_anon: str, entidades: List[Dict[str, Any]]) -> str:
        texto_lower = texto_anon.lower()

        if any(w in texto_lower for w in ["dolor toracico", "toracico", "precordial", "pecho opresivo", "iam", "infarto", "cardiaco"]):
            return "Cardiologia"
        if any(w in texto_lower for w in ["deficit neurologico", "hemiparesia", "convulsion", "cefalea brusca", "afasia", "neurologico", "acv"]):
            return "Neurologia"
        if any(w in texto_lower for w in ["via aerea", "disnea", "desaturacion", "respirar", "respiratoria", "estridor", "sato2"]):
            return "Neumologia"
        if any(w in texto_lower for w in ["trauma", "sangrado masivo", "hemorragia", "fractura", "herida por arma", "apunalado", "punalada", "acuchillado", "herida"]):
            return "Cirugia general"
        if any(w in texto_lower for w in ["sepsis", "foco infeccioso", "fiebre", "infeccion bacteriana"]):
            return "Medicina interna"
        if any(w in texto_lower for w in ["dolor abdominal", "abdomen agudo", "epigastralgia", "vomito persistente"]):
            return "Gastroenterologia"

        edad_match = re.search(r'(\d{1,2})\s*(?:anos|meses)', texto_lower)
        if edad_match:
            valor_edad = int(edad_match.group(1))
            if "meses" in edad_match.group(0) or valor_edad < 18:
                return "Pediatria"
        if any(w in texto_lower for w in ["lactante", "pediatrico", "recien nacido", "infante"]):
            return "Pediatria"

        return "Medicina general"

    # ================================================================
    #  PIPELINE PRINCIPAL
    # ================================================================
    def procesar(self, texto_crudo: str, usar_ia: bool = True) -> Dict[str, Any]:
        texto_norm = normalizar_texto(texto_crudo)
        texto_anon = anonimizador.anonimizar(texto_norm)
        entidades = ner_extractor.extraer_entidades(texto_anon)

        # 1. Intentar clasificacion con IA avanzada (Google Gemini) si está habilitado
        gemini_result = self.clasificar_con_gemini(texto_anon) if usar_ia else None

        if gemini_result:
            nivel = gemini_result["nivel_urgencia"]
            puntaje = gemini_result["puntaje_severidad"]
            especialidad = gemini_result["especialidad_asignada"]
            requiere_push = nivel in [1, 2]
        else:
            # 2. Fallback de alta disponibilidad: Motor de Reglas clinicas
            puntaje = self.calcular_severidad(texto_anon, entidades)
            nivel, requiere_push = self.determinar_nivel_triaje(puntaje)
            especialidad = self.derivar_especialidad(texto_anon, entidades)

        return {
            "texto_anonimizado": texto_anon,
            "entidades": entidades,
            "puntaje_severidad": puntaje,
            "nivel_urgencia": nivel,
            "especialidad_asignada": especialidad,
            "alerta_push_requerida": requiere_push
        }

triage_engine = MotorInferenciaTriaje()
