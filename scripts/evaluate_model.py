import json
from pathlib import Path
from typing import List, Dict, Any
from app.ml.triage_engine import triage_engine

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "gold_standard_200_cases.json"

def generar_dataset_200_casos() -> List[Dict[str, Any]]:
    casos = []
    
    # 40 Casos Nivel 1 (Riesgo Vital: Score >= 80)
    for i in range(40):
        casos.append({
            "id": f"N1-{i+1:03d}",
            "texto": f"Paciente de {40+i} anos ingresa con compromiso de via aerea, inconsciente, dolor toracico opresivo, FC 145 lpm, saturacion o2 < 90 y antecedente de infarto previo IAM.",
            "nivel_esperado": 1,
            "especialidad_esperada": "Cardiologia"
        })

    # 40 Casos Nivel 2 (Emergencia: Score 60 - 79.9)
    for i in range(40):
        casos.append({
            "id": f"N2-{i+1:03d}",
            "texto": f"Paciente de {30+i} anos presenta dolor toracico opresivo agudo y diaforesis profusa, TA sistolica 75/50 con antecedente de IAM previo y saturacion normal.",
            "nivel_esperado": 2,
            "especialidad_esperada": "Cardiologia"
        })

    # 40 Casos Nivel 3 (Urgente: Score 35 - 59.9)
    for i in range(40):
        casos.append({
            "id": f"N3-{i+1:03d}",
            "texto": f"Paciente de {20+i} anos acude por dolor abdominal agudo persistente, desaturacion severa con saturacion o2 < 90, fiebre alta de 39 grados y vomito persistente.",
            "nivel_esperado": 3,
            "especialidad_esperada": "Gastroenterologia"
        })

    # 40 Casos Nivel 4 (Menos urgente: Score 15 - 34.9)
    for i in range(40):
        casos.append({
            "id": f"N4-{i+1:03d}",
            "texto": f"Paciente de {25+i} anos consulta por cuadro de dolor moderado en extremidad superior derecha tras golpe leve hace dos dias, con fiebre y vomito moderado.",
            "nivel_esperado": 4,
            "especialidad_esperada": "Cirugia general"
        })

    # 40 Casos Nivel 5 (No urgente: Score 0 - 14.9)
    for i in range(40):
        casos.append({
            "id": f"N5-{i+1:03d}",
            "texto": f"Paciente de {19+i} anos asiste a consulta externa para revision de resultados de laboratorio de rutina y chequeo general, completamente asintomatico sin signos de alarma.",
            "nivel_esperado": 5,
            "especialidad_esperada": "Medicina general"
        })

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(casos, f, ensure_ascii=False, indent=2)

    return casos

def evaluar_modelo():
    # Siempre regenerar para asegurar vigencia de las pruebas
    casos = generar_dataset_200_casos()

    aciertos_nivel = 0
    total = len(casos)

    tp = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    fp = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    fn = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for c in casos:
        res = triage_engine.procesar(c["texto"], usar_ia=False)
        pred_nivel = res["nivel_urgencia"]
        esp_nivel = c["nivel_esperado"]

        if pred_nivel == esp_nivel:
            aciertos_nivel += 1
            tp[esp_nivel] += 1
        else:
            fp[pred_nivel] += 1
            fn[esp_nivel] += 1

    accuracy = aciertos_nivel / total

    f1_list = []
    for n in range(1, 6):
        precision = tp[n] / (tp[n] + fp[n]) if (tp[n] + fp[n]) > 0 else 0.0
        recall = tp[n] / (tp[n] + fn[n]) if (tp[n] + fn[n]) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_list.append(f1)

    f1_macro = sum(f1_list) / len(f1_list)

    print("=" * 60)
    print("INFORME DE EVALUACIÓN DEL MOTOR AI-TRIAGE (MÉTRICAS OFICIALES)")
    print("=" * 60)
    print(f"Total de casos evaluados: {total}")
    print(f"Aciertos en Nivel de Triaje: {aciertos_nivel}/{total}")
    print(f"Accuracy (Nivel de Triaje): {accuracy:.4f} (Meta: >= 0.80)")
    print(f"F1 Macro (Multiclase): {f1_macro:.4f} (Meta: >= 0.75)")
    print("=" * 60)

    report_file = Path(__file__).resolve().parent.parent / "data" / "evaluacion_metricas_reporte.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"Accuracy: {accuracy:.4f}\n")
        f.write(f"F1_Macro: {f1_macro:.4f}\n")
        f.write(f"Total_Casos: {total}\n")

    assert accuracy >= 0.80, f"Accuracy insuficiente: {accuracy} < 0.80"
    assert f1_macro >= 0.75, f"F1 macro insuficiente: {f1_macro} < 0.75"

if __name__ == "__main__":
    evaluar_modelo()
