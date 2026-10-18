
"""Prueba controlada de una reservacion con clima IDEAL."""

from unittest.mock import patch

from mcp_server.server import create_appointment_tool


def test_booking_ideal():
    fecha = "2026-10-20"

    clima_simulado = {
        "date": fecha,
        "temperature_2m": 25,
        "precipitation": 0,
        "cloud_cover": 10,
        "wind_speed_10m": 5,
        "wind_gust_10m": 10,
    }

    cita_simulada = {
        "name": "Cliente de prueba",
        "date": fecha,
        "jump_type": "tandem",
    }

    with (
        patch(
            "mcp_server.server.validate_forecast_date",
            return_value={"valid": True},
        ),
        patch(
            "mcp_server.server.get_weather",
            return_value=clima_simulado,
        ),
        patch(
            "mcp_server.server.create_appointment",
            return_value=cita_simulada,
        ) as mock_create,
    ):
        resultado = create_appointment_tool(
        name="Cliente de prueba",
        appointment_date=fecha,
        jump_type="tandem",
    )

        mock_create.assert_called_once_with(
            name="Cliente de prueba",
            appointment_date=fecha,
            jump_type="tandem",
        )

        assert "Cita creada correctamente" in resultado

        print("\nPRUEBA EXITOSA")
        print(resultado)
        print("No se modifico appointments.json")


if __name__ == "__main__":
    test_booking_ideal()
