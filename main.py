from datetime import datetime

import requests


def get_coordinates(city):
    try:
        params = {"name": city, "count": 1, "language": "ru", "format": "json"}
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search", params=params, timeout=5
        )
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            return (
                data["results"][0]["latitude"],
                data["results"][0]["longitude"],
                data["results"][0]["name"],
            )
        return None
    except requests.exceptions.Timeout:
        print("Превышено время ожидания")
        return None
    except requests.exceptions.RequestException:
        print("Ошибка запроса")
        return None


def get_weather(latitude, longitude):
    if latitude is None or longitude is None:
        print("Нет координат")
        return None
    try:
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
        }
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=weather_params,
            timeout=5,
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        if weather_data.get("current"):
            current = weather_data.get("current")
            weather_time = current.get("time")
            temperature = current.get("temperature_2m")
            weather_speed = current.get("wind_speed_10m")
            if temperature is None or weather_speed is None or weather_time is None:
                return None
            try:
                formatted_time = datetime.strptime(weather_time, "%Y-%m-%dT%H:%M")
                return (
                    temperature,
                    weather_speed,
                    formatted_time,
                )
            except ValueError:
                print("Некорректный формат времени")
                return None
        return None
    except requests.exceptions.Timeout:
        print("Превышено время ожидания")
        return None
    except requests.exceptions.RequestException:
        print("Ошибка запроса")
        return None


def main():
    city = input("Введите город: ").strip()
    if city:
        coordinates = get_coordinates(city)
        if coordinates:
            weather = get_weather(coordinates[0], coordinates[1])
            if weather:
                print(
                    f"\nГород: {coordinates[2]}",
                    f"Широта: {round(coordinates[0], 2)}",
                    f"Долгота: {round(coordinates[1], 2)}",
                    f"Температура: {round(weather[0], 1)}°C",
                    f"Скорость ветра: {weather[1]} км/ч",
                    f"Время обновления: {weather[2].strftime('%d.%m.%Y | %H:%M')}",
                    sep="\n",
                )
            else:
                print("Не удалось получить погоду")
        else:
            print("Город не найден")
    else:
        print("Введите название города")


if __name__ == "__main__":
    main()
