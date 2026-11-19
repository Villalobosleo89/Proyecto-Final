import pytest

def test_login_exitoso(client):
    res = client.post("/api/v1/auth/login", json={"usuario": "admin_test", "contrasena": "pass123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900

def test_login_credenciales_invalidas(client):
    res = client.post("/api/v1/auth/login", json={"usuario": "admin_test", "contrasena": "clave_errada"})
    assert res.status_code == 401
    assert "inválidas" in res.json()["detail"].lower()

def test_refresh_token_ciclo(client):
    login_res = client.post("/api/v1/auth/login", json={"usuario": "admin_test", "contrasena": "pass123"})
    refresh_token = login_res.json()["refresh_token"]

    # Usar refresh token
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()
    assert "refresh_token" in refresh_res.json()

    # Reintentar con el mismo refresh token revocado -> debe fallar 401 (RF-15)
    segundo_intento = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert segundo_intento.status_code == 401
