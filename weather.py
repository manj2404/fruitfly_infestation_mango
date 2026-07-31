"""
weather.py
==========
Fetches today's maximum/minimum temperature for a given GPS location.

Uses Open-Meteo (https://open-meteo.com) — a free weather API that
requires NO API key. This keeps the project simple for a student
deployment: no signup, no key management, no billing.

Also does a best-effort reverse geocode (coordinates -> place name)
using the free BigDataCloud client API, so the result page can show
"Coimbatore, Tamil Nadu" instead of raw latitude/longitude.
"""

import requests

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_API_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"

REQUEST_TIMEOUT = 8  # seconds


class WeatherError(Exception):
    """Raised when weather data cannot be retrieved or parsed."""
    pass


def get_temperature(latitude, longitude):
    """
    Fetch today's forecast maximum and minimum temperature (°C) for the
    given coordinates.

    Returns:
        dict: {
            "temp_max": float,
            "temp_min": float,
            "location_name": str,
        }

    Raises:
        WeatherError: if the API call fails or the response is malformed.
        This is caught in app.py, which then falls back to asking the
        farmer to enter temperatures manually.
    """
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        raise WeatherError("Invalid latitude/longitude values.")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
    }

    try:
        response = requests.get(WEATHER_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        temp_max = float(data["daily"]["temperature_2m_max"][0])
        temp_min = float(data["daily"]["temperature_2m_min"][0])

    except (requests.RequestException, KeyError, IndexError, ValueError, TypeError) as exc:
        raise WeatherError(f"Could not fetch weather data: {exc}")

    location_name = get_location_name(latitude, longitude)

    return {
        "temp_max": temp_max,
        "temp_min": temp_min,
        "location_name": location_name,
    }


def get_location_name(latitude, longitude):
    """
    Best-effort reverse geocode of coordinates to a human-readable place
    name (e.g. "Coimbatore, Tamil Nadu"). Never raises — falls back to
    plain coordinates if the lookup fails, since location naming is a
    "nice to have", not something that should block a prediction.
    """
    try:
        response = requests.get(
            GEOCODE_API_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "localityLanguage": "en",
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        city = data.get("city") or data.get("locality")
        region = data.get("principalSubdivision")

        if city and region:
            return f"{city}, {region}"
        if city:
            return city
        if region:
            return region

    except Exception:
        pass

    return f"{latitude:.2f}, {longitude:.2f}"