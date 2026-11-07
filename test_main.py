import unittest
from datetime import datetime
from unittest.mock import patch

from main import get_coordinates, get_weather, main, requests


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
        with (
            patch("main.requests.get") as mock_get,
            patch("builtins.print") as mock_print,
        ):
            mock_get.side_effect = requests.exceptions.Timeout
            result = get_weather(55.75, 37.62)
            self.assertIsNone(result)
            mock_get.assert_called_once()
            mock_print.assert_called_once_with("Превышено время ожидания")

    def test_request_error(self):
        with (
            patch("main.requests.get") as mock_get,
            patch("builtins.print") as mock_print,
        ):
            mock_response = mock_get.return_value
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
            result = get_weather(55.75, 37.62)
            self.assertIsNone(result)
            mock_get.assert_called_once()
            mock_print.assert_called_once_with("Ошибка запроса")

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
            result = get_weather(55.75, 37.62)
            self.assertIsNone(result)

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
            result = get_coordinates("Москва")
            self.assertIsNone(result)

    def test_request_error(self):
        with patch("main.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
            result = get_coordinates("Москва")
            self.assertIsNone(result)


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
        ):
            mock_input.return_value = "Москва"
            mock_coord.return_value = (55.7558, 37.6173, "Москва")
            mock_weather.return_value = (10.5, 15.2, datetime(2026, 11, 7, 12, 0))
            main()
            mock_coord.assert_called_once_with("Москва")
            mock_weather.assert_called_once_with(55.7558, 37.6173)
            mock_print.assert_called_once_with(
                "\nГород: Москва",
                "Широта: 55.76",
                "Долгота: 37.62",
                "Температура: 10.5°C",
                "Скорость ветра: 15.2 км/ч",
                "Время обновления: 07.11.2026 | 12:00",
                sep="\n",
            )

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
