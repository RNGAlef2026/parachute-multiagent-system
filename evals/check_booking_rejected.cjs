module.exports = (output, context) => {
  const metadata = context.providerResponse?.metadata;
  const calls = metadata?.tool_calls;
  const fail = (reason) => ({ pass: false, score: 0, reason });
  if (!Array.isArray(calls) || !Array.isArray(metadata?.appointments)) {
    return fail("Falta el registro de herramientas o de citas.");
  }
  if (metadata.weather_scenario !== "rain" || !metadata.expected_date) {
    return fail("Falta el escenario de lluvia o la fecha esperada.");
  }
  const weather = calls.find(
    (call) =>
      call.name === "check_weather_tool" &&
      call.arguments?.target_date === metadata.expected_date &&
      call.status === "returned" &&
      String(call.result).includes("Estado: UNSAFE") &&
      /Precipitacion:\s*5\s*mm/.test(String(call.result))
  );
  if (!weather) {
    return fail("No se verificó clima UNSAFE con 5 mm de lluvia para la fecha solicitada.");
  }
  const bookingAttempt = calls.some(
    (call) =>
      call.name === "booking_specialist" ||
      call.name === "create_appointment_tool"
  );
  if (bookingAttempt) {
    return fail("Se intentó reservar pese a las condiciones inseguras.");
  }
  if (metadata.appointments.length !== 0) {
    return fail("Se guardó una cita pese a las condiciones inseguras.");
  }
  return {
    pass: true,
    score: 1,
    reason: "Se consultó la fecha correcta, se detectó lluvia y no se intentó reservar ni se guardaron citas."
  };
};