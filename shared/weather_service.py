from datetime import date
import requests

LATITUDE = 14.013722
LONGITUDE = -90.771611

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def get_weather(target_date: date) -> dict:
    """
    Obtiene el pronóstico meteorológico para a fecha indiada
    utilizando las coordenadas de Parachute S.A.
    """

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
        "daily": [
            "temperature_2m_max",
            "precipitation_sum",
            "cloud_cover_mean",
            "wind_speed_10m_max",
            "wind_gusts_10m_max"
        ],
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()
    daily = data["daily"]

    return {
        "date": daily["time"][0],
        "temperature_2m": daily["temperature_2m_max"][0],
        "precipitation": daily["precipitation_sum"][0],
        "cloud_cover": daily["cloud_cover_mean"][0],
        "wind_speed_10m": daily["wind_speed_10m_max"][0],
        "wind_gust_10m": daily["wind_gusts_10m_max"][0],
    }