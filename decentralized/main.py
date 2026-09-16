import asyncio
import os
from datetime import date

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool, set_tracing_disabled, handoff, ModelSettings

from shared.faq_service import search_faq
from shared.date_validator import validate_forecast_date
from shared.weather_service import get_weather
from shared.safety_evaluator import evaluate_jump_safety
from shared.calendar_service import create_appointment

from pydantic import BaseModel

# ============================================================
# CONFIGURACION DEL MODELO
# ============================================================

load_dotenv()
set_tracing_disabled(True)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "qwen/qwen3.8-27b"

groq_client = AsyncOpenAI(
    base_url=GROQ_BASE_URL,
    api_key=os.getenv("GROQ_API_KEY"),
)

model = OpenAIChatCompletionsModel(
    model=GROQ_MODEL,
    openai_client=groq_client,
)

default_model_settings = ModelSettings(
    max_tokens=500,
)

tool_required_settings = ModelSettings(
    max_tokens=500,
    tool_choice="required",
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
# AGENTES DESCENTRALIZADOS
# ============================================================

faq_agent = Agent(
    name="FAQ Agent",
    instructions=(
        "Eres el especialista en preguntas frecuentes de Parachute S.A. "
        "Utiliza search_faq_tool para responder utilizando unicamente "
        "la base de conocimientos. "
        "Si la consulta cambia hacia clima o seguridad, "
        "transfiere el control al agente correspondiente. "
        "No inventes informacion. "
        "Responde en español."
    ),
    model=model,
    model_settings=tool_required_settings,
    tools=[search_faq_tool],
)


weather_agent = Agent(
    name="Weather Agent",
    instructions=(
        "Eres el especialista en clima y seguridad de Parachute S.A.\n\n"

        "Cuando recibas una fecha debes utilizar obligatoriamente "
        "check_weather_tool para evaluarla.\n\n"

        "Si la solicitud original es solamente consultar clima o seguridad, "
        "responde al usuario con el resultado.\n\n"

        "Si la solicitud original pide una reservacion:\n"
        "- Primero utiliza check_weather_tool.\n"
        "- Si el resultado es UNSAFE, rechaza la reservacion y NO "
        "realices ningun handoff al Booking Agent.\n"
        "- Si el resultado es IDEAL, realiza un handoff al Booking Agent.\n"
        "- Si el resultado es MARGINAL, solo procede cuando corresponda "
        "a tandem experimentado.\n\n"

        "Nunca inventes condiciones meteorologicas."
    ),
    model=model,
    model_settings=tool_required_settings,
    tools=[check_weather_tool],
)


booking_agent = Agent(
    name="Booking Agent",
    instructions=(
        "Eres el especialista en reservaciones de Parachute S.A.\n\n"

        "Cuando recibas el control desde Weather Agent, significa que "
        "las condiciones meteorologicas ya fueron evaluadas y permiten "
        "continuar con la reservacion.\n\n"

        "Para crear una cita necesitas nombre, fecha y tipo de salto. "
        "Si tienes esos datos, utiliza create_appointment_tool. "
        "Si falta algun dato, solicitalo al usuario. "
        "No inventes informacion faltante.\n\n"

        "Si recibes una nueva solicitud que requiere volver a verificar "
        "otra fecha, realiza un handoff al Weather Agent."
    ),
    model=model,
    model_settings=tool_required_settings,
    tools=[create_appointment_tool],
)

class HandoffInput(BaseModel):
    reason: str

async def on_handoff(context, input_data: HandoffInput):
    pass

to_faq = handoff(
    agent=faq_agent,
    tool_name_override="transfer_to_faq_agent",
    tool_description_override=(
        "Transfiere el control al FAQ Agent para atender "
        "preguntas frecuentes de Parachute S.A."
    ),
    input_type=HandoffInput,
    on_handoff=on_handoff,
)


to_weather = handoff(
    agent=weather_agent,
    tool_name_override="transfer_to_weather_agent",
    tool_description_override=(
        "Transfiere el control al Weather Agent para consultar "
        "clima o evaluar la seguridad de una fecha."
    ),
    input_type=HandoffInput,
    on_handoff=on_handoff,
)


to_booking = handoff(
    agent=booking_agent,
    tool_name_override="transfer_to_booking_agent",
    tool_description_override=(
        "Transfiere el control al Booking Agent cuando las "
        "condiciones permitan continuar con una reservacion."
    ),
    input_type=HandoffInput,
    on_handoff=on_handoff,
)

weather_agent.handoffs = [
    to_booking,
    to_faq,
]

booking_agent.handoffs = [
    to_weather,
]

faq_agent.handoffs = [
    to_weather,
]

# ============================================================
# AGENTE DE ENTRADA
# ============================================================

triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "Eres exclusivamente el enrutador de Parachute S.A. "
        "Debes ejecutar una herramienta de transferencia para cada "
        "solicitud que recibas.\n\n"

        "Usa transfer_to_faq_agent para preguntas frecuentes.\n"
        "Usa transfer_to_weather_agent para clima y seguridad.\n"
        "Usa transfer_to_weather_agent tambien para reservaciones, "
        "porque toda reservacion debe verificar primero el clima.\n\n"

        "No respondas diciendo que vas a transferir al usuario. "
        "No describas la transferencia. "
        "Debes llamar directamente a la herramienta transfer_to_* apropiada."
    ),
    model=model,
    model_settings=tool_required_settings,
    handoffs=[
        to_faq,
        to_weather,
    ],
)


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

async def main():
    print("\nParachute S.A. - Arquitectura Descentralizada")
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
                triage_agent,
                user_input,
            )

            print(f"\nAgente: {result.final_output}\n")

        except KeyboardInterrupt:
            print("\nHasta luego.")
            break


if __name__ == "__main__":
    asyncio.run(main())