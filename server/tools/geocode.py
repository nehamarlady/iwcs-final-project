"""
Geocoding Tool

This module implements the `geocode_location` tool used by the MCP server.
It calls the Nominatim (OpenStreetMap) API to convert a place name into
its geographic coordinates.

The tool is consumed by the Smart City Info Agent, allowing the LLM to
resolve natural-language locations such as “Portland State University”
into latitude/longitude.
"""

import requests


def geocode_location(data):
    """
    Geocode a location string using the OpenStreetMap Nominatim API.

    Parameters
   
    data : dict or str
        Supported formats:
            {"location": "Portland"}
            "Portland"
        If a dictionary is provided, the function expects a "location" key.

    Returns
    
    dict
        A dictionary containing either:
            {
                "display_name": "...",
                "lat": "45.5118",
                "lon": "-122.6861"
            }

        Or an error:
            { "error": "Missing location" }
            { "error": "Location not found" }
            { "error": "Invalid JSON returned by geocoding API" }

    Notes
    
    • Nominatim requires a "User-Agent" header.
    • Only the first result is returned (limit=1) for clarity.
    """

    
    # Extract the location string (supports dict or raw string)
    
    if isinstance(data, dict):
        query = data.get("location")
    else:
        query = data

    if not query:
        return {"error": "Missing location"}

    
    # Build the Nominatim query URL
    url = (
        "https://nominatim.openstreetmap.org/search?"
        f"q={query}&format=json&limit=1"
    )

  
    # Send request to the geocoding API
   
    response = requests.get(url, headers={"User-Agent": "SmartCityAgent"})

    try:
        results = response.json()
    except Exception:
        return {"error": "Invalid JSON returned by geocoding API"}

   
    # Handle empty or missing results
  
    if not results:
        return {"error": "Location not found"}

    
    # Return formatted geocoding response
   
    result = results[0]
    return {
        "display_name": result.get("display_name"),
        "lat": result.get("lat"),
        "lon": result.get("lon"),
    }
