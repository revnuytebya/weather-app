import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from cache import (
    get_cached_data,
    load_cache,
    save_cache,
    update_cache,
)


class TestLoadCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_file = Path(self.temp_dir.name) / "cache.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_existing_cache(self):
        expected = {"москва": {"temperature": 10}}
        self.cache_file.write_text(
            json.dumps(expected),
            encoding="utf-8",
        )

        with patch("cache.CACHE_FILE", self.cache_file):
            result = load_cache()

        self.assertEqual(result, expected)

    def test_missing_file(self):
        with patch("cache.CACHE_FILE", self.cache_file):
            result = load_cache()

        self.assertEqual(result, {})

    def test_invalid_json(self):
        self.cache_file.write_text("{invalid json", encoding="utf-8")

        with patch("cache.CACHE_FILE", self.cache_file):
            result = load_cache()

        self.assertEqual(result, {})

    def test_invalid_json_structure(self):
        self.cache_file.write_text('["Москва"]', encoding="utf-8")

        with patch("cache.CACHE_FILE", self.cache_file):
            result = load_cache()

        self.assertEqual(result, {})

    def test_read_error(self):
        with (
            patch("cache.CACHE_FILE", self.cache_file),
            patch("builtins.open", side_effect=OSError("Ошибка чтения")),
        ):
            result = load_cache()

        self.assertEqual(result, {})

    def test_invalid_encoding(self):
        self.cache_file.write_bytes(b"\xff\xfe\xfa")

        with patch("cache.CACHE_FILE", self.cache_file):
            result = load_cache()

        self.assertEqual(result, {})


class TestSaveCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_file = Path(self.temp_dir.name) / "cache.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_cache(self):
        data = {"москва": {"temperature": 10}}

        with patch("cache.CACHE_FILE", self.cache_file):
            result = save_cache(data)

        self.assertTrue(result)

        content = self.cache_file.read_text(encoding="utf-8")

        self.assertIn("москва", content)
        self.assertEqual(json.loads(content), data)

    def test_save_cache_error(self):
        data = {"москва": {"temperature": 10}}

        with (
            patch("cache.CACHE_FILE", self.cache_file),
            patch("builtins.open", side_effect=OSError("Ошибка записи")),
        ):
            result = save_cache(data)

        self.assertFalse(result)


class TestGetCachedData(unittest.TestCase):
    def test_city_not_found(self):
        self.assertIsNone(get_cached_data({}, "москва"))

    def test_invalid_cache_entry(self):
        cache = {
            "москва": "invalid data",
        }

        self.assertIsNone(get_cached_data(cache, "москва"))

    def test_valid_cache(self):
        now = datetime.now()
        cache = {
            "москва": {
                "saved_at": now.isoformat(),
                "coordinates": [55.75, 37.62, "Москва"],
                "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                "forecast": {
                    "time": ["2026-11-15"],
                    "temperature_2m_max": [12.5],
                    "temperature_2m_min": [5.2],
                    "weather_code": [3],
                },
            }
        }

        result = get_cached_data(cache, "москва")

        self.assertEqual(result, cache["москва"])

    def test_expired_cache(self):
        saved_at = datetime.now() - timedelta(minutes=11)

        cache = {
            "москва": {
                "saved_at": saved_at.isoformat(),
                "coordinates": [55.75, 37.62, "Москва"],
                "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                "forecast": {
                    "time": ["2026-11-15"],
                    "temperature_2m_max": [12.5],
                    "temperature_2m_min": [5.2],
                    "weather_code": [3],
                },
            }
        }

        self.assertIsNone(get_cached_data(cache, "москва"))

    def test_future_cache(self):
        saved_at = datetime.now() + timedelta(minutes=5)

        cache = {
            "москва": {
                "saved_at": saved_at.isoformat(),
                "coordinates": [55.75, 37.62, "Москва"],
                "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                "forecast": {
                    "time": ["2026-11-15"],
                    "temperature_2m_max": [12.5],
                    "temperature_2m_min": [5.2],
                    "weather_code": [3],
                },
            }
        }

        self.assertIsNone(get_cached_data(cache, "москва"))

    def test_missing_fields(self):
        valid_data = {
            "saved_at": datetime.now().isoformat(),
            "coordinates": [55.75, 37.62, "Москва"],
            "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
            "forecast": {
                "time": ["2026-11-15"],
                "temperature_2m_max": [12.5],
                "temperature_2m_min": [5.2],
                "weather_code": [3],
            },
        }

        for field in valid_data:
            with self.subTest(field=field):
                cache = {"москва": valid_data.copy()}
                del cache["москва"][field]

                self.assertIsNone(get_cached_data(cache, "москва"))

    def test_invalid_data_structure(self):
        invalid_cases = [
            ("coordinates", [55.75, 37.62]),
            ("coordinates", "55.75, 37.62, Москва"),
            ("weather", [10.5, 15.2]),
            ("weather", "10.5, 15.2"),
            ("forecast", []),
        ]

        for field, value in invalid_cases:
            with self.subTest(field=field, value=value):
                cache = {
                    "москва": {
                        "saved_at": datetime.now().isoformat(),
                        "coordinates": [55.75, 37.62, "Москва"],
                        "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                        "forecast": {
                            "time": ["2026-11-15"],
                            "temperature_2m_max": [12.5],
                            "temperature_2m_min": [5.2],
                            "weather_code": [3],
                        },
                    }
                }

                cache["москва"][field] = value

                self.assertIsNone(get_cached_data(cache, "москва"))

    def test_invalid_value_types(self):
        invalid_cases = [
            ("coordinates", [55.75, "invalid", "Москва"]),
            ("coordinates", [55.75, 37.62, 123]),
            ("weather", ["invalid", 15.2, "2026-11-15T12:00:00"]),
            ("weather", [10.5, "invalid", "2026-11-15T12:00:00"]),
            ("weather", [10.5, 15.2, "invalid"]),
            ("coordinates", [True, 37.62, "Москва"]),
            ("coordinates", [55.75, math.nan, "Москва"]),
            ("weather", [math.inf, 15.2, "2026-11-15T12:00:00"]),
            ("weather", [10.5, -math.inf, "2026-11-15T12:00:00"]),
            ("weather", [False, 15.2, "2026-11-15T12:00:00"]),
        ]

        for field, value in invalid_cases:
            with self.subTest(field=field, value=value):
                cache = {
                    "москва": {
                        "saved_at": datetime.now().isoformat(),
                        "coordinates": [55.75, 37.62, "Москва"],
                        "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                        "forecast": {
                            "time": ["2026-11-15"],
                            "temperature_2m_max": [12.5],
                            "temperature_2m_min": [5.2],
                            "weather_code": [3],
                        },
                    }
                }

                cache["москва"][field] = value

                self.assertIsNone(get_cached_data(cache, "москва"))

    def test_invalid_forecast(self):
        invalid_cases = [
            {},
            {
                "time": [],
                "temperature_2m_max": [],
                "temperature_2m_min": [],
                "weather_code": [],
            },
            {
                "time": ["2026-11-15"],
                "temperature_2m_max": [12.5],
                "temperature_2m_min": [],
                "weather_code": [3],
            },
            {
                "time": ["2026-11-15"],
                "temperature_2m_max": "12.5",
                "temperature_2m_min": [5.2],
                "weather_code": [3],
            },
        ]

        for forecast in invalid_cases:
            with self.subTest(forecast=forecast):
                cache = {
                    "москва": {
                        "saved_at": datetime.now().isoformat(),
                        "coordinates": [55.75, 37.62, "Москва"],
                        "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                        "forecast": forecast,
                    }
                }

                self.assertIsNone(get_cached_data(cache, "москва"))

    def test_invalid_forecast_values(self):
        invalid_cases = [
            ("time", [123]),
            ("temperature_2m_max", ["invalid"]),
            ("temperature_2m_min", ["invalid"]),
            ("weather_code", ["invalid"]),
            ("weather_code", [3.5]),
            ("temperature_2m_max", [math.nan]),
            ("temperature_2m_min", [math.inf]),
            ("temperature_2m_max", [True]),
            ("time", ["какая-то дата"]),
            ("time", ["2026-13-45"]),
            ("time", ["15.11.2026"]),
            ("temperature_2m_min", [-math.inf]),
        ]

        for field, value in invalid_cases:
            with self.subTest(field=field, value=value):
                cache = {
                    "москва": {
                        "saved_at": datetime.now().isoformat(),
                        "coordinates": [55.75, 37.62, "Москва"],
                        "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                        "forecast": {
                            "time": ["2026-11-15"],
                            "temperature_2m_max": [12.5],
                            "temperature_2m_min": [5.2],
                            "weather_code": [3],
                        },
                    }
                }

                cache["москва"]["forecast"][field] = value

                self.assertIsNone(get_cached_data(cache, "москва"))

    def test_invalid_saved_at(self):
        invalid_values = [
            None,
            123,
            "invalid-date",
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                cache = {
                    "москва": {
                        "saved_at": value,
                        "coordinates": [55.75, 37.62, "Москва"],
                        "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                        "forecast": {
                            "time": ["2026-11-15"],
                            "temperature_2m_max": [12.5],
                            "temperature_2m_min": [5.2],
                            "weather_code": [3],
                        },
                    }
                }

                self.assertIsNone(get_cached_data(cache, "москва"))

    def test_missing_forecast_fields(self):
        forecast = {
            "time": ["2026-11-15"],
            "temperature_2m_max": [12.5],
            "temperature_2m_min": [5.2],
            "weather_code": [3],
        }

        for field in forecast:
            with self.subTest(field=field):
                cache = {
                    "москва": {
                        "saved_at": datetime.now().isoformat(),
                        "coordinates": [55.75, 37.62, "Москва"],
                        "weather": [10.5, 15.2, "2026-11-15T12:00:00"],
                        "forecast": forecast.copy(),
                    }
                }

                del cache["москва"]["forecast"][field]

                self.assertIsNone(get_cached_data(cache, "москва"))


class TestUpdateCache(unittest.TestCase):
    def test_update_cache(self):
        cache = {}
        coordinates = (55.75, 37.62, "Москва")
        weather = (10.5, 15.2, datetime(2026, 11, 15, 12, 0))
        forecast = {
            "time": ["2026-11-15"],
            "temperature_2m_max": [12.5],
            "temperature_2m_min": [5.2],
            "weather_code": [3],
        }

        with patch("cache.save_cache", return_value=True) as mock_save:
            result = update_cache(
                cache,
                "москва",
                coordinates,
                weather,
                forecast,
            )

        self.assertTrue(result)
        self.assertEqual(cache["москва"]["coordinates"], coordinates)
        self.assertEqual(
            cache["москва"]["weather"],
            (
                10.5,
                15.2,
                "2026-11-15T12:00:00",
            ),
        )
        self.assertEqual(cache["москва"]["forecast"], forecast)
        self.assertIn("saved_at", cache["москва"])
        datetime.fromisoformat(cache["москва"]["saved_at"])

        mock_save.assert_called_once_with(cache)

    def test_update_cache_save_error(self):
        cache = {}
        coordinates = (55.75, 37.62, "Москва")
        weather = (10.5, 15.2, datetime(2026, 11, 15, 12, 0))
        forecast = {
            "time": ["2026-11-15"],
            "temperature_2m_max": [12.5],
            "temperature_2m_min": [5.2],
            "weather_code": [3],
        }

        with patch("cache.save_cache", return_value=False):
            result = update_cache(
                cache,
                "москва",
                coordinates,
                weather,
                forecast,
            )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
