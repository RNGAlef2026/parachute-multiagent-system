from datetime import date

from shared.weather_service import get_weather


weather = get_weather(date.today())

print("Pronostico obtenido: ")
print(weather)