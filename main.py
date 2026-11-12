import math
from datetime import datetime

import requests


class InvalidAPIResponse(Exception):
    pass


def is_valid_coordinates(latitude, longitude):
    if latitude is None or longitude is None:
        return False
    if type(latitude) not in (int, float) or type(longitude) not in (int, float):
        return False
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        return False
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def get_coordinates(city):
    params = {"name": city, "count": 1, "language": "ru", "format": "json"}
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search", params=params, timeout=5
    )
    response.raise_for_status()
    data = response.json()
    if data.get("results"):
        result = data["results"][0]
        if all(key in result for key in ("latitude", "longitude", "name")):
            if is_valid_coordinates(result["latitude"], result["longitude"]):
                if isinstance(result["name"], str) and result["name"].strip():
                    return result["latitude"], result["longitude"], result["name"]
                raise InvalidAPIResponse("API вернул неправильное название города")
            raise InvalidAPIResponse("API вернул неправильные данные")
        raise InvalidAPIResponse("API вернул неполные данные")
    return None


def get_weather(latitude, longitude):
    if not is_valid_coordinates(latitude, longitude):
        return None
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
        formatted_time = datetime.strptime(weather_time, "%Y-%m-%dT%H:%M")
        return (
            temperature,
            weather_speed,
            formatted_time,
        )
    return None


def get_forecast(latitude, longitude):
    if not is_valid_coordinates(latitude, longitude):
        return None
    forecast_params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "forecast_days": 7,
    }
    forecast_response = requests.get(
        "https://api.open-meteo.com/v1/forecast", params=forecast_params, timeout=5
    )
    forecast_response.raise_for_status()
    forecast_data = forecast_response.json()
    daily = forecast_data.get("daily")
    if not daily:
        return None
    required_fields = [
        "time",
        "temperature_2m_min",
        "temperature_2m_max",
        "weather_code",
    ]
    if not all(field in daily for field in required_fields):
        return None
    for field in required_fields:
        if not isinstance(daily[field], list) or not daily[field]:
            return None
    if any(type(value) not in (int, float) for value in daily["temperature_2m_min"]):
        return None
    if any(type(value) not in (int, float) for value in daily["temperature_2m_max"]):
        return None
    for temp_min, temp_max in zip(
        daily["temperature_2m_min"],
        daily["temperature_2m_max"],
    ):
        if temp_min > temp_max:
            return None
    if any(type(value) is not int for value in daily["weather_code"]):
        return None
    for date in daily["time"]:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return None
    lengths = []
    for field in required_fields:
        lengths.append(len(daily[field]))
    if len(set(lengths)) != 1:
        return None
    return daily


def get_weather_description(code):
    if not isinstance(code, int) or isinstance(code, bool):
        return "Неизвестная погода"
    if code == 0:
        return "Ясно"
    elif code in (1, 2, 3):
        return "Облачно"
    elif code in (45, 48):
        return "Туман"
    elif code in (51, 53, 55):
        return "Морось"
    elif code in (56, 57):
        return "Ледяная морось"
    elif code in (61, 63, 65):
        return "Дождь"
    elif code in (66, 67):
        return "Ледяной дождь"
    elif code in (71, 73, 75):
        return "Снег"
    elif code == 77:
        return "Снежные зёрна"
    elif code in (80, 81, 82):
        return "Ливень"
    elif code in (85, 86):
        return "Снегопад"
    elif code == 95:
        return "Гроза"
    elif code in (96, 99):
        return "Гроза с градом"
    else:
        return "Неизвестная погода"


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
                        print("\nПрогноз погоды на 7 дней:\n", "-" * 20)
                        for date, temp_min, temp_max, wth_code in zip(
                            forecast["time"],
                            forecast["temperature_2m_min"],
                            forecast["temperature_2m_max"],
                            forecast["weather_code"],
                        ):
                            print(
                                f"{date}: от {temp_min}°C до {temp_max}°C | {get_weather_description(wth_code)}"
                            )
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
        except ValueError:
            print("Сервер вернул некорректный формат времени")
    else:
        print("Введите название города")


if __name__ == "__main__":
    main()
