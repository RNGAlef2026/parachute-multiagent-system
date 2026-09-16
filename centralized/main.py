import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool, set_tracing_disabled

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
set_tracing_disabled(True)

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
    Verifica las condiciones meteorologicas y crea una cita
    solamente cuando sea seguro proceder.

    Args:
        name: Nombre de la persona.
        appointment_date: Fecha de la cita en formato YYYY-MM-DD.
        jump_type: Tipo de salto solicitado.
    """
    try:
        requested_date = date.fromisoformat(appointment_date)
    except ValueError:
        return "La fecha debe utilizar el formato YYYY-MM-DD."

    validation = validate_forecast_date(requested_date)

    if not validation["valid"]:
        return validation["message"]

    weather = get_weather(requested_date)
    evaluation = evaluate_jump_safety(weather)

    if evaluation["status"] == "UNSAFE":
        return (
            "Cita rechazada. Las condiciones meteorologicas "
            "son NO SEGURAS / PROHIBIDAS para esa fecha. "
            f"Razones: {evaluation['reasons']}"
        )

    if evaluation["status"] == "MARGINAL":
        return (
            "La cita no puede confirmarse automaticamente porque "
            "las condiciones son MARGINALES. "
            "Solo se permite proceder cuando corresponda a un "
            "salto tandem experimentado. "
            f"Condiciones: {evaluation['marginal_reasons']}"
        )

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
# AGENTES ESPECIALIZADOS
# ============================================================

faq_agent = Agent(
    name="FAQ Agent",
    instructions=(
        "Eres el agente especializado en preguntas frecuentes "
        "de Parachute S.A. "
        "Para responder preguntas debes utilizar search_faq_tool. "
        "Basa tus respuestas unicamente en la informacion obtenida "
        "de la base de conocimientos. "
        "Si la informacion recuperada no permite responder la pregunta, "
        "indica que no cuentas con esa informacion. "
        "Responde de forma clara, breve y en español."
    ),
    model=model,
    tools=[search_faq_tool],
)

weather_agent = Agent(
    name="Weather Agent",
    instructions=(
        "Eres el especialista meteorologico y de seguridad de Parachute S.A. "
        "Cuando debas evaluar una fecha para realizar un salto, utiliza "
        "check_weather_tool. "
        "Nunca inventes datos meteorologicos ni determines la seguridad "
        "por tu cuenta: utiliza siempre el resultado de la herramienta. "
        "Si la fecha esta fuera del rango disponible de pronostico, "
        "informa claramente al usuario. "
        "Responde en español."
    ),
    model=model,
    tools=[check_weather_tool]
)

booking_agent = Agent(
    name="Booking Agent",
    instructions=(
        "Eres el especialista en calendarizacion de Parachute S.A. "
        "Utiliza create_appointment_tool para registrar una cita "
        "solamente cuando el Manager te indique que las condiciones "
        "meteorologicas permiten realizarla. "
        "Necesitas nombre, fecha y tipo de salto antes de crearla. "
        "Si falta algun dato, indicalo en lugar de inventarlo. "
        "Responde en español."
    ),
    model=model,
    tools=[create_appointment_tool],
)

# ============================================================
# MANAGER CENTRAL
# ============================================================

manager_agent = Agent(
    name="Manager Agent",
    instructions=(
        "Eres el agente central y supervisor de Parachute S.A. "
        "Tu responsabilidad es decidir que especialista utilizar.\n\n"

        "Para preguntas frecuentes utiliza faq_specialist.\n"

        "Para consultar clima o evaluar si una fecha es segura para saltar, "
        "utiliza weather_specialist.\n"

        "Para calendarizar una cita debes seguir obligatoriamente este flujo:\n"
        "1. Asegurate de conocer la fecha solicitada.\n"
        "2. Utiliza weather_specialist para evaluar esa fecha.\n"
        "3. Si el resultado es UNSAFE, NO calendarices la cita.\n"
        "4. Si es IDEAL, puedes utilizar booking_specialist.\n"
        "5. Si es MARGINAL, explica la restriccion y solo procede cuando "
        "corresponda a un salto tandem experimentado.\n"
        "6. Para reservar necesitas nombre, fecha y tipo de salto. "
        "Si falta informacion, solicitala al usuario.\n\n"

        "Nunca inventes informacion meteorologica, FAQs ni confirmaciones "
        "de citas. Utiliza siempre los agentes especializados."
    ),
    model=model,
    tools=[
        faq_agent.as_tool(
            tool_name="faq_specialist",
            tool_description=(
                "Consulta al especialista en preguntas frecuentes "
                "de Parachute S.A."
            ),
        ),
        weather_agent.as_tool(
            tool_name="weather_specialist",
            tool_description=(
                "Consulta clima y determina si una fecha es segura "
                "para realizar un salto."
            ),
        ),
        booking_agent.as_tool(
            tool_name="booking_specialist",
            tool_description=(
                "Calendariza una cita cuando las condiciones "
                "meteorologicas ya fueron verificadas."
            ),
        ),
    ],
)


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

async def main():
    print("\nParachute S.A. - Arquitectura Centralizada")
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
                manager_agent,
                user_input,
            )

            print(f"\nAgente: {result.final_output}\n")

        except KeyboardInterrupt:
            print("\nHasta luego.")
            break


if __name__ == "__main__":
    asyncio.run(main())