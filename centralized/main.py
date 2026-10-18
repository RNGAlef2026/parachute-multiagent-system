
"""Cliente de terminal A2A para Parachute S.A."""

import asyncio
import logging

import httpx

from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)
from a2a.utils import new_agent_text_message


A2A_URL = "http://127.0.0.1:8001"

logging.getLogger("httpx").setLevel(logging.WARNING)


async def main():
    print("\nParachute S.A. - Cliente A2A")
    print("Escribe 'Bye' para salir.\n")

    async with httpx.AsyncClient(timeout=120.0) as http_client:

        # Descubrir el agente mediante su Agent Card
        try:
            response = await http_client.get(
                f"{A2A_URL}/.well-known/agent-card.json"
            )
            response.raise_for_status()

            agent_card = AgentCard.model_validate(
                response.json()
            )

            client = A2AClient(
                httpx_client=http_client,
                agent_card=agent_card,
            )

            print(f"Conectado a: {agent_card.name}")
            print(
                "Skills disponibles: "
                + ", ".join(skill.id for skill in agent_card.skills)
                + "\n"
            )

        except Exception as error:
            print(f"No se pudo conectar al servidor A2A: {error}")
            return

        while True:
            try:
                question = (
                    await asyncio.to_thread(input, "Usuario: ")
                ).strip()

                if question.lower() == "bye":
                    print("Hasta luego.")
                    break

                if not question:
                    continue

                message = new_agent_text_message(question)

                request = SendMessageRequest(
                    id=message.message_id,
                    params=MessageSendParams(
                        message=message
                    ),
                )

                response = await client.send_message(request)

                # El SDK devuelve una respuesta JSON-RPC
                result = response.root

                if hasattr(result, "error"):
                    print(f"\nError A2A: {result.error}\n")
                    continue

                payload = result.result

                # Respuesta directa tipo Message
                if hasattr(payload, "parts"):
                    parts = payload.parts

                # Respuesta tipo Task con mensajes o artifacts
                else:
                    parts = []

                    if payload.status.message:
                        parts.extend(payload.status.message.parts)

                    for artifact in payload.artifacts or []:
                        parts.extend(artifact.parts)

                texts = [
                    part.root.text
                    for part in parts
                    if getattr(part.root, "text", None) is not None
                ]

                answer = "\n".join(texts).strip()

                print(
                    f"\nAgente: {answer or 'Sin respuesta de texto.'}\n"
                )

            except (KeyboardInterrupt, EOFError):
                print("\nHasta luego.")
                break

            except Exception as error:
                print(f"\nError de comunicacion A2A: {error}\n")


if __name__ == "__main__":
    asyncio.run(main())
