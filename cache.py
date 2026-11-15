import json
import math
from datetime import datetime
from pathlib import Path

CACHE_FILE = Path(__file__).parent / "cache.json"


def is_valid_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data

            return {}
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(cache, file, indent=4, ensure_ascii=False)
    except OSError:
        return False

    return True


def get_cached_data(cache, city):
    if city not in cache:
        return None

    city_cache = cache[city]
    if not isinstance(city_cache, dict):
        return None

    saved_at = city_cache.get("saved_at")
    coordinates = city_cache.get("coordinates")
    weather = city_cache.get("weather")
    forecast = city_cache.get("forecast")
    forecast_keys = (
        "time",
        "temperature_2m_max",
        "temperature_2m_min",
        "weather_code",
    )

    if not saved_at:
        return None

    if not isinstance(coordinates, (list, tuple)) or len(coordinates) != 3:
        return None

    if not isinstance(weather, (list, tuple)) or len(weather) != 3:
        return None

    if not (
        is_valid_number(coordinates[0])
        and is_valid_number(coordinates[1])
        and isinstance(coordinates[2], str)
    ) or not (
        is_valid_number(weather[0])
        and is_valid_number(weather[1])
        and isinstance(weather[2], str)
    ):
        return None

    try:
        datetime.fromisoformat(weather[2])
    except ValueError:
        return None

    if not isinstance(forecast, dict):
        return None

    if not all(key in forecast for key in forecast_keys):
        return None

    for key in forecast_keys:
        if not isinstance(forecast[key], list):
            return None

    if len({len(forecast[key]) for key in forecast_keys}) != 1:
        return None

    if not forecast["time"]:
        return None

    for date in forecast["time"]:
        if not isinstance(date, str):
            return None

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return None

    for key in ("temperature_2m_max", "temperature_2m_min"):
        for temperature in forecast[key]:
            if not is_valid_number(temperature):
                return None

    for code in forecast["weather_code"]:
        if type(code) is not int:
            return None

    try:
        saved_time = datetime.fromisoformat(saved_at)
        sec = (datetime.now() - saved_time).total_seconds()
    except (ValueError, TypeError):
        return None

    if sec >= 600 or sec < 0:
        return None

    return city_cache


def update_cache(cache, city, coordinates, weather, forecast):
    cache[city] = {
        "saved_at": datetime.now().isoformat(),
        "coordinates": coordinates,
        "weather": (weather[0], weather[1], weather[2].isoformat()),
        "forecast": forecast,
    }
    return save_cache(cache)
