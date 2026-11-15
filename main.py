from datetime import datetime

import requests

from api import (
    InvalidAPIResponse,
    get_coordinates,
    get_forecast,
    get_weather,
)
from cache import get_cached_data, load_cache, update_cache
from display import print_forecast


def main():
    city = input("Введите город: ").strip()

    if not city:
        print("Введите название города")
        return

    cache = load_cache()

    try:
        cached_data = get_cached_data(cache, city.lower())

        if cached_data:
            coordinates = cached_data["coordinates"]
            weather = cached_data["weather"]
            forecast = cached_data["forecast"]
            weather = (
                weather[0],
                weather[1],
                datetime.fromisoformat(weather[2]),
            )

        else:
            coordinates = get_coordinates(city)
            if not coordinates:
                print("Город не найден")
                return

            weather = get_weather(coordinates[0], coordinates[1])
            if not weather:
                print("Не удалось получить погоду")
                return

            try:
                forecast = get_forecast(coordinates[0], coordinates[1])
            except (InvalidAPIResponse, requests.RequestException):
                forecast = None

            if forecast:
                update_cache(cache, city.lower(), coordinates, weather, forecast)

        print(
            f"\nГород: {coordinates[2]}",
            f"Широта: {round(coordinates[0], 2)}",
            f"Долгота: {round(coordinates[1], 2)}",
            f"Температура: {round(weather[0], 1)}°C",
            f"Скорость ветра: {weather[1]} км/ч",
            f"Время обновления: {weather[2].strftime('%d.%m.%Y | %H:%M')}",
            sep="\n",
        )

        if forecast:
            print_forecast(forecast)
        else:
            print("Не удалось получить прогноз")

    except InvalidAPIResponse as error:
        print(f"Ошибка данных: {error}")
    except requests.exceptions.JSONDecodeError:
        print("Сервер вернул некорректный JSON")
    except requests.RequestException as error:
        print(f"Ошибка запроса: {error}")


if __name__ == "__main__":
    main()
