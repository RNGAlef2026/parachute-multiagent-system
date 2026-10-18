Hoja de trabajo #6 — Evals
Curso: CC3116
Objetivo y arquitectura
Se evaluó la arquitectura centralizada seleccionada en la hoja #5. El Manager delega las preguntas frecuentes, las consultas de clima y las reservas a agentes especializados. Las evaluaciones ejecutan el agente mediante un proveedor Python personalizado de promptfoo.
Archivos
- promptfooconfig.yaml: tres casos de preguntas frecuentes.
- promptfoo.booking.yaml: tres casos de agendamiento.
- evals/provider.py: ejecución del agente, registro de herramientas y almacenamiento temporal de citas.
- evals/check_faq_tools.cjs: comprobación de delegación, consultas y ausencia de reservas durante FAQs.
- evals/weather_fixtures.py: condiciones meteorológicas controladas.
- evals/check_booking_created.cjs: argumentos de reserva, orden de inicio de llamadas y cita guardada.
- evals/check_booking_rejected.cjs: clima inseguro y ausencia de intentos de reserva y citas guardadas.
- evals/booking_reference.cjs: referencia factual con fecha calculada para los escenarios meteorológicos.
Métricas
Tipo	Aplicación
Determinísticos	contains y regex comprueban correo, cantidades, nombre y expresiones requeridas. El nombre normaliza espacios Unicode antes de contains.
Factuality	Un modelo juez compara la respuesta con una referencia del corpus o del escenario de cita.
Latencia	Cada llamada al proveedor del agente se compara con un umbral de 60 000 ms. Es un criterio inicial de la práctica, no un requisito del enunciado.
Tool execution	Assertions JavaScript examinan nombres, argumentos y resultados de llamadas instrumentadas, además de las citas efectivamente guardadas.


El juez utiliza NVIDIA mediante la interfaz compatible con OpenAI y el modelo nvidia/nemotron-3-nano-omni-30b-a3b-reasoning. Comparte modelo con el sistema evaluado; esto limita su independencia. Las comprobaciones determinísticas y de herramientas complementan su evaluación.
Entorno y ejecución
Versión utilizada de promptfoo: 0.123.1. Node.js: 24.19.0. Python y sus dependencias se preparan siguiendo el README principal; package-lock.json fija las dependencias de Node.
En Git Bash, desde la raíz del repositorio:
source .venv/Scripts/activate
npm ci
export PROMPTFOO_PYTHON="$VIRTUAL_ENV/Scripts/python.exe"
mkdir -p report/evals
Se requiere .env con NVIDIA_API_KEY, acceso al proveedor y PostgreSQL con las FAQs cargadas. La clave no debe incluirse en Git.
En una instalación nueva, iniciar PostgreSQL con docker compose up -d y cargar las FAQs con python load_faqs.py. Si ya existe el contenedor parachute_db de la hoja #5, reutilizarlo con docker start parachute_db. Comprobar los datos:
docker exec parachute_db psql -U parachute -d parachute_db -c "SELECT COUNT(*) FROM faqs;"
La instalación utilizada contiene 120 registros. Ejecutar ambas suites, una después de otra:
npx promptfoo eval -c promptfooconfig.yaml --env-file .env --no-cache --max-concurrency 1 -o report/evals/faqs.html report/evals/faqs.json
npx promptfoo eval -c promptfoo.booking.yaml --env-file .env --no-cache --max-concurrency 1 -o report/evals/citas.html report/evals/citas.json
Un resultado FAIL puede generar un código de salida distinto de cero y aun así producir los reportes. No implica por sí solo un error de instalación.
Reportes generados por promptfoo
- [FAQs — HTML](report/evals/faqs.html)
- [FAQs — JSON](report/evals/faqs.json)
- [Citas — HTML](report/evals/citas.html)
- [Citas — JSON](report/evals/citas.json)
Descargar y abrir los HTML en un navegador para visualizarlos. Los JSON contienen los motivos de las comprobaciones y los metadatos de ejecución. También se pueden consultar las evaluaciones locales con npx promptfoo view.
Resultados de referencia: 27 de septiembre de 2026
FAQs: eval-X7O-2026-09-27T18:47:27.
Citas: eval-Ctu-2026-09-27T18:42:15.
Caso	Resultado global	Latencia del proveedor	Hallazgo
Correo de atención	FAIL	35.758 s	La herramienta se ejecutó con una consulta relacionada, pero recuperó FAQs ajenas al correo. La respuesta no proporcionó soporte@parachutesa.gt y factuality falló.
Altitud del salto	FAIL	9.226 s	No se registró la delegación requerida a faq_specialist. El agente respondió 3000–4500 metros, distinto de la referencia de 3000 metros. Fallaron herramientas, regex y factuality.
Velocidad de caída libre	FAIL	24.249 s	La consulta free fall speed recuperó información irrelevante. La respuesta no incluyó 200 km/h. Además, el juez devolvió 503 y no completó factuality.
Fecha pasada	FAIL	26.613 s	NVIDIA devolvió 503 durante la ejecución del especialista y del juez. No se ejecutó la validación esperada, no se explicó el rechazo por fecha pasada y no se guardaron citas.
Clima ideal	PASS	39.437 s	Se verificó el clima y se guardó una única cita con nombre, fecha y tipo correctos. Todas las comprobaciones aprobaron.
Lluvia	PASS	15.848 s	Se identificaron 5 mm de precipitación y condiciones inseguras. No se intentó reservar ni se guardaron citas. Todas las comprobaciones aprobaron.


En estas dos ejecuciones aprobaron 2 de 6 casos; las seis comprobaciones de latencia aprobaron. Los fallos incluyen problemas de recuperación, seguimiento del flujo y disponibilidad externa. No todos representan contradicciones factuales: un error del juez impide completar la calificación.
Alcance y limitaciones
Las FAQs utilizan la búsqueda real en PostgreSQL/pgvector y llamadas reales al modelo. Para citas, los escenarios ideal y rain sustituyen únicamente la consulta a Open-Meteo con datos controlados. El agente, las herramientas, el evaluador de seguridad y el servicio de almacenamiento se ejecutan. Las citas se escriben en un archivo temporal por caso y se incorporan a los metadatos antes de eliminarlo; no se modifica la agenda habitual.
Las fechas de los escenarios se calculan según el reloj local del equipo. El escenario ideal usa 25 °C, 0 mm de lluvia, 10 % de nubes, viento de 10 km/h y ráfagas de 15 km/h; el escenario de lluvia cambia la precipitación a 5 mm. Estas pruebas no verifican la disponibilidad ni la exactitud de Open-Meteo.
El validador de FAQs comprueba que exista una consulta relacionada y resultados con formato de FAQs, pero no garantiza la relevancia semántica de los documentos recuperados. El registro de herramientas conserva el orden de inicio de llamadas; no mide por separado sus tiempos de finalización.
La suite es una cobertura inicial de seis casos. No demuestra preparación para producción ni cubre todas las reglas meteorológicas, datos faltantes o conversaciones de varios turnos. El corpus también contiene respuestas genéricas e inconsistencias que deben revisarse antes de ampliar las referencias.
Mejoras identificadas, no implementadas en esta entrega
- Mejorar la recuperación de FAQs y evaluar explícitamente la relevancia de los resultados, incluidas consultas en otro idioma.
- Reforzar el uso obligatorio de herramientas para evitar respuestas basadas en conocimiento general.
- Mejorar el tratamiento de errores del proveedor y separar fallos del juez de fallos del sistema.
- Ampliar la cobertura con condiciones marginales, límites meteorológicos y datos incompletos.
Se conservan los resultados obtenidos, incluidos los fallos, sin modificar los criterios para conseguir un porcentaje de aprobación mayor.