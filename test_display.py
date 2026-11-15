import unittest
from unittest.mock import patch

from display import get_weather_description, print_forecast


class TestGetWeatherDescription(unittest.TestCase):
    def test_invalid_code(self):
        self.assertEqual(get_weather_description(-1), "Неизвестная погода")
        self.assertEqual(get_weather_description(999), "Неизвестная погода")

    def test_weather_codes(self):
        test_cases = {
            0: "Ясно",
            1: "Преимущественно ясно",
            2: "Переменная облачность",
            3: "Пасмурно",
            45: "Туман",
            48: "Изморозь",
            51: "Лёгкая морось",
            53: "Умеренная морось",
            55: "Сильная морось",
            61: "Небольшой дождь",
            63: "Умеренный дождь",
            65: "Сильный дождь",
            71: "Небольшой снег",
            73: "Умеренный снег",
            75: "Сильный снег",
            80: "Небольшой ливень",
            81: "Умеренный ливень",
            82: "Сильный ливень",
            95: "Гроза",
            96: "Гроза с небольшим градом",
            99: "Гроза с сильным градом",
        }

        for code, expected in test_cases.items():
            with self.subTest(code=code):
                self.assertEqual(get_weather_description(code), expected)

    def test_invalid_type(self):
        invalid_codes = ["0", None, True, 1.5, [], {}]

        for code in invalid_codes:
            with self.subTest(code=code):
                self.assertEqual(
                    get_weather_description(code),
                    "Неизвестная погода",
                )


class TestPrintForecast(unittest.TestCase):
    def test_successful_forecast(self):
        forecast = {
            "time": ["2026-11-15", "2026-11-16"],
            "temperature_2m_min": [2.5, 4.0],
            "temperature_2m_max": [8.5, 10.0],
            "weather_code": [0, 61],
        }

        with patch("builtins.print") as mock_print:
            print_forecast(forecast)

        output = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)

        self.assertIn("Прогноз погоды на 7 дней", output)
        self.assertIn("2026-11-15: от 2.5°C до 8.5°C | Ясно", output)
        self.assertIn("2026-11-16: от 4.0°C до 10.0°C | Небольшой дождь", output)

        self.assertEqual(mock_print.call_count, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
