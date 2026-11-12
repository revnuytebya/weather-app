import unittest
from datetime import datetime
from typing import cast
from unittest.mock import patch

from main import (
    InvalidAPIResponse,
    get_coordinates,
    get_forecast,
    get_weather,
    get_weather_description,
    is_valid_coordinates,
    main,
    requests,
)


class TestIsValidCoordinates(unittest.TestCase):
    def test_valid_coordinates(self):
        valid_coordinates = [
            (55.75, 37.62),
            (90, 180),
            (-90, -180),
            (0, 0),
        ]
        for latitude, longitude in valid_coordinates:
            with self.subTest(latitude=latitude, longitude=longitude):
                self.assertTrue(is_valid_coordinates(latitude, longitude))

    def test_invalid_coordinates(self):
        invalid_coordinates = [
            (None, 37.62),
            (55.75, None),
            ("abc", 37.62),
            (55.75, "abc"),
            (True, 37.62),
            (55.75, False),
            (91, 37.62),
            (-91, 37.62),
            (55.75, 181),
            (55.75, -181),
            (float("nan"), 37.62),
            (float("inf"), 37.62),
            (55.75, float("-inf")),
        ]
        for latitude, longitude in invalid_coordinates:
            with self.subTest(latitude=latitude, longitude=longitude):
                self.assertFalse(is_valid_coordinates(latitude, longitude))


class TestGetWeather(unittest.TestCase):
    def test_successful_response(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "current": {
                    "time": "2026-11-07T12:00",
                    "temperature_2m": 10.5,
                    "wind_speed_10m": 15.2,
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_weather(55.75, 37.62)
            result = cast(tuple, result)
            self.assertEqual(result[0], 10.5)
            self.assertEqual(result[1], 15.2)
            self.assertEqual(
                result[2].strftime("%Y-%m-%dT%H:%M"),
                "2026-11-07T12:00",
            )
            mock_get.assert_called_once_with(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": 55.75,
                    "longitude": 37.62,
                    "current": "temperature_2m,wind_speed_10m",
                },
                timeout=5,
            )

    def test_timeout(self):
        with patch("main.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout
            with self.assertRaises(requests.exceptions.Timeout):
                get_weather(55.75, 37.62)
            mock_get.assert_called_once()

    def test_request_error(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
            with self.assertRaises(requests.exceptions.HTTPError):
                get_weather(55.75, 37.62)
            mock_get.assert_called_once()

    def test_missing_current_data(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {}
            result = get_weather(55.75, 37.62)
            self.assertIsNone(result)

    def test_invalid_time_format(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "current": {
                    "time": "неправильное-время",
                    "temperature_2m": 10.5,
                    "wind_speed_10m": 15.2,
                }
            }
            with self.assertRaises(ValueError):
                get_weather(55.75, 37.62)

    def test_missing_weather_fields(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {"current": {"time": "2026-11-07T12:00"}}
            mock_response.raise_for_status.return_value = None
            result = get_weather(55.75, 37.62)
            self.assertIsNone(result)

    def test_missing_fields(self):
        for field in ["temperature_2m", "wind_speed_10m"]:
            with self.subTest(field=field), patch("main.requests.get") as mock_get:
                mock_response = mock_get.return_value
                mock_response.json.return_value = {
                    "current": {
                        "time": "2026-11-07T12:00",
                        "temperature_2m": 10.5,
                        "wind_speed_10m": 15.2,
                    }
                }
                mock_response.json.return_value["current"][field] = None
                result = get_weather(55.75, 37.62)
                self.assertIsNone(result)

    def test_missing_coordinates(self):
        for latitude, longitude in [
            (None, 37.62),
            (55.75, None),
        ]:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                result = get_weather(latitude, longitude)
                self.assertIsNone(result)
                mock_get.assert_not_called()

    def test_invalid_coordinates(self):
        invalid_coordinates = [
            ("abc", 37.62),
            (55.75, "abc"),
            (True, 37.62),
            (55.75, False),
        ]
        for latitude, longitude in invalid_coordinates:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                result = get_weather(latitude, longitude)
                self.assertIsNone(result)
                mock_get.assert_not_called()

    def test_coordinates_out_of_range(self):
        invalid_coordinates = [
            (91, 37.62),
            (-91, 37.62),
            (55.75, 181),
            (55.75, -181),
        ]
        for latitude, longitude in invalid_coordinates:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                result = get_weather(latitude, longitude)
                self.assertIsNone(result)
                mock_get.assert_not_called()

    def test_non_finite_coordinates(self):
        invalid_coordinates = [
            (float("nan"), 37.62),
            (float("inf"), 37.62),
            (float("-inf"), 37.62),
            (55.75, float("inf")),
            (55.75, float("-inf")),
        ]
        for latitude, longitude in invalid_coordinates:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                result = get_weather(latitude, longitude)
                self.assertIsNone(result)
                mock_get.assert_not_called()


class TestGetCoordinates(unittest.TestCase):
    def test_successful_response(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "results": [
                    {
                        "name": "Москва",
                        "latitude": 55.7558,
                        "longitude": 37.6173,
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            result = get_coordinates("Москва")
            mock_get.assert_called_once_with(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": "Москва",
                    "count": 1,
                    "language": "ru",
                    "format": "json",
                },
                timeout=5,
            )
            self.assertEqual(result, (55.7558, 37.6173, "Москва"))

    def test_city_not_found(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {"results": []}
            mock_response.raise_for_status.return_value = None
            result = get_coordinates("НесуществующийГород")
            self.assertIsNone(result)
            mock_get.assert_called_once()

    def test_timeout(self):
        with patch("main.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout
            with self.assertRaises(requests.exceptions.Timeout):
                get_coordinates("Москва")

    def test_request_error(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
            with self.assertRaises(requests.exceptions.HTTPError):
                get_coordinates("Москва")

    def test_incomplete_api_response(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "results": [
                    {
                        "name": "Москва",
                        "latitude": 55.7558,
                        # longitude отсутствует
                    }
                ]
            }
            with self.assertRaises(InvalidAPIResponse):
                get_coordinates("Москва")

    def test_invalid_name_type(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "results": [{"name": 123, "latitude": 55.7558, "longitude": 37.6173}]
            }
            with self.assertRaises(InvalidAPIResponse):
                get_coordinates("Москва")

    def test_invalid_coordinates(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "results": [{"name": "Москва", "latitude": 999, "longitude": 37.6173}]
            }
            with self.assertRaises(InvalidAPIResponse):
                get_coordinates("Москва")


class TestMain(unittest.TestCase):
    def test_empty_city(self):
        with (
            patch("builtins.input") as mock_input,
            patch("main.get_coordinates") as mock_coord,
            patch("main.get_weather") as mock_weather,
            patch("builtins.print") as mock_print,
        ):
            mock_input.return_value = ""
            main()
            mock_weather.assert_not_called()
            mock_coord.assert_not_called()
            mock_print.assert_called_once_with("Введите название города")

    def test_city_not_found(self):
        with (
            patch("builtins.input") as mock_input,
            patch("main.get_coordinates") as mock_coord,
            patch("main.get_weather") as mock_weather,
            patch("builtins.print") as mock_print,
        ):
            mock_input.return_value = "НесуществующийГород"
            mock_coord.return_value = None
            main()
            mock_coord.assert_called_once_with("НесуществующийГород")
            mock_weather.assert_not_called()
            mock_print.assert_called_once_with("Город не найден")

    def test_successful_weather(self):
        with (
            patch("builtins.input") as mock_input,
            patch("main.get_coordinates") as mock_coord,
            patch("main.get_weather") as mock_weather,
            patch("builtins.print") as mock_print,
            patch("main.get_forecast") as mock_forecast,
        ):
            mock_input.return_value = "Москва"
            mock_coord.return_value = (55.7558, 37.6173, "Москва")
            mock_weather.return_value = (10.5, 15.2, datetime(2026, 11, 7, 12, 0))
            mock_forecast.return_value = {
                "time": ["2026-11-08", "2026-11-09"],
                "temperature_2m_min": [0.4, 2.7],
                "temperature_2m_max": [3.8, 4.6],
                "weather_code": [61, 3],
            }
            main()
            mock_forecast.assert_called_once_with(55.7558, 37.6173)
            mock_coord.assert_called_once_with("Москва")
            mock_weather.assert_called_once_with(55.7558, 37.6173)
            mock_print.assert_any_call(
                "\nГород: Москва",
                "Широта: 55.76",
                "Долгота: 37.62",
                "Температура: 10.5°C",
                "Скорость ветра: 15.2 км/ч",
                "Время обновления: 07.11.2026 | 12:00",
                sep="\n",
            )
            mock_print.assert_any_call(
                "\nПрогноз погоды на 7 дней:\n",
                "-" * 20,
            )
            mock_print.assert_any_call("2026-11-08: от 0.4°C до 3.8°C | Дождь")
            mock_print.assert_any_call("2026-11-09: от 2.7°C до 4.6°C | Облачно")

    def test_weather_not_found(self):
        with (
            patch("builtins.input") as mock_input,
            patch("main.get_coordinates") as mock_coord,
            patch("main.get_weather") as mock_weather,
            patch("builtins.print") as mock_print,
        ):
            mock_input.return_value = "Москва"
            mock_coord.return_value = (55.7558, 37.6173, "Москва")
            mock_weather.return_value = None
            main()
            mock_weather.assert_called_once_with(55.7558, 37.6173)
            mock_print.assert_called_once_with("Не удалось получить погоду")

    def test_forecast_not_found(self):
        with (
            patch("builtins.input") as mock_input,
            patch("main.get_coordinates") as mock_coord,
            patch("main.get_weather") as mock_weather,
            patch("main.get_forecast") as mock_fc,
            patch("builtins.print") as mock_print,
        ):
            mock_input.return_value = "Москва"
            mock_coord.return_value = (55.7558, 37.6173, "Москва")
            mock_weather.return_value = (10.5, 15.2, datetime(2026, 11, 7, 12, 0))
            mock_fc.return_value = None
            main()
            mock_print.assert_any_call("Не удалось получить прогноз")


class TestGetForecast(unittest.TestCase):
    def test_successful_forecast(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-11-08", "2026-11-09"],
                    "temperature_2m_max": [12.5, 10.2],
                    "temperature_2m_min": [5.1, 3.8],
                    "weather_code": [3, 61],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertEqual(
                result,
                {
                    "time": ["2026-11-08", "2026-11-09"],
                    "temperature_2m_max": [12.5, 10.2],
                    "temperature_2m_min": [5.1, 3.8],
                    "weather_code": [3, 61],
                },
            )
            mock_get.assert_called_once_with(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": 55.75,
                    "longitude": 37.62,
                    "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                    "forecast_days": 7,
                },
                timeout=5,
            )

    def test_missing_daily(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {}
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_request_error(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
            with self.assertRaises(requests.exceptions.HTTPError):
                get_forecast(55.75, 37.62)

    def test_connection_error(self):
        with patch("main.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError
            with self.assertRaises(requests.exceptions.ConnectionError):
                get_forecast(55.75, 37.62)

    def test_invalid_json(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
                "Invalid JSON", "", 0
            )
            with self.assertRaises(requests.exceptions.JSONDecodeError):
                get_forecast(55.75, 37.62)

    def test_missing_required_fields(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {"daily": {"time": ["2026-11-08"]}}
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_different_array_lengths(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-11-08", "2026-11-09"],
                    "temperature_2m_min": [3, 4],
                    "temperature_2m_max": [8, 9],
                    "weather_code": [1],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_invalid_array_type(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": "2026-11-08",
                    "temperature_2m_min": [3],
                    "temperature_2m_max": [8],
                    "weather_code": [1],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_empty_arrays(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": [],
                    "temperature_2m_min": [],
                    "temperature_2m_max": [],
                    "weather_code": [],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_none_temperature(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-11-08"],
                    "temperature_2m_min": [None],
                    "temperature_2m_max": [10],
                    "weather_code": [3],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_invalid_temperature_type(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-11-08"],
                    "temperature_2m_min": ["ошибка"],
                    "temperature_2m_max": [10],
                    "weather_code": [3],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_invalid_weather_code_type(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-11-08"],
                    "temperature_2m_min": [5],
                    "temperature_2m_max": [10],
                    "weather_code": ["ошибка"],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_invalid_date_format(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["не дата"],
                    "temperature_2m_min": [5],
                    "temperature_2m_max": [10],
                    "weather_code": [3],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_invalid_calendar_date(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-02-30"],
                    "temperature_2m_min": [5],
                    "temperature_2m_max": [10],
                    "weather_code": [3],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_boolean_temperature(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-02-28"],
                    "temperature_2m_min": [True],
                    "temperature_2m_max": [10],
                    "weather_code": [3],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_boolean_weather_code(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-02-28"],
                    "temperature_2m_min": [3],
                    "temperature_2m_max": [10],
                    "weather_code": [True],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_float_weather_code(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-02-28"],
                    "temperature_2m_min": [3],
                    "temperature_2m_max": [10],
                    "weather_code": [3.5],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_min_temperature_greater_than_max(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.json.return_value = {
                "daily": {
                    "time": ["2026-02-28"],
                    "temperature_2m_min": [15],
                    "temperature_2m_max": [10],
                    "weather_code": [3],
                }
            }
            mock_response.raise_for_status.return_value = None
            result = get_forecast(55.75, 37.62)
            self.assertIsNone(result)

    def test_missing_coordinates(self):
        for latitude, longitude in [
            (None, 37.62),
            (55.75, None),
        ]:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                result = get_forecast(latitude, longitude)
                self.assertIsNone(result)
                mock_get.assert_not_called()

    def test_invalid_coordinates(self):
        for latitude, longitude in [
            ("abc", 37.62),
            (55.75, "abc"),
        ]:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                result = get_forecast(latitude, longitude)
                self.assertIsNone(result)
                mock_get.assert_not_called()

    def test_coordinates_out_of_range(self):
        for latitude, longitude in [
            (91, 181),
            (-91, -181),
        ]:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                result = get_forecast(latitude, longitude)
                self.assertIsNone(result)
                mock_get.assert_not_called()

    def test_coordinates_at_boundaries(self):
        mock_data = {
            "daily": {
                "time": ["2026-11-08"],
                "temperature_2m_min": [5.0],
                "temperature_2m_max": [12.0],
                "weather_code": [1],
            }
        }
        for latitude, longitude in [
            (90, 180),
            (-90, -180),
        ]:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                mock_get.return_value.json.return_value = mock_data
                result = get_forecast(latitude, longitude)
                self.assertEqual(result, mock_data["daily"])
                mock_get.assert_called_once()

    def test_non_finite_coordinates(self):
        invalid_coordinates = [
            (float("nan"), 37.62),
            (float("inf"), 37.62),
            (float("-inf"), 37.62),
            (55.75, float("inf")),
            (55.75, float("-inf")),
        ]
        for latitude, longitude in invalid_coordinates:
            with (
                self.subTest(latitude=latitude, longitude=longitude),
                patch("main.requests.get") as mock_get,
            ):
                result = get_forecast(latitude, longitude)
                self.assertIsNone(result)
                mock_get.assert_not_called()


class TestGetWeatherDescription(unittest.TestCase):
    def test_weather_codes(self):
        cases = [
            (0, "Ясно"),
            (1, "Облачно"),
            (45, "Туман"),
            (51, "Морось"),
            (56, "Ледяная морось"),
            (61, "Дождь"),
            (66, "Ледяной дождь"),
            (71, "Снег"),
            (77, "Снежные зёрна"),
            (80, "Ливень"),
            (85, "Снегопад"),
            (95, "Гроза"),
            (96, "Гроза с градом"),
            (999, "Неизвестная погода"),
        ]
        for code, expected in cases:
            with self.subTest(code=code):
                result = get_weather_description(code)
                self.assertEqual(result, expected)

    def test_invalid_code(self):
        invalid_codes = ["61", None, True, False]
        for x in invalid_codes:
            with self.subTest(x=x):
                result = get_weather_description(x)
                self.assertEqual(result, "Неизвестная погода")


if __name__ == "__main__":
    unittest.main(verbosity=2)
