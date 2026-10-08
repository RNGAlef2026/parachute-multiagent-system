
import logging
from datetime import date

from mcp.server.fastmcp import FastMCP

from shared.weather_service import get_weather
from shared.safety_evaluator import evaluate_jump_safety
from shared.date_validator import validate_forecast_date
from shared.faq_service import search_faq

from shared.calendar_service import create_appointment


# Configuracion de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("parachute-mcp")

# Servidor MCP
mcp = FastMCP("Parachute MCP Server", host="127.0.0.1", port=8000)


@mcp.tool()
def check_weather_tool(target_date: str) -> str:
    """
    Consulta el clima para una fecha y evalua si las condiciones
    permiten realizar un salto en Parachute S.A.

    Args:
        target_date: Fecha solicitada en formato YYYY-MM-DD.
    """
    logger.info("Ejecutando check_weather_tool: %s", target_date)

    try:
        requested_date = date.fromisoformat(target_date)
    except ValueError:
        logger.warning("Fecha invalida: %s", target_date)
        return "La fecha debe utilizar el formato YYYY-MM-DD."

    validation = validate_forecast_date(requested_date)

    if not validation["valid"]:
        logger.warning("Fecha fuera del rango permitido: %s", target_date)
        return validation["message"]

    weather = get_weather(requested_date)
    evaluation = evaluate_jump_safety(weather)

    logger.info(
        "Evaluacion completada | Fecha: %s | Estado: %s",
        target_date,
        evaluation["status"],
    )

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


@mcp.tool()
def search_faq_tool(query: str) -> str:
    """
    Busca informacion en la base de conocimientos de FAQs
    de Parachute S.A.

    Args:
        query: Pregunta o consulta del usuario.
    """
    logger.info("Ejecutando search_faq_tool: %s", query)

    results = search_faq(query, limit=3)

    if not results:
        logger.info("No se encontraron resultados para la consulta.")
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

    logger.info(
        "Busqueda FAQ completada | Resultados: %s",
        len(results),
    )

    return "\n\n".join(formatted_results)


@mcp.tool()
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
    logger.info(
        "Ejecutando create_appointment_tool | Fecha: %s | Tipo: %s",
        appointment_date,
        jump_type,
    )

    try:
        requested_date = date.fromisoformat(appointment_date)
    except ValueError:
        logger.warning("Formato de fecha invalido")
        return "La fecha debe utilizar el formato YYYY-MM-DD."

    validation = validate_forecast_date(requested_date)

    if not validation["valid"]:
        logger.warning("Fecha no permitida: %s", appointment_date)
        return validation["message"]

    weather = get_weather(requested_date)
    evaluation = evaluate_jump_safety(weather)

    if evaluation["status"] == "UNSAFE":
        logger.warning("Cita rechazada por clima inseguro")
        return (
            "Cita rechazada. Las condiciones meteorologicas "
            "son NO SEGURAS / PROHIBIDAS para esa fecha. "
            f"Razones: {evaluation['reasons']}"
        )

    if evaluation["status"] == "MARGINAL":
        logger.warning("Cita no confirmada por condiciones marginales")
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

    logger.info(
        "Cita creada correctamente | Fecha: %s",
        appointment_date,
    )

    return (
        "Cita creada correctamente.\n"
        f"Nombre: {appointment['name']}\n"
        f"Fecha: {appointment['date']}\n"
        f"Tipo de salto: {appointment['jump_type']}"
    )


if __name__ == "__main__":
    logger.info("Iniciando servidor MCP de Parachute...")
    mcp.run(transport="streamable-http")
