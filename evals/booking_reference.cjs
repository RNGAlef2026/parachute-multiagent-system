module.exports = (output, context) => {
  const metadata = context.providerResponse?.metadata;
  const date = metadata?.expected_date;
  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    throw new Error("Falta la fecha esperada de la evaluación.");
  }
  if (metadata.weather_scenario === "rain") {
    return (
      `En este caso, mañana corresponde a ${date}. ` +
      `No se creó una cita para Cliente Prueba para el ${date}. ` +
      "Las condiciones son inseguras para un salto tándem porque " +
      "se esperan 5 mm de precipitación y la regla prohíbe saltar " +
      "con precipitación mayor que 0 mm. Los demás datos del escenario " +
      "son temperatura de 25 °C, cobertura de nubes del 10 %, viento " +
      "de 10 km/h y ráfagas de 15 km/h."
    );
  }
  if (metadata.weather_scenario !== "ideal") {
    throw new Error("La referencia requiere el escenario ideal o rain.");
  }
  return (
    `En este caso, mañana corresponde a ${date}. ` +
    `Se creó una cita para Cliente Prueba para el ${date}, ` +
    "para un salto tándem, después de verificar condiciones " +
    "meteorológicas ideales: temperatura de 25 °C, " +
    "precipitación de 0 mm, cobertura de nubes del 10 %, " +
    "viento de 10 km/h y ráfagas de 15 km/h."
  );
};