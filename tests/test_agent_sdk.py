import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel

load_dotenv()

nvidia_client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
)

model = OpenAIChatCompletionsModel(
    model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    openai_client=nvidia_client,
)



async def main():
    agent = Agent(
        name="Test Agent",
        instructions=(
            "Eres un agente de prueba. "
            "Responde de manera breve y en español."
        ),
        model=model,
    )

    result = await Runner.run(
        agent,
        "Responde solamente con: Agente funcionando con NVIDIA",
    )

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())