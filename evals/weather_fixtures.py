from contextlib import contextmanager

import centralized.main as app


@contextmanager
def controlled_weather(scenario):
    original = app.get_weather

    if scenario not in ("ideal", "rain"):
        raise ValueError(f"Escenario desconocido: {scenario}")

    def get_test_weather(target_date):
        return {
            "date": target_date.isoformat(),
            "temperature_2m": 25,
            "precipitation": 0 if scenario == "ideal" else 5,
            "cloud_cover": 10,
            "wind_speed_10m": 10,
            "wind_gust_10m": 15,
        }

    app.get_weather = get_test_weather

    try:
        yield
    finally:
        app.get_weather = original