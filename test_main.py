import unittest
from datetime import datetime
from unittest.mock import patch

import requests

from api import InvalidAPIResponse
from main import main


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
            mock_print.assert_any_call(
                "2026-11-08: от 0.4°C до 3.8°C | Небольшой дождь"
            )
            mock_print.assert_any_call("2026-11-09: от 2.7°C до 4.6°C | Пасмурно")

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

    def test_invalid_api_response(self):
        with (
            patch("builtins.input", return_value="Москва"),
            patch(
                "main.get_coordinates",
                side_effect=InvalidAPIResponse("Некорректные данные"),
            ),
            patch("builtins.print") as mock_print,
        ):
            main()
            mock_print.assert_called_once_with("Ошибка данных: Некорректные данные")

    def test_json_decode_error(self):
        with (
            patch("builtins.input", return_value="Москва"),
            patch(
                "main.get_coordinates",
                side_effect=requests.exceptions.JSONDecodeError("Invalid JSON", "", 0),
            ),
            patch("builtins.print") as mock_print,
        ):
            main()
            mock_print.assert_called_once_with("Сервер вернул некорректный JSON")

    def test_request_exception(self):
        with (
            patch("builtins.input", return_value="Москва"),
            patch(
                "main.get_coordinates",
                side_effect=requests.exceptions.ConnectionError("Нет соединения"),
            ),
            patch("builtins.print") as mock_print,
        ):
            main()
            mock_print.assert_called_once_with("Ошибка запроса: Нет соединения")

    def test_invalid_api_response_from_weather(self):
        with (
            patch("builtins.input", return_value="Москва"),
            patch(
                "main.get_coordinates",
                return_value=(55.75, 37.62, "Москва"),
            ),
            patch(
                "main.get_weather",
                side_effect=InvalidAPIResponse("Некорректное время"),
            ),
            patch("builtins.print") as mock_print,
        ):
            main()
            mock_print.assert_called_once_with("Ошибка данных: Некорректное время")


if __name__ == "__main__":
    unittest.main(verbosity=2)
