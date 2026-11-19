import pytest

def test_analizar_triaje_nivel_1_critico(client, admin_token):
    payload = {
        "id_origen_clinica": "DOC-TEST-001",
        "texto_sintomas": "Paciente de 55 anos con dolor toracico opresivo irradiado a mandíbula, sudoracion fria, disnea súbita, inconsciencia, FC 140 lpm y antecedente de IAM previo."
    }
    res = client.post(
        "/api/v1/triaje/analizar",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["nivel_urgencia"] in [1, 2]
    assert data["puntaje_severidad"] >= 60.0
    assert data["especialidad_asignada"] == "Cardiologia"
    assert data["alerta_push_enviada"] is True
    assert "id_triaje" in data

def test_analizar_triaje_longitud_invalida_422(client, admin_token):
    # Texto menor a 30 caracteres
    res = client.post(
        "/api/v1/triaje/analizar",
        json={"id_origen_clinica": "DOC-SHORT", "texto_sintomas": "Dolor de cabeza leve"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 422

def test_analizar_triaje_duplicado_409(client, admin_token):
    payload = {
        "id_origen_clinica": "DOC-DUP-01",
        "texto_sintomas": "Paciente con dolor abdominal agudo persistente y vomito de 12 horas de evolucion sin diarrea."
    }
    # Primera vez -> 201
    res1 = client.post("/api/v1/triaje/analizar", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res1.status_code == 201

    # Segunda vez con mismo id_origen_clinica -> 409
    res2 = client.post("/api/v1/triaje/analizar", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 409

def test_analizar_triaje_rol_medico_prohibido_403(client, medico_token):
    # Médicos no tienen acceso a ingesta (solo administrativos)
    res = client.post(
        "/api/v1/triaje/analizar",
        json={"id_origen_clinica": "DOC-MED", "texto_sintomas": "Paciente con fiebre alta y tos productiva de 3 dias de evolucion."},
        headers={"Authorization": f"Bearer {medico_token}"}
    )
    assert res.status_code == 403
