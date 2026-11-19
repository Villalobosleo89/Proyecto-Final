import re
import sys
from typing import List, Dict, Any
from pathlib import Path
import yaml

def get_config_path() -> Path:
    if hasattr(sys, '_MEIPASS'):
        p = Path(sys._MEIPASS) / "app" / "ml" / "rules_config.yaml"
        if p.exists():
            return p
    return Path(__file__).resolve().parent / "rules_config.yaml"

CONFIG_PATH = get_config_path()

class MedicalNERExtractor:
    """
    Extractor de Entidades Clínicas (Medical NER) para Triaje Hospitalario.
    Identifica:
    - sintoma: síntomas referidos y observados
    - signo_vital: constantes fisiológicas alteradas (FC, TA, SatO2, Temp)
    - antecedente: antecedentes patológicos de riesgo
    - diagnostico_cie10: codificación de sospecha diagnóstica (CIE-10)
    """

    def __init__(self):
        self.config = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

        # Diccionarios de detección clínica
        self.sintomas_catalogo = [
            ("compromiso de via aerea", "sintoma", 0.98),
            ("paro cardiorrespiratorio", "sintoma", 0.99),
            ("inconsciencia", "sintoma", 0.95),
            ("inconsciente", "sintoma", 0.95),
            ("convulsion actual", "sintoma", 0.95),
            ("convulsion", "sintoma", 0.90),
            ("anafilaxia", "sintoma", 0.95),
            ("dolor toracico opresivo", "sintoma", 0.95),
            ("dolor toracico", "sintoma", 0.90),
            ("dolor precordial", "sintoma", 0.90),
            ("dolor de pecho", "sintoma", 0.88),
            ("sudoracion fria", "sintoma", 0.85),
            ("dificultad para respirar", "sintoma", 0.90),
            ("disnea", "sintoma", 0.92),
            ("deficit neurologico agudo", "sintoma", 0.95),
            ("hemiparesia", "sintoma", 0.92),
            ("afasia", "sintoma", 0.90),
            ("sangrado masivo", "sintoma", 0.95),
            ("hemorragia activa", "sintoma", 0.92),
            ("cefalea brusca", "sintoma", 0.88),
            ("cefalea intensa", "sintoma", 0.85),
            ("dolor abdominal agudo", "sintoma", 0.90),
            ("dolor abdominal", "sintoma", 0.85),
            ("vomito persistente", "sintoma", 0.80),
            ("vomito", "sintoma", 0.75),
            ("trauma craneoencefalico", "sintoma", 0.92),
            ("trauma", "sintoma", 0.80),
            ("fractura", "sintoma", 0.85),
        ]

        self.signos_vitales_catalogo = [
            (r'fc\s*[:=]?\s*(\d{2,3})', "signo_vital", "FC"),
            (r'frecuencia\s+cardiaca\s*[:=]?\s*(\d{2,3})', "signo_vital", "FC"),
            (r'ta\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})', "signo_vital", "TA"),
            (r'tension\s+arterial\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})', "signo_vital", "TA"),
            (r'sat(?:uracion)?\s*(?:o2)?\s*[:=]?\s*(\d{2,3})\s*%', "signo_vital", "SatO2"),
            (r'temp(?:eratura)?\s*[:=]?\s*(\d{2}(?:\.\d)?)\s*°?c?', "signo_vital", "Temp"),
            (r'glasgow\s*[:=]?\s*(\d{1,2})', "signo_vital", "Glasgow"),
        ]

        self.antecedentes_catalogo = [
            ("iam", "antecedente", "Antecedente de IAM", 0.92),
            ("infarto agudo de miocardio", "antecedente", "Antecedente de IAM", 0.95),
            ("epoc", "antecedente", "EPOC descompensada", 0.90),
            ("diabetes", "antecedente", "Diabetes Mellitus", 0.88),
            ("hipertension", "antecedente", "Hipertension Arterial", 0.88),
            ("inmunosupresion", "antecedente", "Inmunosupresion", 0.92),
            ("embarazo", "antecedente", "Embarazo", 0.95),
            ("gestante", "antecedente", "Embarazo", 0.95),
        ]

        self.cie10_map = [
            ("i20", "I20.9 - Angina de pecho, no especificada"),
            ("i21", "I21.9 - Infarto agudo del miocardio"),
            ("j96", "J96.0 - Insuficiencia respiratoria aguda"),
            ("r57", "R57.9 - Choque, no especificado"),
            ("i63", "I63.9 - Infarto cerebral"),
            ("i64", "I64.X - Accidente vascular encefalico agudo"),
            ("r07", "R07.4 - Dolor en el pecho, no especificado"),
            ("r10", "R10.0 - Abdomen agudo"),
        ]

    def extraer_entidades(self, texto: str) -> List[Dict[str, Any]]:
        entidades: List[Dict[str, Any]] = []
        texto_lower = texto.lower()

        # 1. Extracción de Síntomas
        for termino, tipo, confianza in self.sintomas_catalogo:
            if termino in texto_lower:
                entidades.append({
                    "tipo": tipo,
                    "valor": termino,
                    "confianza": confianza
                })

        # 2. Extracción de Signos Vitales
        for regex_pat, tipo, nombre in self.signos_vitales_catalogo:
            matches = re.finditer(regex_pat, texto_lower)
            for m in matches:
                valor_detectado = m.group(0).strip()
                entidades.append({
                    "tipo": tipo,
                    "valor": f"{nombre}: {valor_detectado}",
                    "confianza": 0.95
                })

        # 3. Antecedentes
        for termino, tipo, canonico, confianza in self.antecedentes_catalogo:
            if re.search(r'\b' + re.escape(termino) + r'\b', texto_lower):
                entidades.append({
                    "tipo": tipo,
                    "valor": canonico,
                    "confianza": confianza
                })

        # 4. Diagnósticos CIE-10
        for clave, valor_cie in self.cie10_map:
            if re.search(r'\b' + re.escape(clave) + r'\b', texto_lower):
                entidades.append({
                    "tipo": "diagnostico_cie10",
                    "valor": valor_cie,
                    "confianza": 0.90
                })

        if "dolor toracico opresivo" in texto_lower and not any(e["tipo"] == "diagnostico_cie10" for e in entidades):
            entidades.append({
                "tipo": "diagnostico_cie10",
                "valor": "I20.9 - Angina de pecho / Dolor precordial",
                "confianza": 0.85
            })

        return entidades

ner_extractor = MedicalNERExtractor()
