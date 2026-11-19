import pytest

def test_matriz_rbac_completa(client, admin_token, medico_token):
    # 1. POST /triaje/analizar
    # Public -> 401
    res_pub = client.post("/api/v1/triaje/analizar", json={"id_origen_clinica": "T1", "texto_sintomas": "test test test test test test test"})
    assert res_pub.status_code == 401

    # Medico -> 403
    res_med = client.post("/api/v1/triaje/analizar", json={"id_origen_clinica": "T1", "texto_sintomas": "test test test test test test test"}, headers={"Authorization": f"Bearer {medico_token}"})
    assert res_med.status_code == 403

    # Admin -> pasa autorización (201 o 422 si formato)
    res_adm = client.post("/api/v1/triaje/analizar", json={"id_origen_clinica": "T-ADM-01", "texto_sintomas": "Paciente acude con dolor toracico de 30 minutos de evolucion."}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res_adm.status_code == 201

    # 2. GET /colas
    # Public -> 401
    assert client.get("/api/v1/colas?especialidad=Cardiologia").status_code == 401
    # Admin -> 403
    assert client.get("/api/v1/colas?especialidad=Cardiologia", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 403
    # Medico -> 200
    assert client.get("/api/v1/colas?especialidad=Cardiologia", headers={"Authorization": f"Bearer {medico_token}"}).status_code == 200

    # 3. POST /dispositivos/registrar
    payload_disp = {"sistema_operativo": "WearOS", "fcm_token": "token_prueba_123"}
    # Public -> 401
    assert client.post("/api/v1/dispositivos/registrar", json=payload_disp).status_code == 401
    # Admin -> 403
    assert client.post("/api/v1/dispositivos/registrar", json=payload_disp, headers={"Authorization": f"Bearer {admin_token}"}).status_code == 403
    # Medico -> 200
    assert client.post("/api/v1/dispositivos/registrar", json=payload_disp, headers={"Authorization": f"Bearer {medico_token}"}).status_code == 200

    # 4. GET /healthz -> Public 200
    assert client.get("/healthz").status_code == 200
