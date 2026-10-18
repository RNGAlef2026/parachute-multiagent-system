
"""Servidor A2A de Parachute S.A."""

import logging
import os

import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from a2a_server.agent_executor import ParachuteExecutor


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("parachute-a2a")


def create_app():
    skills = [
        AgentSkill(
            id="faq",
            name="Preguntas frecuentes",
            description=(
                "Responde consultas sobre servicios, requisitos "
                "y politicas de Parachute S.A."
            ),
            tags=["faq", "informacion", "paracaidismo"],
            examples=[
                "¿Cuáles son los requisitos para saltar?"
            ],
        ),
        AgentSkill(
            id="weather",
            name="Consulta meteorologica",
            description=(
                "Consulta el clima y evalua las condiciones "
                "de seguridad para realizar saltos."
            ),
            tags=["clima", "seguridad", "weather"],
            examples=[
                "¿Es seguro saltar el 2026-10-20?"
            ],
        ),
        AgentSkill(
            id="booking",
            name="Reservaciones",
            description=(
                "Gestiona solicitudes de reservacion "
                "considerando las condiciones meteorologicas."
            ),
            tags=["reservaciones", "citas", "booking"],
            examples=[
                "Quiero reservar un salto para el 2026-10-20."
            ],
        ),
    ]

    agent_card = AgentCard(
        name="Parachute S.A. Multi Agent System",
        description=(
            "Sistema multiagente de Parachute S.A. "
            "para consultas, clima y reservaciones."
        ),
        url=os.getenv(
            "A2A_URL",
            "http://127.0.0.1:8001/"
        ),
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,
        ),
        skills=skills,
    )

    handler = DefaultRequestHandler(
        agent_executor=ParachuteExecutor(),
        task_store=InMemoryTaskStore(),
    )

    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler,
    ).build()


app = create_app()


if __name__ == "__main__":
    logger.info("Iniciando servidor A2A de Parachute S.A.")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info",
    )
