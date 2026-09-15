from datetime import date, timedelta

FORECAST_DAYS = 16

def validate_forecast_date(target_date: date) -> dict:
    """
    Valida que la fecha solicitada se encuentre dentro
    del rango disponible de pronostico
    """

    today = date.today()
    max_date = today + timedelta(days=FORECAST_DAYS - 1)

    if target_date < today:
        return {
            "valid": False,
            "message": "No se puede calendarizar una cita en una fecha pasada."
        }

    if target_date > max_date:
        return {
            "valid": False,
            "message": (
                f"No se puede consultar el clima para {target_date}. "
                f"El pronostico solo esta disponible hasta {max_date}."
            ),
        }

    return {
        "valid": True,
        "message": "La fecha se encuentra dentro del rango de pronostico."
    }