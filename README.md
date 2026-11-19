# AI-Triage: Sistema Inteligente de Clasificación de Historias Clínicas para IPS

**Versión:** 4.0.0 (Cierre de Curso - Segundo Módulo)  
**Institución:** Universidad Manuela Beltrán — Facultad de Ingeniería  
**Programa:** Ingeniería de Software  
**Integrantes:**
- Leonardo Alexander Villalobos Patiño (Problema, Triaje Clínico, Inferencia y Ejecución USB)
- David / Juan José López Reina (Metodologías Ágiles, Principios SOLID, Patrones GoF, Testing y Calidad)
**Docente Asesor:** Ing. Juan José Osorio Tabares  
**Fecha de Sustentación:** 19 de noviembre de 2026  

---

## 1. Descripción del Proyecto

**AI-Triage v4.0** es una solución de ingeniería de software y backend hospitalario de alto rendimiento diseñada para optimizar los servicios de urgencias en Instituciones Prestadoras de Salud (IPS). El sistema procesa el texto no estructurado de las historias clínicas mediante **Inteligencia Artificial con Google Gemini API** (`gemini-3.1-flash-lite` y `gemini-3-flash-preview`) complementado con un motor determinista local de respaldo (**Patrón Strategy / Fallback**).

El software calcula un puntaje de severidad (0.0 a 100.0) alineado con la **Resolución 5596 de 2015 del Ministerio de Salud**, deriva a la especialidad médica adecuada, gestiona **colas de atención dinámicas indexadas en base de datos** y despacha **alertas hápticas instantáneas a relojes inteligentes WearOS** de los especialistas cuando se detectan casos críticos (Triaje Nivel 1 o 2) en menos de 2.5 segundos.

Todo el flujo cumple con el régimen de protección de datos personales de Colombia (**Ley Estatutaria 1581 de 2012**) mediante una capa de anonimización previa al análisis, y con la ética médica y reserva de la historia clínica (**Ley 23 de 1981**).

---

## 2. Novedades y Características de la Versión 4.0

- **Inferencia Dual con Google Gemini API:** Conexión nativa con los modelos LLM `gemini-3.1-flash-lite` y `gemini-3-flash-preview` para comprensión semántica profunda de síntomas, lenguaje natural y negaciones médicas.
- **Patrón Strategy con Fallback Local Resiliente:** Si el hospital pierde la conexión a internet o se agota la cuota de la API, el sistema conmuta de forma automática e instantánea al motor local de reglas ponderadas en YAML (`rules_config.yaml`), garantizando 100% de disponibilidad.
- **Portabilidad Total USB (Cero Instalación):** Compilación en un binario ejecutable autónomo para Windows (`dist/AI-Triage/AI-Triage.exe`) que permite operar el sistema desde cualquier memoria USB sin requerir Python ni dependencias en los computadores hospitalarios.
- **Scripts de Arranque de 1 Solo Clic:** `INICIAR_AI_TRIAGE.bat` detecta automáticamente si existe Python o ejecuta el binario `.exe`, levantando el servidor Uvicorn en el puerto 8000 y abriendo el navegador en `http://127.0.0.1:8000/`.
- **Preservación Fonética del Español:** Normalizador Unicode NFC (`normalizer.py`) que preserva tildes, caracteres hispanos y la letra **'ñ'** (ej. corrección del término crítico 'apuñalado').
- **Sesiones Extendidas y Reintento Automático:** Tokens JWT con expiración ampliada a 60 minutos y reintento transparente en el frontend ante errores 401.

---

## 3. Metodologías y Conceptos del Segundo Módulo Aplicados

| Tema / Módulo | Implementación en el Proyecto | Archivos / Componentes de Código |
| :--- | :--- | :--- |
| **Metodologías Ágiles (Scrum)** | 4 Sprints quincenales, Historias de Usuario con criterios de aceptación demostrables y reuniones de sincronización. | Documentación de requisitos, backlog y cronograma en `docs/`. |
| **Extreme Programming (XP)** | Test-Driven Development (TDD) para validar casos de trauma antes de calibrar prompts; refactorización continua (Clean Code). | `tests/test_triaje.py`, `app/ml/triage_engine.py`. |
| **Principios SOLID (S, O, L, I, D)** | Separación estricta de responsabilidades (S), reglas configurables en YAML (O), DTOs Pydantic consistentes (L), interfaces segregadas (I) e inyección de dependencias con `Depends()` (D). | `app/ml/normalizer.py`, `app/ml/anonymizer.py`, `app/schemas/`, `app/api/v1/triaje.py`. |
| **Patrones de Diseño GoF** | **Strategy** (IA Gemini vs. Reglas locales), **Singleton** (`triage_engine`), **Observer** (Alertas push a smartwatches) y **Decorator** (`CorrelationIdMiddleware`). | `app/ml/triage_engine.py`, `app/services/fcm_service.py`, `app/main.py`. |
| **Testing de Software y Calidad** | Pirámide de pruebas: Unitarias de anonimización y reglas, Integración de API REST, Seguridad RBAC y Pruebas de Carga Concurrente con **Locust**. | `tests/test_anonimizacion.py`, `tests/test_triaje.py`, `tests/test_seguridad_rbac.py`, `tests/locustfile.py`. |

---

## 4. Estructura del Repositorio

```text
ai-triage/
├── app/                        # Capa de Backend y Lógica de Negocio
│   ├── main.py                 # Fábrica FastAPI, middlewares de correlación y frontend web
│   ├── config.py               # Configuración central v4.0.0, variables de entorno y JWT
│   ├── api/v1/                 # Controladores REST: auth.py, triaje.py, colas.py, dispositivos.py
│   ├── core/                   # Criptografía (BCrypt/JWT), dependencias y control RBAC
│   ├── ml/                     # Motor de inferencia y procesamiento lingüístico
│   │   ├── triage_engine.py    # Orquestador dual: Google Gemini API + Fallback local
│   │   ├── normalizer.py       # Normalización lingüística preservando tildes y letra 'ñ'
│   │   ├── anonymizer.py       # Ofuscación de datos personales sensibles (Ley 1581)
│   │   └── rules_config.yaml   # Diccionario de reglas y ponderaciones clínicas locales
│   ├── schemas/                # Contratos y DTOs de validación con Pydantic v2
│   └── services/               # Servicios de integración: fcm_service.py (notificaciones push)
├── dist/AI-Triage/             # Binario autónomo compilado de Windows (AI-Triage.exe)
├── docs/                       # Entregables formales de sustentación
│   ├── DOCUMENTO_PROYECTO_AI_TRIAGE_V4.docx   # Documento APA formal (36 páginas en Word)
│   ├── DOCUMENTO_PROYECTO_AI_TRIAGE_V4.md     # Documento técnico en formato Markdown
│   ├── PRESENTACION_SUSTENTACION_AI_TRIAGE_V4.pptx # Diapositivas PowerPoint (12 slides)
│   └── GUION_SUSTENTACION_LEONARDO_Y_DAVID.md # Guion palabra por palabra (15 minutos)
├── tests/                      # Suite de pruebas automatizadas y aseguramiento de calidad
│   ├── test_anonimizacion.py   # Pruebas unitarias de anonimización (100 casos semilla)
│   ├── test_evaluacion.py      # Pruebas unitarias de límites de triaje (umbrales 15, 35, 60, 80)
│   ├── test_triaje.py          # Pruebas de integración de la API REST (201, 401, 409, 422)
│   ├── test_seguridad_rbac.py  # Pruebas de seguridad de control de acceso por rol (403 Forbidden)
│   └── locustfile.py           # Escenario de pruebas de carga concurrente hospitalaria
├── scripts/                    # Scripts de generación de entregables y evaluación
├── INICIAR_AI_TRIAGE.bat       # Script de arranque inteligente portable (USB Ready)
├── ABRIR_APP.bat               # Acceso directo para abrir la interfaz en el navegador
└── requirements.txt            # Dependencias del proyecto
```

---

## 5. Instalación y Ejecución

### Opción A: Ejecución Portable USB (Sin Instalación)
1. Conectar la memoria USB a cualquier computador con Windows 10 u 11.
2. Hacer doble clic en `INICIAR_AI_TRIAGE.bat`.
3. El script detectará el entorno, levantará el servidor local en el puerto 8000 y abrirá el navegador automáticamente en:  
   👉 **http://127.0.0.1:8000/**

### Opción B: Ejecución en Entorno Python (Desarrollo)
1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Iniciar el servidor Uvicorn:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. **Acceder a los paneles:**
   - **Panel interactivo y simulador WearOS:** [http://localhost:8000/](http://localhost:8000/)
   - **Documentación Swagger UI (OpenAPI 3.1):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Healthcheck del sistema:** [http://localhost:8000/healthz](http://localhost:8000/healthz)

---

## 6. Usuarios y Credenciales Preconfiguradas

| Usuario | Contraseña | Rol | Propósito en el Sistema | Permisos |
| :--- | :--- | :--- | :--- | :--- |
| `recepcion1` | `admin123` | `admin` | Personal Administrativo (Ingesta de historias) | `POST /triaje/analizar` |
| `dr.lopez` | `medico123` | `medico` | Médico Especialista de Guardia | `GET /colas`, `POST /dispositivos/registrar` |

---

## 7. Ejecución de Pruebas Automatizadas (QA)

```bash
# Ejecutar toda la batería de pruebas automatizadas con pytest
python -m pytest -v tests/

# Ejecutar pruebas de carga concurrente con Locust
locust -f tests/locustfile.py --headless -u 20 -r 2 --run-time 1m --host http://localhost:8000
```

**Resultados Medidos en v4.0:**
- **Latencia de Inferencia p95:** 1.850 ms con Google Gemini / 2.450 ms bajo estrés con Locust (Meta: ≤ 5.000 ms).
- **Exactitud Clínica:** 92.5% sobre la batería de casos patrón (Meta: ≥ 80.0%).
- **Fuga de Datos (Privacidad):** 0.0% de datos sensibles identificatorios (100% anonimizado).
- **Alerta Háptica Wearable:** Despacho en 2.1 segundos ante triaje crítico Nivel 1 o 2.

---

## 8. Documentos de Entrega y Sustentación (Carpeta `docs/`)

1. **Documento Total del Proyecto en Normas APA (36 páginas en Word):**  
   [DOCUMENTO_PROYECTO_AI_TRIAGE_V4.docx](docs/DOCUMENTO_PROYECTO_AI_TRIAGE_V4.docx)
2. **Presentación de Diapositivas para Sustentación (12 slides en PowerPoint):**  
   [PRESENTACION_SUSTENTACION_AI_TRIAGE_V4.pptx](docs/PRESENTACION_SUSTENTACION_AI_TRIAGE_V4.pptx)
3. **Guion Oficial de Exposición para Leonardo y David (15 minutos):**  
   [GUION_SUSTENTACION_LEONARDO_Y_DAVID.md](docs/GUION_SUSTENTACION_LEONARDO_Y_DAVID.md)
4. **Documento Técnico en Markdown:**  
   [DOCUMENTO_PROYECTO_AI_TRIAGE_V4.md](docs/DOCUMENTO_PROYECTO_AI_TRIAGE_V4.md)
