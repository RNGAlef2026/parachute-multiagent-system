# Parachute S.A. - Multi-Agent System

Proyecto académico desarrollado para comparar tres arquitecturas de orquestación de sistemas multiagente (MAS) utilizando OpenAI Agents SDK.

El mismo problema de Parachute S.A. se implementa mediante tres arquitecturas diferentes:

- Centralizada
- Jerárquica
- Descentralizada

Las integraciones y reglas de negocio se encuentran separadas de la lógica de orquestación para facilitar la reutilización y la incorporación de nuevos requerimientos.

---

## Funcionalidades

El sistema permite:

- Responder preguntas frecuentes de Parachute S.A.
- Realizar búsqueda semántica mediante embeddings.
- Almacenar y consultar embeddings utilizando PostgreSQL + pgvector.
- Consultar pronósticos meteorológicos mediante Open-Meteo.
- Validar que la fecha solicitada se encuentre dentro del rango disponible de pronóstico.
- Evaluar automáticamente las condiciones de seguridad para realizar un salto.
- Rechazar reservaciones cuando las condiciones meteorológicas sean inseguras.
- Calendarizar citas cuando las condiciones permitan realizar el salto.
- Mantener una interfaz interactiva mediante terminal.
- Comparar tres formas distintas de orquestación multiagente.

---

## Tecnologías utilizadas

- Python
- OpenAI Agents SDK
- NVIDIA Build
- Groq
- Open-Meteo API
- PostgreSQL 17
- pgvector
- Sentence Transformers
- Docker

---

## Estructura del proyecto

```text
parachute-multiagent-system/
|
|-- centralized/
|   `-- main.py
|
|-- hierarchical/
|   `-- main.py
|
|-- decentralized/
|   `-- main.py
|
|-- shared/
|   |-- calendar_service.py
|   |-- date_validator.py
|   |-- faq_service.py
|   |-- safety_evaluator.py
|   `-- weather_service.py
|
|-- tests/
|
|-- diagrams/
|
|-- report/
|
|-- Corpus_FAQs_Parachute_SA_2026.txt
|-- load_faqs.py
|-- docker-compose.yml
|-- requirements.txt
|-- .env.example
|-- .gitignore
`-- README.md
```

---

# Arquitecturas

## 1. Arquitectura centralizada

La arquitectura centralizada utiliza un agente Manager como punto principal de coordinación.

El Manager recibe las solicitudes del usuario y utiliza agentes especializados mediante `as_tool()`.

```text
                        Usuario
                           |
                           v
                     Manager Agent
                    /      |       \
                   /       |        \
                  v        v         v
             FAQ Agent  Weather   Booking
                 |        Agent      Agent
                 |          |          |
                 v          v          v
              pgvector  Open-Meteo   Calendar
                            |
                            v
                    Safety Evaluator
```

El Manager mantiene el control del proceso y decide qué especialista debe utilizar.

---

## 2. Arquitectura jerárquica

La arquitectura jerárquica introduce diferentes niveles de supervisión.

```text
                         Usuario
                            |
                            v
                       Root Manager
                      /            \
                     /              \
                    v                v
          FAQ Supervisor      Booking Supervisor
                 |               /          \
                 |              /            \
                 v             v              v
             FAQ Agent    Weather Agent   Calendar Agent
                 |             |
                 v             v
              pgvector     Open-Meteo
                                |
                                v
                        Safety Evaluator
```

El `Root Manager` no accede directamente a todos los trabajadores.

En su lugar, delega responsabilidades a supervisores intermedios, que posteriormente coordinan agentes especializados.

---

## 3. Arquitectura descentralizada

La arquitectura descentralizada utiliza `handoffs` de OpenAI Agents SDK.

Los agentes pueden transferirse directamente el control sin depender de un Manager central durante todo el proceso.

```text
                         Usuario
                            |
                            v
                       Triage Agent
                       /          \
                      /            \
                     v              v
                FAQ Agent      Weather Agent
                    ^              |
                    |              |
                    |              v
                    +-------- Booking Agent
                           handoffs
```

El `Triage Agent` únicamente determina el especialista inicial.

Después del primer `handoff`, los agentes especializados pueden transferirse el control directamente cuando sea necesario.

---

# Servicios compartidos

Las tres arquitecturas reutilizan la misma lógica de integración.

```text
shared/
|
|-- faq_service.py
|-- weather_service.py
|-- safety_evaluator.py
|-- date_validator.py
`-- calendar_service.py
```

Esto permite modificar una integración sin tener que reimplementar la lógica para cada arquitectura.

---

# Base de conocimiento

La base de FAQs utiliza:

```text
PostgreSQL + pgvector
```

Los embeddings son generados localmente mediante:

```text
all-MiniLM-L6-v2
```

Este modelo produce vectores de:

```text
384 dimensiones
```

La tabla utilizada es:

```text
faqs
|
|-- id
|-- categoria
|-- pregunta
|-- respuesta
`-- embedding vector(384)
```

El corpus contiene:

```text
120 FAQs
```

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/RNGAlef2026/parachute-multiagent-system.git
```

Entrar al proyecto:

```bash
cd parachute-multiagent-system
```

---

## 2. Crear un entorno virtual

```bash
python -m venv .venv
```

### Git Bash / Windows

```bash
source .venv/Scripts/activate
```

### PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

---

## 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

---

## 4. Configurar las variables de entorno

Crear un archivo:

```text
.env
```

en la raíz del proyecto.

Agregar:

```env
NVIDIA_API_KEY=your_nvidia_api_key
GROQ_API_KEY=your_groq_api_key
```

Las claves reales no deben almacenarse en el repositorio.

El archivo `.env` se encuentra excluido mediante `.gitignore`.

---

# Inicialización de PostgreSQL

## 5. Levantar PostgreSQL + pgvector

Es necesario tener Docker Desktop ejecutándose.

Ejecutar:

```bash
docker compose up -d
```

Verificar:

```bash
docker ps
```

Debe aparecer el contenedor:

```text
parachute_db
```

La configuración utilizada es:

```text
PostgreSQL: 17
Extensión: pgvector
Puerto: 5432
Base de datos: parachute_db
Usuario: parachute
```

---

## 6. Cargar la base de FAQs

Una vez que PostgreSQL se encuentre en ejecución:

```bash
python load_faqs.py
```

El script realiza automáticamente:

1. Lectura del corpus de Parachute S.A.
2. Detección de las 120 FAQs.
3. Activación de la extensión `pgvector`.
4. Creación de la tabla `faqs` si no existe.
5. Generación de embeddings con `all-MiniLM-L6-v2`.
6. Inserción de los embeddings en PostgreSQL.

El script utiliza:

```sql
ON CONFLICT (id) DO UPDATE
```

por lo que puede ejecutarse nuevamente sin duplicar las FAQs.

Para verificar la cantidad de registros:

```bash
docker exec -it parachute_db psql -U parachute -d parachute_db -c "SELECT COUNT(*) FROM faqs;"
```

El resultado esperado es:

```text
120
```

---

# Ejecución

Las tres implementaciones utilizan una interfaz mediante terminal.

## Arquitectura centralizada

```bash
python -m centralized.main
```

## Arquitectura jerárquica

```bash
python -m hierarchical.main
```

## Arquitectura descentralizada

```bash
python -m decentralized.main
```

Para terminar una sesión:

```text
Bye
```

También puede utilizarse:

```text
Ctrl+C
```

---

# Open-Meteo

Las condiciones meteorológicas se consultan mediante la API gratuita de Open-Meteo.

Coordenadas utilizadas:

```text
Latitud: 14.013722
Longitud: -90.771611
```

Se obtienen los siguientes valores:

- Temperatura
- Precipitación
- Cobertura de nubes
- Velocidad del viento en superficie
- Ráfagas de viento

Antes de realizar la consulta se valida que la fecha se encuentre dentro del rango de pronóstico permitido.

---

# Reglas de seguridad

Las reglas meteorológicas se encuentran implementadas mediante código determinista.

## Velocidad del viento en superficie

```text
Ideal:
< 20 km/h

Marginal:
20 - 28 km/h

NO SEGURO:
> 28 km/h
```

## Ráfagas de viento

```text
NO SEGURO:
> 35 km/h
```

## Precipitación

```text
NO SEGURO:
> 0.0 mm
```

## Cobertura de nubes

```text
Ideal:
< 30%

Marginal:
30 - 75%

NO SEGURO:
> 75%
```

La temperatura es obtenida de Open-Meteo, pero no se utiliza como criterio de rechazo debido a que el requerimiento no proporciona un límite específico de temperatura.

---

# Protección de reservaciones

Las reglas críticas de seguridad no dependen únicamente de las decisiones del LLM.

Antes de almacenar una cita, el sistema vuelve a realizar:

```text
Fecha solicitada
      |
      v
Date Validator
      |
      v
Open-Meteo
      |
      v
Safety Evaluator
      |
      +-------------------+
      |         |         |
      v         v         v
    IDEAL    MARGINAL   UNSAFE
      |         |         |
      v         v         v
   Guardar   Restringir  Rechazar
```

Esto evita que una decisión incorrecta de un agente pueda registrar una cita durante condiciones inseguras.

---

# Proveedores de modelos

El proyecto utiliza OpenAI Agents SDK para definir agentes, tools, managers y handoffs.

Durante la implementación se utilizaron proveedores externos compatibles con la API de OpenAI.

## NVIDIA Build

Utilizado principalmente en las arquitecturas:

- Centralizada
- Jerárquica

Modelo utilizado:

```text
nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
```

## Groq

Utilizado en la arquitectura descentralizada para obtener compatibilidad confiable con tool calls y handoffs.

Modelo utilizado:

```text
qwen/qwen3.8-27b
```

Endpoint:

```text
https://api.groq.com/openai/v1
```

---

# Seguridad de credenciales

Las API keys nunca se almacenan directamente en el código.

El archivo `.gitignore` excluye:

```text
.env
.venv/
appointments.json
__pycache__/
*.pyc
```

El archivo `appointments.json` se genera durante la ejecución y tampoco se almacena en el repositorio.

---

# Pruebas realizadas

Durante el desarrollo se verificaron individualmente:

- Conexión con PostgreSQL.
- Generación de embeddings de 384 dimensiones.
- Búsqueda semántica con pgvector.
- Consulta a Open-Meteo.
- Evaluación de condiciones meteorológicas.
- Validación del rango de fechas.
- Creación de citas.
- Bloqueo de citas inseguras.
- Integración con NVIDIA Build.
- Integración con Groq.
- OpenAI Agents SDK.
- `as_tool()` para agentes manager.
- `handoffs` entre agentes.
- Arquitectura centralizada.
- Arquitectura jerárquica.
- Arquitectura descentralizada.

---

# Consideraciones

Los proveedores gratuitos de modelos pueden presentar temporalmente errores de disponibilidad o límites de solicitudes.

La lógica de negocio y las integraciones se encuentran separadas de los agentes para permitir cambiar el proveedor o modelo sin modificar las reglas principales del sistema.

---

## Autor

Proyecto desarrollado para el curso **CC3116**.