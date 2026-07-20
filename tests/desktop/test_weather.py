import json

from secondbrain.desktop_native.weather import fetch_weather, weather_config, weather_labels


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(
            {
                "current": {
                    "temperature_2m": 21.6,
                    "weather_code": 2,
                    "relative_humidity_2m": 57.2,
                    "wind_speed_10m": 12.7,
                }
            }
        ).encode()


def test_weather_config_requires_valid_coordinates() -> None:
    assert weather_config({}) == {"configured": False}
    assert weather_config({"SECONDBRAIN_WEATHER_LAT": "91", "SECONDBRAIN_WEATHER_LON": "8"}) == {
        "configured": False
    }
    assert weather_config(
        {
            "SECONDBRAIN_WEATHER_LAT": "49.0",
            "SECONDBRAIN_WEATHER_LON": "8.9",
            "SECONDBRAIN_WEATHER_PLACE": "Home",
        }
    ) == {"configured": True, "latitude": 49.0, "longitude": 8.9, "place": "Home"}


def test_weather_fetch_and_labels_are_bounded() -> None:
    config = {"configured": True, "latitude": 49.0, "longitude": 8.9, "place": "Home"}
    snapshot = fetch_weather(config, opener=lambda _url, timeout: Response())

    assert snapshot == {
        "status": "ready",
        "place": "Home",
        "temperature": 22,
        "condition": "Partly cloudy",
        "humidity": 57,
        "wind": 13,
    }
    assert weather_labels(snapshot) == {
        "place": "Home",
        "temperature": "22 deg",
        "detail": "Partly cloudy\nHumidity 57%\nWind 13 km/h",
    }


def test_weather_failure_does_not_expose_transport_details() -> None:
    def fail(_url, *, timeout):
        raise OSError(f"secret endpoint failed after {timeout}")

    result = fetch_weather(
        {"configured": True, "latitude": 49.0, "longitude": 8.9, "place": "Home"},
        opener=fail,
    )

    assert result == {"status": "offline", "place": "Home"}
    assert "secret" not in str(result)
    assert weather_labels(result)["temperature"] == "Offline"


def test_unconfigured_weather_skips_transport() -> None:
    result = fetch_weather({"configured": False}, opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()))

    assert result == {"status": "not_configured", "place": "Weather"}
    assert weather_labels(result)["temperature"] == "Not configured"
