
from agents import Agent

from centralized.model_config import model


def create_manager(mcp_server):
    """
    Construye el sistema multiagente centralizado
    utilizando las herramientas del servidor MCP.
    """

    faq_agent = Agent(
        name="FAQ Agent",
        instructions=(
            "Eres el especialista en preguntas frecuentes de Parachute S.A. "
            "Utiliza search_faq_tool para consultar la base de conocimientos. "
            "No inventes informacion. Responde en español."
        ),
        model=model,
        mcp_servers=[mcp_server],
    )

    weather_agent = Agent(
        name="Weather Agent",
        instructions=(
            "Eres el especialista meteorologico de Parachute S.A. "
            "Utiliza check_weather_tool para evaluar las condiciones "
            "de seguridad antes de realizar un salto. "
            "No inventes datos meteorologicos. Responde en español."
        ),
        model=model,
        mcp_servers=[mcp_server],
    )

    booking_agent = Agent(
        name="Booking Agent",
        instructions=(
            "Eres el especialista en reservaciones de Parachute S.A. "
            "Utiliza create_appointment_tool para gestionar las citas. "
            "Necesitas nombre, fecha y tipo de salto. "
            "Respeta las restricciones meteorologicas."
        ),
        model=model,
        mcp_servers=[mcp_server],
    )

    manager = Agent(
        name="Manager Agent",
        instructions=(
            "Eres el coordinador central de Parachute S.A. "
            "Delega preguntas frecuentes al especialista FAQ. "
            "Delega consultas meteorologicas al especialista de clima. "
            "Para reservar, primero verifica las condiciones del clima. "
            "No confirmes citas si las condiciones son inseguras. "
            "Nunca inventes informacion ni confirmaciones."
        ),
        model=model,
        tools=[
            faq_agent.as_tool(
                tool_name="faq_specialist",
                tool_description="Responde preguntas frecuentes.",
            ),
            weather_agent.as_tool(
                tool_name="weather_specialist",
                tool_description="Consulta clima y seguridad.",
            ),
            booking_agent.as_tool(
                tool_name="booking_specialist",
                tool_description="Gestiona reservaciones.",
            ),
        ],
    )

    return manager
