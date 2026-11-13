import unittest

from display import get_weather_description


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
