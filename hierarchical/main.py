import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool

from shared.faq_service import search_faq

from datetime import date

from shared.date_validator import validate_forecast_date
from shared.weather_service import get_weather
from shared.safety_evaluator import evaluate_jump_safety
from shared.calendar_service import create_appointment


# ============================================================
# CONFIGURACION DEL MODELO
# ============================================================

load_dotenv()

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"

nvidia_client = AsyncOpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=os.getenv("NVIDIA_API_KEY"),
)

model = OpenAIChatCompletionsModel(
    model=NVIDIA_MODEL,
    openai_client=nvidia_client,
)


# ============================================================
# TOOLS
# ============================================================

@function_tool
def search_faq_tool(query: str) -> str:
    """
    Busca informacion en la base de conocimientos de FAQs
    de Parachute S.A.
    """
    results = search_faq(query, limit=3)

    if not results:
        return (
            "No se encontro informacion relacionada "
            "en la base de conocimientos."
        )

    formatted_results = []

    for result in results:
        formatted_results.append(
            f"Pregunta: {result['question']}\n"
            f"Respuesta: {result['answer']}\n"
            f"Distancia: {result['distance']:.4f}"
        )

    return "\n\n".join(formatted_results)

@function_tool
def check_weather_tool(target_date: str) -> str:
    """
    Consulta el clima para una fecha y evalua si las condiciones
    permiten realizar un salto en Parachute S.A.

    Args:
        target_date: Fecha solicitada en formato YYYY-MM-DD.
    """
    try:
        requested_date = date.fromisoformat(target_date)
    except ValueError:
        return "La fecha debe utilizar el formato YYYY-MM-DD."

    validation = validate_forecast_date(requested_date)

    if not validation["valid"]:
        return validation["message"]

    weather = get_weather(requested_date)
    evaluation = evaluate_jump_safety(weather)

    return (
        f"Fecha: {weather['date']}\n"
        f"Temperatura: {weather['temperature_2m']} C\n"
        f"Precipitacion: {weather['precipitation']} mm\n"
        f"Cobertura de nubes: {weather['cloud_cover']}%\n"
        f"Velocidad del viento: {weather['wind_speed_10m']} km/h\n"
        f"Rafagas de viento: {weather['wind_gust_10m']} km/h\n"
        f"Estado: {evaluation['status']}\n"
        f"Evaluacion: {evaluation['message']}\n"
        f"Razones de prohibicion: {evaluation['reasons']}\n"
        f"Condiciones marginales: {evaluation['marginal_reasons']}"
    )

@function_tool
def create_appointment_tool(
    name: str,
    appointment_date: str,
    jump_type: str,
) -> str:
    """
    Crea una cita para Parachute S.A.

    Args:
        name: Nombre de la persona
        appointment_date: Fecha de la cita en formato YYYY-MM-DD.
        jump_type: Tipo de salto solicitado.
    """
    appointment = create_appointment(
        name=name,
        appointment_date=appointment_date,
        jump_type=jump_type,
    )

    return (
        "Cita creada correctamente.\n"
        f"Nombre: {appointment['name']}\n"
        f"Fecha: {appointment['date']}\n"
        f"Tipo de salto: {appointment['jump_type']}"
    )

# ============================================================
# AGENTES TRABAJADORES
# ============================================================

faq_agent = Agent(
    name="FAQ Agent",
    instructions=(
        "Eres un agente trabajador especializado en preguntas frecuentes "
        "de Parachute S.A. "
        "Utiliza siempre search_faq_tool para consultar la base de "
        "conocimientos. "
        "No inventes informacion y responde en español."
    ),
    model=model,
    tools=[search_faq_tool],
)


weather_agent = Agent(
    name="Weather Agent",
    instructions=(
        "Eres un agente trabajador especializado en clima y seguridad "
        "para saltos de Parachute S.A. "
        "Utiliza siempre check_weather_tool para evaluar la fecha indicada. "
        "No inventes datos meteorologicos ni reglas de seguridad. "
        "Responde en español."
    ),
    model=model,
    tools=[check_weather_tool],
)


calendar_agent = Agent(
    name="Calendar Agent",
    instructions=(
        "Eres un agente trabajador especializado en registrar citas "
        "de Parachute S.A. "
        "Utiliza create_appointment_tool para crear una cita. "
        "Necesitas nombre, fecha y tipo de salto. "
        "No inventes informacion faltante. "
        "Responde en español."
    ),
    model=model,
    tools=[create_appointment_tool],
)


# ============================================================
# SUPERVISORES INTERMEDIOS
# ============================================================

faq_supervisor = Agent(
    name="FAQ Supervisor",
    instructions=(
        "Eres el supervisor del area de preguntas frecuentes. "
        "Cuando recibas una consulta sobre informacion de Parachute S.A., "
        "delega la investigacion al FAQ Agent mediante faq_worker. "
        "Devuelve al supervisor principal solamente informacion respaldada "
        "por la base de conocimientos."
    ),
    model=model,
    tools=[
        faq_agent.as_tool(
            tool_name="faq_worker",
            tool_description=(
                "Agente trabajador que consulta la base vectorial de FAQs."
            ),
        )
    ],
)


booking_supervisor = Agent(
    name="Booking Supervisor",
    instructions=(
        "Eres el supervisor del proceso de reservaciones de Parachute S.A. "
        "Coordinas a los trabajadores de clima y calendario.\n\n"

        "Para evaluar una fecha utiliza weather_worker.\n"

        "Si se solicita calendarizar una cita, primero debes verificar "
        "obligatoriamente el clima mediante weather_worker.\n"

        "Si el resultado es UNSAFE, no utilices calendar_worker.\n"

        "Si el resultado es IDEAL, puedes utilizar calendar_worker "
        "cuando tengas nombre, fecha y tipo de salto.\n"

        "Si el resultado es MARGINAL, solo se puede proceder cuando "
        "corresponda a tandem experimentado.\n"

        "Nunca registres una cita sin haber verificado primero "
        "las condiciones meteorologicas."
    ),
    model=model,
    tools=[
        weather_agent.as_tool(
            tool_name="weather_worker",
            tool_description=(
                "Trabajador que consulta Open-Meteo y evalua "
                "la seguridad del salto."
            ),
        ),
        calendar_agent.as_tool(
            tool_name="calendar_worker",
            tool_description=(
                "Trabajador que registra una cita de Parachute S.A."
            ),
        ),
    ],
)


# ============================================================
# SUPERVISOR PRINCIPAL
# ============================================================

root_manager = Agent(
    name="Root Manager",
    instructions=(
        "Eres el supervisor principal de Parachute S.A. "
        "No realizas directamente las tareas operativas: debes delegarlas "
        "a los supervisores correspondientes.\n\n"

        "Para preguntas frecuentes utiliza faq_department.\n"

        "Para consultas de clima, seguridad, fechas o reservaciones "
        "utiliza booking_department.\n"

        "No inventes informacion y respeta las decisiones de seguridad "
        "obtenidas por el departamento de reservaciones."
    ),
    model=model,
    tools=[
        faq_supervisor.as_tool(
            tool_name="faq_department",
            tool_description=(
                "Supervisor del departamento de preguntas frecuentes."
            ),
        ),
        booking_supervisor.as_tool(
            tool_name="booking_department",
            tool_description=(
                "Supervisor del departamento de clima, seguridad "
                "y reservaciones."
            ),
        ),
    ],
)


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

async def main():
    print("\nParachute S.A. - Arquitectura Jerarquica")
    print("Escribe 'Bye' para salir.\n")

    while True:
        try:
            user_input = input("Usuario: ").strip()

            if user_input.lower() == "bye":
                print("Hasta luego.")
                break

            if not user_input:
                continue

            result = await Runner.run(
                root_manager,
                user_input,
            )

            print(f"\nAgente: {result.final_output}\n")

        except KeyboardInterrupt:
            print("\nHasta luego.")
            break


if __name__ == "__main__":
    asyncio.run(main())