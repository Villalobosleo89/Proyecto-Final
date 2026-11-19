from locust import HttpUser, task, between

class PersonalAdministrativoUser(HttpUser):
    wait_time = between(1, 3)
    token = ""

    def on_start(self):
        res = self.client.post("/api/v1/auth/login", json={"usuario": "recepcion1", "contrasena": "admin123"})
        if res.status_code == 200:
            self.token = res.json().get("access_token")

    @task(3)
    def analizar_historia_clinica(self):
        import random
        doc_id = f"LOCUST-{random.randint(100000, 999999)}"
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.post(
            "/api/v1/triaje/analizar",
            json={
                "id_origen_clinica": doc_id,
                "texto_sintomas": "Paciente acude con dolor toracico opresivo de inicio agudo, sudoracion y disnea moderada con FC 110 lpm."
            },
            headers=headers
        )

class MedicoEspecialistaUser(HttpUser):
    wait_time = between(1, 2)
    token = ""

    def on_start(self):
        res = self.client.post("/api/v1/auth/login", json={"usuario": "dr.lopez", "contrasena": "medico123"})
        if res.status_code == 200:
            self.token = res.json().get("access_token")

    @task(10)
    def consultar_cola_cardiologia(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.get("/api/v1/colas?especialidad=Cardiologia&limite=20", headers=headers)
