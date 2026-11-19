# DICCIONARIO DE DATOS (ISO/IEC 11179)
## Proyecto: AI-Triage (Versión 2.0)
**Institución:** Universidad Manuela Beltrán  
**Autores:** Leonardo Alexander Villalobos Patiño & Juan José López Reina  
**Docente:** Ing. Juan José Osorio Tabares  

---

### 1. Entidad: `especialidades`
* **Definición:** Catálogo institucional de especialidades médicas habilitadas en la IPS para derivación de triaje.
* **Clave Primaria:** `id_especialidad` (SMALLSERIAL / INTEGER)

| Elemento de Datos | Definición | Tipo | Dominio / Reglas | Nulable |
| :--- | :--- | :--- | :--- | :--- |
| `id_especialidad` | Identificador autoincremental de la especialidad | SMALLINT | Entero > 0 | No |
| `nombre` | Nombre oficial de la especialidad clínica | VARCHAR(80) | Único (ej. 'Cardiologia') | No |
| `activa` | Indicador de disponibilidad operativa | BOOLEAN | TRUE / FALSE (default TRUE) | No |

---

### 2. Entidad: `medicos`
* **Definición:** Personal médico especialista registrado y activo para atención de colas y recepción de alertas en wearables.
* **Clave Primaria:** `id_medico` (UUID v4)

| Elemento de Datos | Definición | Tipo | Dominio / Reglas | Nulable |
| :--- | :--- | :--- | :--- | :--- |
| `id_medico` | Identificador único universal del médico | UUID v4 | Cadena de 36 caracteres UUID | No |
| `nombre_completo` | Nombre y apellidos del profesional de la salud | VARCHAR(120) | Texto alfabético | No |
| `correo` | Correo electrónico institucional | VARCHAR(120) | Formato email RFC 5322, Único | No |
| `id_especialidad` | Especialidad principal asignada | SMALLINT | Clave foránea -> `especialidades` | No |
| `activo` | Estado de turno y recepción de alertas | BOOLEAN | TRUE / FALSE (default TRUE) | No |

---

### 3. Entidad: `dispositivos_wearable`
* **Definición:** Registro de relojes inteligentes vinculados a médicos para recepción de alertas críticas (FCM).
* **Clave Primaria:** `id_dispositivo` (UUID v4)

| Elemento de Datos | Definición | Tipo | Dominio / Reglas | Nulable |
| :--- | :--- | :--- | :--- | :--- |
| `id_dispositivo` | Identificador único del dispositivo | UUID v4 | Cadena UUID | No |
| `id_medico` | Médico propietario del wearable | UUID v4 | FK -> `medicos(id_medico)` ON DELETE CASCADE | No |
| `sistema_operativo` | Plataforma del reloj inteligente | VARCHAR(20) | CHECK in ('WearOS', 'watchOS', 'otro') | No |
| `fcm_token` | Token de registro de Firebase Cloud Messaging | VARCHAR(255) | Token FCM emitido por Google Services | No |
| `registrado_en` | Marca de tiempo de vinculación | TIMESTAMPTZ | Fecha UTC con zona horaria | No |

* **Restricción de unicidad:** `UNIQUE (id_medico, sistema_operativo)` (Garantiza rotación y no duplicidad, RF-11).

---

### 4. Entidad: `pacientes`
* **Definición:** Registro de pacientes ingresados referenciados por el identificador de la historia clínica de la IPS.
* **Clave Primaria:** `id_paciente` (UUID v4)

| Elemento de Datos | Definición | Tipo | Dominio / Reglas | Nulable |
| :--- | :--- | :--- | :--- | :--- |
| `id_paciente` | Identificador único interno del paciente | UUID v4 | Cadena UUID | No |
| `id_origen_clinica`| Número o código de caso en el sistema HIS/IPS | VARCHAR(40) | Único (ej. 'DOC-9982'). Sin PII directa | No |
| `creado_en` | Marca de tiempo de registro | TIMESTAMPTZ | Fecha UTC | No |

---

### 5. Entidad: `triajes`
* **Definición:** Registro del resultado de la inferencia clínica automatizada y unidad básica de la cola dinámica.
* **Clave Primaria:** `id_triaje` (UUID v4)

| Elemento de Datos | Definición | Tipo | Dominio / Reglas | Nulable |
| :--- | :--- | :--- | :--- | :--- |
| `id_triaje` | Identificador único del triaje emitido | UUID v4 | Cadena UUID | No |
| `id_paciente` | Paciente asociado | UUID v4 | FK -> `pacientes(id_paciente)` ON DELETE RESTRICT | No |
| `texto_anonimizado`| Texto clínico procesado libre de identificadores | TEXT | 30 a 10.000 caracteres | No |
| `nivel_urgencia` | Nivel de triaje según Resolución 5596/2015 | SMALLINT | CHECK (1 <= nivel_urgencia <= 5) | No |
| `puntaje_severidad`| Calificación numérica calculada por el motor | NUMERIC(5,2)| CHECK (0.0 <= puntaje_severidad <= 100.0) | No |
| `especialidad_asignada`| Especialidad médica derivada | VARCHAR(80)| FK -> `especialidades(nombre)` | No |
| `id_medico_asignado` | Médico que atiende el caso (NULL = en cola) | UUID v4 | FK -> `medicos(id_medico)` | Sí |
| `alerta_push_enviada` | Estado de notificación a wearables | BOOLEAN | TRUE si nivel 1-2 y enviado a FCM | No |
| `creado_en` | Fecha y hora exacta de clasificación | TIMESTAMPTZ | Fecha UTC | No |

* **Índice de Rendimiento:** `CREATE INDEX idx_triajes_cola ON triajes (id_medico_asignado, nivel_urgencia, puntaje_severidad DESC, creado_en);`

---

### 6. Entidad: `entidades_clinicas`
* **Definición:** Hallazgos médicos estructurados extraídos por el componente Medical NER del texto clínico.
* **Clave Primaria:** `id_entidad` (BIGSERIAL / INTEGER)

| Elemento de Datos | Definición | Tipo | Dominio / Reglas | Nulable |
| :--- | :--- | :--- | :--- | :--- |
| `id_entidad` | Identificador autoincremental del hallazgo | INTEGER | Entero > 0 | No |
| `id_triaje` | Triaje al que pertenece la entidad | UUID v4 | FK -> `triajes(id_triaje)` ON DELETE CASCADE | No |
| `tipo` | Categoría médica estandarizada | VARCHAR(20) | CHECK in ('sintoma','signo_vital','antecedente','diagnostico_cie10') | No |
| `valor` | Descripción clínica normalizada o código CIE-10 | VARCHAR(160)| Texto clínico (ej. 'dolor toracico', 'I20.9') | No |
| `confianza` | Probabilidad asignada por el modelo NER | NUMERIC(4,3)| Rango 0.000 a 1.000 | Sí |

---

### 7. Entidad: `auditoria_eventos`
* **Definición:** Registro inmutable (solo-apéndice) de todas las operaciones sensibles del sistema (RF-12, RN-07).
* **Clave Primaria:** `id_evento` (INTEGER)

| Elemento de Datos | Definición | Tipo | Dominio / Reglas | Nulable |
| :--- | :--- | :--- | :--- | :--- |
| `id_evento` | Secuencial único del evento de auditoría | INTEGER | Entero > 0 | No |
| `usuario` | Nombre del usuario que ejecutó la acción | VARCHAR(80) | Username autenticado o 'sistema' | Sí |
| `accion` | Operación realizada | VARCHAR(80) | 'LOGIN', 'ANALIZAR_TRIAJE', 'CONSULTAR_COLA', etc. | No |
| `entidad_afectada` | Recurso o tabla intervenida | VARCHAR(80) | ej. 'triajes', 'dispositivos:UUID' | Sí |
| `correlation_id` | Identificador de trazabilidad distribuida | VARCHAR(36) | UUID v4 presente en cabecera HTTP | No |
| `resultado` | Estado final de la operación | VARCHAR(20) | 'SUCCESS', 'FAILED' | No |
| `detalle` | Contexto de diagnóstico y auditoría forense | TEXT | Mensaje explicativo | Sí |
| `creado_en` | Marca temporal inmutable del suceso | TIMESTAMPTZ | Fecha UTC precisa | No |
