module.exports = (output, context) => {
  const calls = context.providerResponse?.metadata?.tool_calls;

  const fail = (reason) => ({
    pass: false,
    score: 0,
    reason,
  });

  if (!Array.isArray(calls)) {
    return fail("No se recibió el registro de herramientas.");
  }

  const specialist = calls.find(
    (call) =>
      call.name === "faq_specialist" &&
      call.status === "returned"
  );

  if (!specialist) {
    return fail("El Manager no completó la llamada a faq_specialist.");
  }

  const searches = calls.filter(
    (call) =>
      call.name === "search_faq_tool" &&
      call.status === "returned"
  );

  if (searches.length === 0) {
    return fail("No se completó ninguna llamada a search_faq_tool.");
  }

  const question = context.vars.question.toLowerCase();

  let topic;
  if (question.includes("correo")) {
    topic = /correo|email|e-mail|contact|atenci[oó]n|soporte/i;
  } else if (question.includes("altura")) {
    topic = /altura|altitud|altitude|height/i;
  } else if (question.includes("velocidad")) {
    topic = /velocidad|ca[ií]da|speed|free.?fall/i;
  } else {
    return fail("Este validador todavía no define el tema de esta pregunta.");
  }

  const validSearch = searches.some((call) => {
    const query = call.arguments?.query;

    return (
      typeof query === "string" &&
      query.trim().length > 0 &&
      topic.test(query) &&
      String(call.result).includes("Pregunta:") &&
      String(call.result).includes("Respuesta:")
    );
  });

  if (!validSearch) {
    return fail(
      "La búsqueda no tiene un argumento relacionado con el tema o no devolvió FAQs."
    );
  }

  const bookingAttempt = calls.some(
    (call) =>
      call.name === "booking_specialist" ||
      call.name === "create_appointment_tool"
  );

  if (bookingAttempt) {
    return fail("Se intentó agendar durante una consulta de FAQs.");
  }

  return {
    pass: true,
    score: 1,
    reason:
      "Se ejecutaron faq_specialist y search_faq_tool con una consulta relacionada y resultados de FAQs, sin intentar reservar.",
  };
};