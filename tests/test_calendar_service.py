from shared.calendar_service import create_appointment

appointment = create_appointment(
    name="Ale",
    appointment_date="2026-09-20",
    jump_type="tandem"
)

print("Cita creada correctamente:")
print(appointment)