import asyncio
import json
import sys
from contextlib import nullcontext
from datetime import date, timedelta

from contextvars import ContextVar
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from evals.weather_fixtures import controlled_weather
from agents import Runner
from shared import calendar_service
from centralized.main import (
    manager_agent,
    faq_agent,
    weather_agent,
    booking_agent,
)

# Cada evaluación mantiene su propio registro.
tool_log = ContextVar("tool_log", default=None)


def instrument_tool(tool):
    original = tool.on_invoke_tool

    async def tracked_call(context, arguments):
        calls = tool_log.get()

        if calls is None:
            return await original(context, arguments)

        try:
            parsed_arguments = json.loads(arguments)
        except json.JSONDecodeError:
            parsed_arguments = {"invalid_json": arguments}

        entry = {
            "name": tool.name,
            "arguments": parsed_arguments,
            "status": "started",
        }
        calls.append(entry)

        try:
            result = await original(context, arguments)
            entry["status"] = "returned"
            entry["result"] = str(result)
            return result
        except Exception as exc:
            entry["status"] = "exception"
            entry["error_type"] = type(exc).__name__
            raise

    tool.on_invoke_tool = tracked_call


# Incluye las herramientas internas de los especialistas.
seen = set()

for agent in (manager_agent, faq_agent, weather_agent, booking_agent):
    for tool in agent.tools:
        if id(tool) not in seen:
            instrument_tool(tool)
            seen.add(id(tool))


# Evita que dos evaluaciones compartan el archivo temporal.
evaluation_lock = asyncio.Lock()


async def call_api(prompt, options, context):
    async with evaluation_lock:
        calls = []
        token = tool_log.set(calls)
        original_file = calendar_service.APPOINTMENTS_FILE

        variables = context.get("vars", {})
        scenario = variables.get("weather_scenario")

        today = date.today()
        tomorrow = (today + timedelta(days=1)).isoformat()

        actual_prompt = prompt
        if scenario:
            actual_prompt = (
                f"Fecha actual: {today.isoformat()}. "
                f"Mañana corresponde a {tomorrow}.\n\n"
                f"{prompt}"
            )

        weather_context = (
            controlled_weather(scenario)
            if scenario
            else nullcontext()
        )

        try:
            with TemporaryDirectory(prefix="parachute_eval_") as folder:
                evaluation_file = Path(folder) / "appointments.json"
                evaluation_file.write_text("[]", encoding="utf-8")
                calendar_service.APPOINTMENTS_FILE = evaluation_file

                with weather_context:
                    result = await Runner.run(
                        manager_agent,
                        actual_prompt,
                    )

                appointments = json.loads(
                    evaluation_file.read_text(encoding="utf-8")
                )

                return {
                    "output": result.final_output,
                    "metadata": {
                        "tool_calls": calls,
                        "appointments": appointments,
                        "expected_date": tomorrow,
                        "weather_scenario": scenario or "live",
                    },
                }
        finally:
            calendar_service.APPOINTMENTS_FILE = original_file
            tool_log.reset(token)