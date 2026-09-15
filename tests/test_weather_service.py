from datetime import date

from shared.weather_service import get_weather
from shared.safety_evaluator import evaluate_jump_safety

weather = get_weather(date.today())
evaluation = evaluate_jump_safety(weather)

print("Pronostico obtenido:")
print(weather)

print("\nEvaluacion de seguridad")
print(evaluation)