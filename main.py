import requests
from datetime import datetime

city = input("Введите город: ")
params = {"name": city, "count": 1, "language": "ru", "format": "json"}

try:
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search", params=params, timeout=5
    )

    response.raise_for_status()
    data = response.json()

    if data.get("results"):
        latitude = data["results"][0]["latitude"]
        longitude = data["results"][0]["longitude"]

        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
        }
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast", params=weather_params, timeout=5
        )

        weather_response.raise_for_status()
        weather_data = weather_response.json()

        temperature = weather_data["current"]["temperature_2m"]
        weather_time = weather_data["current"]["time"]
        wind_speed = weather_data["current"]["wind_speed_10m"]
        formatted_time = datetime.strptime(weather_time, "%Y-%m-%dT%H:%M")

        print(
            f"\nГород: {data['results'][0]['name']}",
            f"Широта: {round(latitude, 2)}",
            f"Долгота: {round(longitude, 2)}",
            f"Температура: {round(temperature, 1)}°C",
            f"Скорость ветра: {wind_speed} км/ч",
            f"Время обновления: {formatted_time.strftime('%d.%m.%Y | %H:%M')}",
            sep="\n",
        )

    else:
        print("Город не найден")
except requests.exceptions.Timeout:
    print("Превышено время ожидания")
except requests.exceptions.RequestException:
    print("Ошибка запроса")
