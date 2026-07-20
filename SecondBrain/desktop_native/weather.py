from __future__ import annotations

import json
import os
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlencode

WEATHER_CODES = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Fog",
    51: "Drizzle",
    53: "Drizzle",
    55: "Drizzle",
    61: "Rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Showers",
    81: "Showers",
    82: "Heavy showers",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm",
}


def weather_config(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = env if env is not None else os.environ
    try:
        latitude = float(values.get("SECONDBRAIN_WEATHER_LAT", ""))
        longitude = float(values.get("SECONDBRAIN_WEATHER_LON", ""))
    except (TypeError, ValueError):
        return {"configured": False}
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return {"configured": False}
    place = str(values.get("SECONDBRAIN_WEATHER_PLACE", "Configured location")).strip()
    return {
        "configured": True,
        "latitude": latitude,
        "longitude": longitude,
        "place": place[:60] or "Configured location",
    }


def fetch_weather(
    config: Mapping[str, Any],
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: float = 4.0,
) -> dict[str, Any]:
    if not config.get("configured"):
        return {"status": "not_configured", "place": "Weather"}
    params = {
        "latitude": config["latitude"],
        "longitude": config["longitude"],
        "current": "temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
        "timezone": "auto",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
    try:
        with opener(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        current = payload["current"]
        return {
            "status": "ready",
            "place": str(config.get("place", "Configured location"))[:60],
            "temperature": round(float(current["temperature_2m"])),
            "condition": WEATHER_CODES.get(int(current["weather_code"]), "Unknown"),
            "humidity": max(0, min(100, round(float(current["relative_humidity_2m"])))),
            "wind": max(0, round(float(current["wind_speed_10m"]))),
        }
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
        return {"status": "offline", "place": str(config.get("place", "Weather"))[:60]}


def weather_labels(snapshot: Mapping[str, Any]) -> dict[str, str]:
    status = snapshot.get("status")
    place = str(snapshot.get("place", "Weather"))[:60]
    if status == "not_configured":
        return {"place": place, "temperature": "Not configured", "detail": "Set weather coordinates"}
    if status != "ready":
        return {"place": place, "temperature": "Offline", "detail": "Weather unavailable"}
    return {
        "place": place,
        "temperature": f"{int(snapshot['temperature'])} deg",
        "detail": (
            f"{snapshot['condition']}\n"
            f"Humidity {int(snapshot['humidity'])}%\n"
            f"Wind {int(snapshot['wind'])} km/h"
        ),
    }
