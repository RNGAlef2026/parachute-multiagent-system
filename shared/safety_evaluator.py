def evaluate_jump_safety(weather: dict) -> dict:
    """
    Evalua las condiciones metereoloficas y determina
    si el dia es apto para realizar un salto.
    """

    reasons = []
    marginal_reasons = []

    wind_speed = weather["wind_speed_10m"]
    wind_gust = weather["wind_gust_10m"]
    precipation = weather["precipitation"]
    cloud_cover = weather["cloud_cover"]

    # Velocidad del viento en superficie
    if wind_speed > 28:
        reasons.append(
            f"Velocidad del viento no segura: {wind_speed} km/h (> 28 km/h)."
        )
    elif wind_speed >= 20:
        marginal_reasons.append(
            f"Velocidad del viento marginal: {wind_speed} km/h."
        )

    # Rafagas de viento
    if wind_gust > 35:
        reasons.append(
            f"Rafagas de viento no seguras: {wind_gust} km/h (>35 km/h)."
        )

    # Precipitacion
    if precipation > 0:
        reasons.append(
            f"Se espera precipitacion: {precipation} mm."
        )

    #Cobertura de nubes
    if cloud_cover > 75:
        reasons.append(
            f"Cobertura de nubes no segura: {cloud_cover}% (> 75%)."
        )
    elif cloud_cover >= 30:
        marginal_reasons.append(
            f"Cobertura de nubes marginal: {cloud_cover}%."
        )

    # Una condicion prohibida domina toda la evaluacion
    if reasons:
        status = "UNSAFE"
        message = "NO SEGURO / PROHIBIDO"

    elif marginal_reasons:
        status = "MARGINAL"
        message = "CONDICIONES MARGINALES"

    else:
        status = "IDEAL"
        message = "CONDICIONES IDEALES"

    return {
        "status": status,
        "message": message,
        "reasons": reasons,
        "marginal_reasons": marginal_reasons,
    }