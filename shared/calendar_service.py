import json
from pathlib import Path


APPOINTMENTS_FILE = Path("appointments.json")


def create_appointment(name: str, appointment_date: str, jump_type: str) -> dict:
    """
    Guarda una nueva cita localmente.
    """

    appointment = {
        "name": name,
        "date": appointment_date,
        "jump_type": jump_type,
    }

    if APPOINTMENTS_FILE.exists():
        with open(APPOINTMENTS_FILE, "r", encoding="utf-8") as file:
            appointments = json.load(file)
    else:
        appointments = []

    appointments.append(appointment)

    with open(APPOINTMENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(appointments, file, indent=4, ensure_ascii=False)

    return appointment