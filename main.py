import requests

from api import (
    InvalidAPIResponse,
    get_coordinates,
    get_forecast,
    get_weather,
)
from display import print_forecast


def main():
    city = input("Введите город: ").strip()
    if city:
        try:
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
                    forecast = get_forecast(coordinates[0], coordinates[1])
                    if forecast:
                        print_forecast(forecast)
                    else:
                        print("Не удалось получить прогноз")
                else:
                    print("Не удалось получить погоду")
            else:
                print("Город не найден")
        except InvalidAPIResponse as error:
            print(f"Ошибка данных: {error}")
        except requests.exceptions.JSONDecodeError:
            print("Сервер вернул некорректный JSON")
        except requests.RequestException as error:
            print(f"Ошибка запроса: {error}")
    else:
        print("Введите название города")


if __name__ == "__main__":
    main()
