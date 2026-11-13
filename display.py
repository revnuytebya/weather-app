def get_weather_description(code):
    if not isinstance(code, int) or isinstance(code, bool):
        return "Неизвестная погода"

    descriptions = {
        0: "Ясно",
        1: "Преимущественно ясно",
        2: "Переменная облачность",
        3: "Пасмурно",
        45: "Туман",
        48: "Изморозь",
        51: "Лёгкая морось",
        53: "Умеренная морось",
        55: "Сильная морось",
        61: "Небольшой дождь",
        63: "Умеренный дождь",
        65: "Сильный дождь",
        71: "Небольшой снег",
        73: "Умеренный снег",
        75: "Сильный снег",
        80: "Небольшой ливень",
        81: "Умеренный ливень",
        82: "Сильный ливень",
        95: "Гроза",
        96: "Гроза с небольшим градом",
        99: "Гроза с сильным градом",
    }

    return descriptions.get(code, "Неизвестная погода")


def print_forecast(forecast):
    print("\nПрогноз погоды на 7 дней:\n", "-" * 20)

    for date, temp_min, temp_max, wth_code in zip(
        forecast["time"],
        forecast["temperature_2m_min"],
        forecast["temperature_2m_max"],
        forecast["weather_code"],
    ):
        print(
            f"{date}: от {temp_min}°C до {temp_max}°C | "
            f"{get_weather_description(wth_code)}"
        )
