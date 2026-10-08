import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.mcp import MCPServerStreamableHttp

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
# AGENTES ESPECIALIZADOS
# ============================================================

async def main():
    async with MCPServerStreamableHttp(
        name="Parachute MCP",
        params={"url": "http://127.0.0.1:8000/mcp", "timeout": 30},
        cache_tools_list=True,
    ) as mcp_server:
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
            mcp_servers=[mcp_server],
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
            mcp_servers=[mcp_server]
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
            mcp_servers=[mcp_server],
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

        print("\nParachute S.A. - Arquitectura Centralizada (MCP)")
        print("Escribe 'Bye' para salir.\n")

        while True:
            try:
                user_input = await asyncio.to_thread(input, "Usuario: ")
                user_input = user_input.strip()
                if user_input.lower() == "bye":
                    print("Hasta luego.")
                    break
                if not user_input:
                    continue
                result = await Runner.run(manager_agent, user_input)
                print(f"\nAgente: {result.final_output}\n")
            except (KeyboardInterrupt, EOFError):
                print("\nHasta luego.")
                break


if __name__ == "__main__":
    asyncio.run(main())
