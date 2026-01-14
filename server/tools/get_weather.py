"""
get_weather.py

Provides the MCP tool for weather lookup using the OpenWeather API.

This module performs:
  1. Geocoding a location string into latitude/longitude using the
     shared geocode_location() tool.
  2. Calling the OpenWeather REST API to retrieve current weather
     conditions.
  3. Returning a clean, structured dictionary suitable for use
     by the LLM agent or front-end UI.

Environment Variables Required:
  OPENWEATHER_API_KEY  - Your OpenWeather API key (kept out of source)

This file will be part of the MCP server container deployed on Cloud Run.
"""

import os
import requests
from tools.geocode import geocode_location

# OpenWeather endpoint + API key (must be set in Cloud Run env vars)
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(data):
    """
    Retrieve current weather information for a given location.

    Args:
        data (dict):
            Expected format:
                {
                    "location": "Portland"
                }

    Returns:
        dict:
            {
                "location": "Portland",
                "temperature_c": 10.5,
                "weather": "broken clouds",
                "humidity": 93,
                "wind_speed": 2.5
            }

        OR an error dictionary:
            { "error": "message" }
    """
    # Validate and extract location
    location = data.get("location")
    if not location:
        return {"error": "Missing required field: 'location'"}

    # Step 1 — Convert text location to coordinates
    coords = geocode_location({"location": location})
    if "error" in coords:
        return coords  # Pass error upward

    lat, lon = coords["lat"], coords["lon"]

    # Step 2 — Query OpenWeather API
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(OPENWEATHER_URL, params=params)
        response.raise_for_status()
        w = response.json()

        # Extract key weather values
        return {
            "location": location,
            "temperature_c": w["main"]["temp"],
            "weather": w["weather"][0]["description"],
            "humidity": w["main"]["humidity"],
            "wind_speed": w["wind"]["speed"],
        }

    except Exception as e:
        # Any HTTP / JSON issue returns an error message
        return {"error": str(e)}
