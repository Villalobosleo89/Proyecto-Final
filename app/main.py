import uuid
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.core.logging import setup_logging, correlation_id_ctx
from app.api.v1 import auth, triaje, colas, dispositivos, health
from app.models.models import Especialidad, Medico, DispositivoWearable, Usuario
from app.core.security import get_password_hash

# Configurar logging estructurado
setup_logging()

# Crear tablas en BD al iniciar
Base.metadata.create_all(bind=engine)

def seed_initial_data():
    """Poblar catálogos y usuarios iniciales si la BD está vacía"""
    db = SessionLocal()
    try:
        if db.query(Especialidad).count() == 0:
            especialidades = [
                "Cardiologia",
                "Neurologia",
                "Neumologia",
                "Cirugia general",
                "Medicina interna",
                "Gastroenterologia",
                "Pediatria",
                "Medicina general"
            ]
            for esp in especialidades:
                db.add(Especialidad(nombre=esp, activa=True))
            db.commit()

        cardio = db.query(Especialidad).filter(Especialidad.nombre == "Cardiologia").first()
        neuro = db.query(Especialidad).filter(Especialidad.nombre == "Neurologia").first()

        if db.query(Medico).count() == 0:
            med_cardio = Medico(
                nombre_completo="Dr. Leonardo Villalobos",
                correo="leonardo.villalobos@umb.edu.co",
                id_especialidad=cardio.id_especialidad if cardio else 1,
                activo=True
            )
            med_neuro = Medico(
                nombre_completo="Dr. Juan José López Reina",
                correo="juan.lopez@umb.edu.co",
                id_especialidad=neuro.id_especialidad if neuro else 2,
                activo=True
            )
            db.add_all([med_cardio, med_neuro])
            db.commit()

            db.add(DispositivoWearable(
                id_medico=med_cardio.id_medico,
                sistema_operativo="WearOS",
                fcm_token="token_simulado_wearos_dr_villalobos"
            ))
            db.commit()

        if db.query(Usuario).count() == 0:
            medico1 = db.query(Medico).first()
            admin_user = Usuario(
                nombre_usuario="recepcion1",
                contrasena_hash=get_password_hash("admin123"),
                rol="admin",
                activo=True
            )
            medico_user = Usuario(
                nombre_usuario="dr.lopez",
                contrasena_hash=get_password_hash("medico123"),
                rol="medico",
                id_medico=medico1.id_medico if medico1 else None,
                activo=True
            )
            db.add_all([admin_user, medico_user])
            db.commit()
    finally:
        db.close()

seed_initial_data()

app = FastAPI(
    title="AI-Triage API",
    description="Sistema Inteligente de Clasificación de Historias Clínicas para IPS (v4.0)",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Middleware de Correlation-ID y Trazabilidad (RN-12)
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        corr_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
        token = correlation_id_ctx.set(corr_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-Id"] = corr_id
            return response
        finally:
            correlation_id_ctx.reset(token)

app.add_middleware(CorrelationIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(triaje.router, prefix=settings.API_V1_PREFIX)
app.include_router(colas.router, prefix=settings.API_V1_PREFIX)
app.include_router(dispositivos.router, prefix=settings.API_V1_PREFIX)
app.include_router(health.router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index():
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Triage - Panel Clínico Inteligente</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <style>
        body {{ background-color: #f4f6f9; font-family: system-ui, -apple-system, sans-serif; }}
        .header-umb {{ background: linear-gradient(135deg, #8B0000 0%, #B22222 100%); color: white; padding: 18px 0; }}
        .triage-badge-1 {{ background-color: #dc3545; color: white; font-weight: bold; }}
        .triage-badge-2 {{ background-color: #fd7e14; color: white; font-weight: bold; }}
        .triage-badge-3 {{ background-color: #ffc107; color: black; font-weight: bold; }}
        .triage-badge-4 {{ background-color: #28a745; color: white; font-weight: bold; }}
        .triage-badge-5 {{ background-color: #0d6efd; color: white; font-weight: bold; }}
        .watch-simulation {{
            width: 250px; height: 250px; border-radius: 50%; background: #1a1a1a;
            border: 10px solid #333; margin: 0 auto; display: flex; flex-direction: column;
            justify-content: center; align-items: center; color: white; text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); padding: 20px; transition: all 0.3s;
        }}
        .watch-vibrating {{ animation: vibrate 0.3s infinite; border-color: #dc3545; }}
        @keyframes vibrate {{ 0% {{ transform: translate(0); }} 25% {{ transform: translate(-3px, 3px); }} 50% {{ transform: translate(3px, -3px); }} 75% {{ transform: translate(-3px, -3px); }} 100% {{ transform: translate(0); }} }}
    </style>
</head>
<body>
    <div class="header-umb mb-4 shadow">
        <div class="container d-flex justify-content-between align-items-center">
            <div>
                <h2 class="mb-0 fw-bold"><i class="bi bi-heart-pulse-fill me-2"></i>AI-Triage (v4.0)</h2>
                <small>Universidad Manuela Beltrán — Facultad de Ingeniería | Clasificación Inteligente de Historias Clínicas</small>
            </div>
            <div>
                <a href="/docs" class="btn btn-outline-light btn-sm fw-bold"><i class="bi bi-journal-code me-1"></i>Swagger OpenAPI 3.1</a>
                <a href="/healthz" class="btn btn-light btn-sm fw-bold text-danger ms-2"><i class="bi bi-shield-check me-1"></i>Healthcheck</a>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Banner Huawei Watch GT5 -->
        <div class="alert alert-info border-0 shadow-sm d-flex justify-content-between align-items-center py-2 px-3 mb-4 rounded-3">
            <div class="d-flex align-items-center">
                <i class="bi bi-smartwatch fs-2 text-primary me-3"></i>
                <div>
                    <strong class="text-dark">Conexión con Huawei Watch GT5 / Cualquier Reloj Inteligente</strong>
                    <div class="small text-muted">Abre en tu celular: <a href="https://ntfy.sh/{settings.NTFY_TOPIC}" target="_blank" class="fw-bold text-primary">https://ntfy.sh/{settings.NTFY_TOPIC}</a> y pulsa <i>Permitir notificaciones</i>. ¡Tu reloj vibrará con cada alerta crítica!</div>
                </div>
            </div>
            <button class="btn btn-primary btn-sm fw-bold" onclick="probarVibracionHuawei()"><i class="bi bi-bell-fill me-1"></i>Probar Vibración en mi Reloj</button>
        </div>

        <div class="row g-4">
            <!-- Columna Izquierda: Ingesta de Historias Clínicas (Rol Administrativo) -->
            <div class="col-lg-7">
                <div class="card shadow-sm border-0 mb-4">
                    <div class="card-header bg-dark text-white fw-bold d-flex justify-content-between">
                        <span><i class="bi bi-file-earmark-medical me-2"></i>Ingesta de Historia Clínica (Rol Administrativo)</span>
                        <span class="badge bg-secondary">POST /api/v1/triaje/analizar</span>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label fw-bold">ID Origen Clínica (HIS):</label>
                            <input type="text" id="idOrigen" class="form-control" value="DOC-9982">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Texto Clínico no estructurado (mínimo 30 caracteres):</label>
                            <textarea id="textoSintomas" class="form-control" rows="4" placeholder="Escriba o pegue la historia clínica...">Paciente masculino de 45 años con CC 1020304050 y tel 3112223344 atendido por Dr. Lopez. Ingresa con dolor toracico opresivo de 1 hora de evolucion, sudoracion fria, disnea, FC 140 lpm, TA 75/50 y antecedente de IAM hace 2 años.</textarea>
                            <small class="text-muted">Ley 1581 de 2012: Nombres, cédulas y teléfonos se anonimizan automáticamente antes del análisis.</small>
                        </div>
                        <div class="d-flex flex-wrap gap-2">
                            <button class="btn btn-danger fw-bold flex-grow-1" onclick="analizarTexto()"><i class="bi bi-cpu me-2"></i>Procesar con Motor de Inferencia IA</button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="cargarEjemplo(1)">Ejemplo Nivel 1</button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="cargarEjemplo(2)">Ejemplo Nivel 2</button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="cargarEjemplo(3)">Ejemplo Nivel 3</button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="cargarEjemplo(5)">Ejemplo Nivel 5</button>
                        </div>

                        <!-- Resultado del Análisis -->
                        <div id="resultadoAnalisis" class="mt-4 p-3 bg-light rounded border" style="display:none;">
                            <h5 class="fw-bold mb-3 text-dark"><i class="bi bi-clipboard2-check me-2"></i>Resultado de Inferencia:</h5>
                            <div class="row text-center mb-3 g-2">
                                <div class="col-4">
                                    <div class="p-2 bg-white rounded border">
                                        <div class="text-muted small">Nivel de Triaje</div>
                                        <span id="resNivel" class="badge p-2 fs-6">Nivel 1</span>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="p-2 bg-white rounded border">
                                        <div class="text-muted small">Severidad</div>
                                        <span id="resPuntaje" class="fw-bold fs-5 text-danger">85.0 / 100</span>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="p-2 bg-white rounded border">
                                        <div class="text-muted small">Especialidad</div>
                                        <span id="resEspecialidad" class="fw-bold fs-6 text-primary">Cardiología</span>
                                    </div>
                                </div>
                            </div>
                            <div class="small text-muted mb-1">UUID de Triaje: <span id="resIdTriaje" class="fw-bold text-dark font-monospace"></span></div>
                            <div class="small text-muted">Alerta Smartwatch: <span id="resAlerta" class="badge bg-success">Enviada vía Push</span></div>
                        </div>
                    </div>
                </div>

                <!-- Cola de Atención en Tiempo Real -->
                <div class="card shadow-sm border-0">
                    <div class="card-header bg-primary text-white fw-bold d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-list-ol me-2"></i>Cola Dinámica Hospitalaria (Consulta Médicos)</span>
                        <div class="d-flex align-items-center gap-2">
                            <select id="selectEspecialidad" class="form-select form-select-sm" onchange="actualizarCola()">
                                <option value="Cardiologia" selected>Cardiología</option>
                                <option value="Neurologia">Neurología</option>
                                <option value="Neumologia">Neumología</option>
                                <option value="Cirugia general">Cirugía general</option>
                                <option value="Medicina interna">Medicina interna</option>
                                <option value="Gastroenterologia">Gastroenterología</option>
                                <option value="Pediatria">Pediatría</option>
                                <option value="Medicina general">Medicina general</option>
                            </select>
                            <button class="btn btn-sm btn-light" onclick="actualizarCola()"><i class="bi bi-arrow-clockwise"></i></button>
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-hover mb-0 align-middle">
                            <thead class="table-light">
                                <tr>
                                    <th>Prioridad</th>
                                    <th>Nivel Triaje</th>
                                    <th>ID Triaje</th>
                                    <th>Tiempo en Espera</th>
                                </tr>
                            </thead>
                            <tbody id="tablaCola">
                                <tr><td colspan="4" class="text-center py-4 text-muted">Cargando cola...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Columna Derecha: Simulación WearOS y Detalles de Arquitectura -->
            <div class="col-lg-5">
                <div class="card shadow-sm border-0 mb-4 text-center">
                    <div class="card-header bg-dark text-white fw-bold">
                        <i class="bi bi-smartwatch me-2"></i>Simulador de Wearable (Médico en Guardia)
                    </div>
                    <div class="card-body py-4">
                        <div id="relojWearOS" class="watch-simulation">
                            <i class="bi bi-clock-history fs-3 mb-1 text-secondary"></i>
                            <div class="small text-uppercase text-secondary" style="letter-spacing: 1px;">Smartwatch</div>
                            <div id="relojContenido" class="mt-2">
                                <span class="badge bg-success mb-2">Monitor Listo</span>
                                <div class="text-muted small">Sin emergencias activas en turno</div>
                            </div>
                        </div>
                        <div class="mt-3">
                            <small class="text-muted">Si la IA clasifica en <strong>Nivel 1 o 2</strong>, el reloj vibra y notifica inmediatamente.</small>
                        </div>
                    </div>
                </div>

                <!-- Configuración de Canal Huawei -->
                <div class="card shadow-sm border-0 mb-4">
                    <div class="card-header bg-secondary text-white fw-bold">
                        <i class="bi bi-broadcast me-2"></i>Canal de Notificaciones Huawei Watch GT5
                    </div>
                    <div class="card-body small">
                        <p class="mb-2">Los relojes Huawei Watch GT5 reciben notificaciones vía Bluetooth desde la app <strong>Salud de Huawei</strong> de tu teléfono.</p>
                        <ol class="ps-3 mb-3">
                            <li>En tu celular, abre en Chrome: <br><a href="https://ntfy.sh/{settings.NTFY_TOPIC}" target="_blank" class="fw-bold">https://ntfy.sh/{settings.NTFY_TOPIC}</a></li>
                            <li>Toca en <strong>"Suscribirse"</strong> o <strong>"Permitir Notificaciones"</strong>.</li>
                            <li>En la app <i>Salud de Huawei</i> de tu celular, asegúrate de tener las notificaciones activas para Chrome o para la app ntfy.</li>
                        </ol>
                        <button class="btn btn-outline-primary btn-sm w-100 fw-bold" onclick="probarVibracionHuawei()"><i class="bi bi-bell-fill me-1"></i>Enviar Alerta de Prueba al Reloj</button>
                    </div>
                </div>

                <!-- Resumen Técnico -->
                <div class="card shadow-sm border-0">
                    <div class="card-header bg-secondary text-white fw-bold">
                        <i class="bi bi-info-circle me-2"></i>Especificación Técnica Cumplida
                    </div>
                    <div class="card-body small">
                        <ul class="list-unstyled mb-0">
                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i><strong>Resolución 5596/2015:</strong> 5 Niveles de Triaje normativos.</li>
                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i><strong>Ley 1581/2012:</strong> Anonimización de datos sensibles antes de IA.</li>
                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i><strong>ISO/IEC 11179:</strong> Diccionario de datos y modelo 3FN.</li>
                            <li class="mb-2"><i class="bi bi-check-circle-fill text-success me-2"></i><strong>Seguridad:</strong> JWT RS256, tokens de 15 min y control RBAC.</li>
                            <li class="mb-0"><i class="bi bi-check-circle-fill text-success me-2"></i><strong>Notificaciones:</strong> FCM HTTP v1 + Canal Push Universal.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let adminToken = "";
        let medicoToken = "";

        async function autenticar() {{
            try {{
                let r1 = await fetch("/api/v1/auth/login", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{usuario: "recepcion1", contrasena: "admin123"}})
                }});
                if (r1.ok) {{
                    let d1 = await r1.json();
                    adminToken = d1.access_token;
                }}

                let r2 = await fetch("/api/v1/auth/login", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{usuario: "dr.lopez", contrasena: "medico123"}})
                }});
                if (r2.ok) {{
                    let d2 = await r2.json();
                    medicoToken = d2.access_token;
                }}

                actualizarCola();
            }} catch (e) {{
                console.error("Error autenticando:", e);
            }}
        }}

        async function analizarTexto() {{
            if (!adminToken) await autenticar();
            const idOrigen = document.getElementById("idOrigen").value.trim();
            const texto = document.getElementById("textoSintomas").value.trim();

            if (texto.length < 30) {{
                alert("Atención: El texto clínico debe tener al menos 30 caracteres (Requerimiento RF-02). Actualmente tiene " + texto.length + " caracteres.");
                return;
            }}

            try {{
                let res = await fetch("/api/v1/triaje/analizar", {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${{adminToken}}`
                    }},
                    body: JSON.stringify({{
                        id_origen_clinica: idOrigen,
                        texto_sintomas: texto
                    }})
                }});

                if (res.status === 401) {{
                    console.log("Token expirado o no autenticado. Renovando sesion...");
                    adminToken = "";
                    await autenticar();
                    // Reintentar con el nuevo token
                    res = await fetch("/api/v1/triaje/analizar", {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${{adminToken}}`
                        }},
                        body: JSON.stringify({{
                            id_origen_clinica: idOrigen,
                            texto_sintomas: texto
                        }})
                    }});
                }}

                if (res.status === 409) {{
                    alert("Aviso: El caso " + idOrigen + " ya fue ingresado. Se generará un nuevo ID.");
                    document.getElementById("idOrigen").value = "DOC-" + Math.floor(Math.random() * 9000 + 1000);
                    return analizarTexto();
                }}

                if (!res.ok) {{
                    let err = await res.json();
                    alert("Error en validación: " + (err.detail ? JSON.stringify(err.detail) : JSON.stringify(err)));
                    return;
                }}

                let data = await res.json();
                mostrarResultado(data);
                document.getElementById("idOrigen").value = "DOC-" + Math.floor(Math.random() * 9000 + 1000);
                actualizarCola();
            }} catch (e) {{
                alert("Error comunicando con la API: " + e + ". Asegúrate de que la app esté iniciada.");
            }}
        }}

        function mostrarResultado(data) {{
            document.getElementById("resultadoAnalisis").style.display = "block";
            document.getElementById("resIdTriaje").innerText = data.id_triaje;
            document.getElementById("resEspecialidad").innerText = data.especialidad_asignada;
            document.getElementById("resPuntaje").innerText = data.puntaje_severidad.toFixed(1) + " / 100";
            
            const badgeNivel = document.getElementById("resNivel");
            badgeNivel.className = `badge p-2 fs-6 triage-badge-${{data.nivel_urgencia}}`;
            badgeNivel.innerText = `Nivel ${{data.nivel_urgencia}}`;

            const badgeAlerta = document.getElementById("resAlerta");
            if (data.alerta_push_enviada) {{
                badgeAlerta.className = "badge bg-danger";
                badgeAlerta.innerText = "¡ALERTA PUSH ENVIADA AL RELOJ!";
                dispararReloj(data);
            }} else {{
                badgeAlerta.className = "badge bg-secondary";
                badgeAlerta.innerText = "Sin alerta al reloj (No crítico)";
            }}
        }}

        function dispararReloj(data) {{
            const reloj = document.getElementById("relojWearOS");
            const cont = document.getElementById("relojContenido");
            reloj.classList.add("watch-vibrating");

            cont.innerHTML = `
                <div class="text-danger fw-bold small"><i class="bi bi-exclamation-triangle-fill"></i> ¡CASO CRÍTICO!</div>
                <div class="fs-4 fw-bold mt-1 text-white">Nivel ${{data.nivel_urgencia}}</div>
                <div class="text-warning small">${{data.especialidad_asignada}}</div>
                <div class="small text-white-50 mt-1 font-monospace" style="font-size: 10px;">${{data.id_triaje.substring(0,8)}}...</div>
            `;

            setTimeout(() => {{
                reloj.classList.remove("watch-vibrating");
            }}, 4000);
        }}

        async function probarVibracionHuawei() {{
            try {{
                let res = await fetch("/api/v1/dispositivos/probar-alerta", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{
                        canal: "{settings.NTFY_TOPIC}",
                        nivel_urgencia: 1,
                        especialidad: "Cardiologia"
                    }})
                }});
                let d = await res.json();
                alert("¡Alerta de prueba enviada! Revisa tu celular / Huawei Watch GT5.");
            }} catch (e) {{
                alert("Error enviando alerta de prueba: " + e);
            }}
        }}

        async function actualizarCola() {{
            if (!medicoToken) await autenticar();
            const esp = document.getElementById("selectEspecialidad").value;
            try {{
                let res = await fetch(`/api/v1/colas?especialidad=${{esp}}&limite=20`, {{
                    headers: {{"Authorization": `Bearer ${{medicoToken}}`}}
                }});
                if (res.status === 401) {{
                    medicoToken = "";
                    await autenticar();
                    res = await fetch(`/api/v1/colas?especialidad=${{esp}}&limite=20`, {{
                        headers: {{"Authorization": `Bearer ${{medicoToken}}`}}
                    }});
                }}
                if (!res.ok) return;
                let data = await res.json();
                let tbody = document.getElementById("tablaCola");
                tbody.innerHTML = "";

                if (data.pacientes.length === 0) {{
                    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">No hay pacientes en espera para ${{esp}}</td></tr>`;
                    return;
                }}

                data.pacientes.forEach((p, idx) => {{
                    let tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td class="fw-bold">#${{idx + 1}}</td>
                        <td><span class="badge triage-badge-${{p.nivel_urgencia}}">Nivel ${{p.nivel_urgencia}}</span></td>
                        <td class="font-monospace small">${{p.id_triaje}}</td>
                        <td><i class="bi bi-clock me-1"></i>${{p.tiempo_espera_minutos}} min</td>
                    `;
                    tbody.appendChild(tr);
                }});
            }} catch (e) {{
                console.error("Error al actualizar cola:", e);
            }}
        }}

        function cargarEjemplo(nivel) {{
            const txt = document.getElementById("textoSintomas");
            if (nivel === 1) {{
                txt.value = "Paciente masculino de 50 años ingresa con compromiso de via aerea, inconsciente, dolor toracico opresivo, FC 145 lpm, SatO2 85% y antecedente de infarto previo.";
            }} else if (nivel === 2) {{
                txt.value = "Paciente masculino de 42 años apuñalado en torax con herida profunda, sangrado activo moderado, diaforesis y dolor agudo severo de 30 minutos de evolucion.";
            }} else if (nivel === 3) {{
                txt.value = "Paciente femenina de 32 años acude por dolor abdominal agudo de moderada intensidad, fiebre de 39 grados y vomito persistente de 8 horas de evolucion.";
            }} else if (nivel === 5) {{
                txt.value = "Paciente masculino de 28 años acude para renovacion de formula medica de rutina, sin sintomas agudos ni dolor ni signos de alarma.";
            }}
        }}

        window.onload = autenticar;
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
