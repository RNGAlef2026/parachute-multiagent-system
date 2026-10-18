
"""Conecta el protocolo A2A con el sistema multiagente de Parachute S.A."""

import logging
import os

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from agents import Runner
from agents.mcp import MCPServerStreamableHttp

from centralized.agent_system import create_manager


logger = logging.getLogger("parachute-a2a")


class ParachuteExecutor(AgentExecutor):

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:

        # Extraer el mensaje recibido del cliente A2A
        parts = context.message.parts if context.message else []

        question = "\n".join(
            part.root.text
            for part in parts
            if getattr(part.root, "text", None) is not None
        ).strip()

        if not question:
            await event_queue.enqueue_event(
                new_agent_text_message("Envia una consulta de texto.")
            )
            return

        logger.info("Solicitud A2A recibida: %s", question)

        try:
            # Conectarse al servidor MCP existente
            async with MCPServerStreamableHttp(
                name="Parachute MCP",
                params={
                    "url": os.getenv(
                        "MCP_URL",
                        "http://127.0.0.1:8000/mcp"
                    ),
                    "timeout": 60,
                },
                cache_tools_list=True,
            ) as mcp:

                # Reutilizar el sistema multiagente
                manager = create_manager(mcp)

                # Ejecutar la solicitud
                result = await Runner.run(manager, question)

                answer = str(result.final_output)

            # Enviar respuesta al cliente A2A
            await event_queue.enqueue_event(
                new_agent_text_message(answer)
            )

            logger.info("Respuesta A2A enviada")

        except Exception:
            logger.exception("Error al procesar solicitud A2A")

            await event_queue.enqueue_event(
                new_agent_text_message(
                    "No se pudo procesar la solicitud. "
                    "Verifica MCP, el modelo y sus credenciales."
                )
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        logger.info("Cancelacion A2A solicitada")
        raise NotImplementedError(
            "La cancelacion de tareas no esta implementada."
        )
