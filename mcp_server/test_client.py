
import asyncio
from datetime import date, timedelta

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = "http://127.0.0.1:8000/mcp"

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()

            print("\nHerramientas MCP disponibles:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            target_date = (date.today() + timedelta(days=1)).isoformat()

            print(f"\nConsultando clima para: {target_date}")

            result = await session.call_tool(
                "check_weather_tool",
                arguments={"target_date": target_date},
            )

            print("\nRespuesta del servidor MCP:")
            for content in result.content:
                if content.type == "text":
                    print(content.text)

            
            print("\nConsultando preguntas frecuentes...")

            faq_result = await session.call_tool(
                "search_faq_tool",
                arguments={
                    "query": "¿Cuáles son los requisitos para saltar en paracaídas?"
                },
            )

            print("\nRespuesta FAQ:")
            for content in faq_result.content:
                if content.type == "text":
                    print(content.text)

            
            print("\nProbando reservacion con clima inseguro...")

            booking_result = await session.call_tool(
                "create_appointment_tool",
                arguments={
                    "name": "Usuario Prueba",
                    "appointment_date": target_date,
                    "jump_type": "Tandem",
                },
            )

            print("\nRespuesta de reservacion:")
            for content in booking_result.content:
                if content.type == "text":
                    print(content.text)




if __name__ == "__main__":
    asyncio.run(main())
