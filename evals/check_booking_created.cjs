module.exports = (output, context) => {
  const metadata = context.providerResponse?.metadata;
  const calls = metadata?.tool_calls;
  const appointments = metadata?.appointments;

  const fail = (reason) => ({
    pass: false,
    score: 0,
    reason,
  });

  if (!Array.isArray(calls) || !Array.isArray(appointments)) {
    return fail("Falta el registro de herramientas o de citas.");
  }

  const normalize = (value) =>
    String(value ?? "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();

  const expectedDate = metadata.expected_date;

  const weatherIndex = calls.findIndex(
    (call) =>
      call.name === "check_weather_tool" &&
      call.arguments?.target_date === expectedDate &&
      call.status === "returned" &&
      String(call.result).includes("Estado: IDEAL")
  );

  const createCalls = calls.filter(
    (call) => call.name === "create_appointment_tool"
  );

  if (weatherIndex < 0) {
    return fail("No se verificó clima IDEAL para la fecha solicitada.");
  }

  if (createCalls.length !== 1) {
    return fail("Se esperaba exactamente una llamada para crear la cita.");
  }

  const creation = createCalls[0];
  const args = creation.arguments;

  if (
    calls.indexOf(creation) <= weatherIndex ||
    creation.status !== "returned" ||
    args?.name !== "Cliente Prueba" ||
    args?.appointment_date !== expectedDate ||
    !/\btandem\b/.test(normalize(args?.jump_type)) ||
    !String(creation.result).includes("Cita creada correctamente")
  ) {
    return fail("La creación tiene argumentos, resultado u orden incorrectos.");
  }

  if (appointments.length !== 1) {
    return fail("El archivo debe contener exactamente una cita.");
  }

  const saved = appointments[0];

  if (
    saved.name !== args.name ||
    saved.date !== args.appointment_date ||
    saved.jump_type !== args.jump_type
  ) {
    return fail("La cita guardada no coincide con los argumentos utilizados.");
  }

  return {
    pass: true,
    score: 1,
    reason:
      "Se consultó el clima y se creó una única cita con los datos correctos."
  };
};