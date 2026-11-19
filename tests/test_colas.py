import pytest

def test_consultar_cola_medico_orden(client, admin_token, medico_token):
    # 1. Ingresar caso nivel urgente (moderado)
    client.post(
        "/api/v1/triaje/analizar",
        json={
            "id_origen_clinica": "DOC-C-01",
            "texto_sintomas": "Paciente acude por palpitaciones leves y mareo ocasional de 2 semanas de evolucion."
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # 2. Ingresar caso crítico (Nivel 1 o 2)
    client.post(
        "/api/v1/triaje/analizar",
        json={
            "id_origen_clinica": "DOC-C-02",
            "texto_sintomas": "Paciente con paro cardiorrespiratorio o dolor toracico opresivo masivo, inconsciente, sudoroso y desaturando."
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # 3. Consultar cola como médico
    res = client.get("/api/v1/colas?especialidad=Cardiologia&limite=10", headers={"Authorization": f"Bearer {medico_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["especialidad"] == "Cardiologia"
    assert len(data["pacientes"]) >= 1
    
    # El primer paciente en la cola debe ser el más crítico (menor nivel de triaje: 1 o 2)
    primero = data["pacientes"][0]
    assert primero["nivel_urgencia"] in [1, 2]

def test_consultar_cola_rol_admin_prohibido_403(client, admin_token):
    res = client.get("/api/v1/colas?especialidad=Cardiologia", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 403

def test_consultar_cola_especialidad_inexistente_404(client, medico_token):
    res = client.get("/api/v1/colas?especialidad=EspecialidadFantasma", headers={"Authorization": f"Bearer {medico_token}"})
    assert res.status_code == 404
