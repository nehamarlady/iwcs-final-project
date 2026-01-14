"""
Yelp Places Search Tool

This module implements the `search_places` tool for the MCP server.

Functionality:
• Converts a natural-language location (e.g., “Portland State University”)
  into geographic coordinates using the geocode_location tool.
• Sends the coordinates to the Yelp Business Search API.
• Returns a cleaned list of relevant business information, limited to 5 items.

This tool is consumed by the Smart City Info Agent to answer questions like:
  "Find coffee shops near PSU"
  "Search for restaurants near downtown Portland"
"""

import os
import requests
from tools.geocode import geocode_location

# Yelp Business Search API endpoint
YELP_URL = "https://api.yelp.com/v3/businesses/search"
YELP_API_KEY = os.environ.get("YELP_API_KEY")  # Key is injected via env vars


def search_places(data):
    """
    Search for nearby businesses using the Yelp API.

    Parameters
    
    data : dict
        Must contain:
            {
                "query": "coffee",
                "location": "Portland State University"
            }

    Returns
    
    dict
        On success:
            {
                "results": [
                    {
                        "name": "...",
                        "rating": 4.5,
                        "address": "...",
                        "phone": "...",
                        "url": "..."
                    },
                    ...
                ]
            }

        On failure:
            { "error": "message" }

    Notes
    
    • This function relies on geocode_location() to convert locations
      into coordinates suitable for Yelp's latitude/longitude parameters.
    • Yelp API requires authentication via a Bearer token.
    """

    # Validate input
    query = data.get("query")
    location = data.get("location")

    if not query or not location:
        return {"error": "Both 'query' and 'location' are required"}

    if not YELP_API_KEY:
        return {"error": "YELP_API_KEY not found in environment variables"}

    # Step 1: Convert location name → coordinates
    coords = geocode_location({"location": location})

    if "error" in coords:
        return coords

    lat = coords["lat"]
    lon = coords["lon"]

    # Step 2: Call Yelp Business Search API
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        "term": query,
        "latitude": lat,
        "longitude": lon,
        "limit": 5  # Keep output manageable for LLM consumption
    }

    try:
        response = requests.get(YELP_URL, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()

        # Clean Yelp response to include only useful fields
        cleaned = []
        for business in results.get("businesses", []):
            cleaned.append({
                "name": business["name"],
                "rating": business["rating"],
                "address": " ".join(business["location"]["display_address"]),
                "phone": business.get("display_phone"),
                "url": business["url"]
            })

        return {"results": cleaned}

    except Exception as e:
        return {"error": str(e)}
