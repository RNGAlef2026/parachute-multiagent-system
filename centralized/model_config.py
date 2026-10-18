
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv()
set_tracing_disabled(True)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-20b"

groq_client = AsyncOpenAI(
    base_url=GROQ_BASE_URL,
    api_key=os.getenv("GROQ_API_KEY"),
)

model = OpenAIChatCompletionsModel(
    model=GROQ_MODEL,
    openai_client=groq_client,
)
