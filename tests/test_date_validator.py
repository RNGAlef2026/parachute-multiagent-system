from datetime import date, timedelta

from shared.date_validator import validate_forecast_date


today = date.today()

test_dates = {
    "Hoy": today,
    "En 10 dias": today + timedelta(days=10),
    "Limite de 16 dias": today + timedelta(days=15),
    "Fuera del limite": today + timedelta(days=16),
    "Fecha pasada": today - timedelta(days=1),
}

for name, target_date in test_dates.items():
    result = validate_forecast_date(target_date)

    print(f"\n{name}: {target_date}")
    print(result)