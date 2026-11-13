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
        "https://geocoding-api.open-meteo.com/v1/search",
        params=params,
        timeout=5,
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise InvalidAPIResponse("API вернул неправильную структуру данных")

    results = data.get("results")

    if results is not None and not isinstance(results, list):
        raise InvalidAPIResponse("API вернул неправильный формат списка городов")

    if results:
        result = data["results"][0]

        if not isinstance(result, dict):
            raise InvalidAPIResponse("API вернул неправильный формат данных о городе")

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

    if not isinstance(weather_data, dict):
        raise InvalidAPIResponse("API вернул неправильную структуру данных")

    current = weather_data.get("current")
    if not isinstance(current, dict):
        return None

    weather_time = current.get("time")
    temperature = current.get("temperature_2m")
    weather_speed = current.get("wind_speed_10m")

    if not isinstance(weather_time, str):
        return None
    if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
        return None
    if not isinstance(weather_speed, (int, float)) or isinstance(weather_speed, bool):
        return None
    if not math.isfinite(temperature) or not math.isfinite(weather_speed):
        return None

    try:
        formatted_time = datetime.strptime(weather_time, "%Y-%m-%dT%H:%M")
    except ValueError as error:
        raise InvalidAPIResponse("API вернул неправильный формат времени") from error

    return (
        temperature,
        weather_speed,
        formatted_time,
    )


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
        "https://api.open-meteo.com/v1/forecast",
        params=forecast_params,
        timeout=5,
    )
    forecast_response.raise_for_status()
    forecast_data = forecast_response.json()

    if not isinstance(forecast_data, dict):
        raise InvalidAPIResponse("API вернул неправильную структуру данных")

    daily = forecast_data.get("daily")

    if daily is None:
        return None

    if not isinstance(daily, dict):
        raise InvalidAPIResponse("API вернул неправильную структуру прогноза")

    required_fields = [
        "time",
        "temperature_2m_min",
        "temperature_2m_max",
        "weather_code",
    ]

    if not all(field in daily for field in required_fields):
        return None

    for field in required_fields:
        if daily[field] is None or daily[field] == []:
            return None

        if not isinstance(daily[field], list):
            raise InvalidAPIResponse(f"API вернул неправильный формат поля {field}")

    for field in ("temperature_2m_min", "temperature_2m_max"):
        for value in daily[field]:
            if type(value) not in (int, float) or not math.isfinite(value):
                raise InvalidAPIResponse(
                    f"API вернул неправильные значения поля {field}"
                )

    for code in daily["weather_code"]:
        if type(code) is not int:
            raise InvalidAPIResponse("API вернул неправильный код погоды")

    for date in daily["time"]:
        if not isinstance(date, str):
            raise InvalidAPIResponse("API вернул неправильный формат даты")

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError as error:
            raise InvalidAPIResponse("API вернул неправильную дату") from error

    lengths = [len(daily[field]) for field in required_fields]

    if len(set(lengths)) != 1:
        raise InvalidAPIResponse("API вернул массивы разной длины")

    for temp_min, temp_max in zip(
        daily["temperature_2m_min"],
        daily["temperature_2m_max"],
    ):
        if temp_min > temp_max:
            raise InvalidAPIResponse("Минимальная температура выше максимальной")

    return daily
