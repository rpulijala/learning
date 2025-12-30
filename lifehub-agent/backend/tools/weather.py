"""Weather tool - fetches real weather data from Open-Meteo API (free, no API key required)."""

import httpx
from langchain_core.tools import tool

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Weather code descriptions from Open-Meteo
WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def _get_coordinates(city: str) -> tuple[float, float, str, str] | None:
    """Get latitude and longitude for a city using Open-Meteo geocoding."""
    # Try the full query first, then just the city name (before comma)
    queries_to_try = [city]
    if "," in city:
        queries_to_try.append(city.split(",")[0].strip())
    
    for query in queries_to_try:
        try:
            response = httpx.get(
                GEOCODING_URL,
                params={"name": query, "count": 5, "language": "en", "format": "json"},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                return (
                    result["latitude"],
                    result["longitude"],
                    result.get("name", city),
                    result.get("country", ""),
                )
        except Exception:
            continue
    
    return None


@tool
def get_weather(city: str) -> dict:
    """Get the current weather for a city.
    
    Args:
        city: The name of the city to get weather for.
        
    Returns:
        A dictionary with temperature, conditions, humidity, and other weather data.
    """
    # First, geocode the city
    coords = _get_coordinates(city)
    if not coords:
        return {"error": f"City '{city}' not found", "city": city}
    
    lat, lon, city_name, country = coords
    
    try:
        response = httpx.get(
            WEATHER_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "timezone": "auto",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        weather_code = current.get("weather_code", 0)
        
        return {
            "city": city_name,
            "country": country,
            "temp": f"{current.get('temperature_2m', 0):.0f}°F",
            "feels_like": f"{current.get('apparent_temperature', 0):.0f}°F",
            "humidity": f"{current.get('relative_humidity_2m', 0)}%",
            "conditions": WEATHER_CODES.get(weather_code, "unknown"),
            "wind_speed": f"{current.get('wind_speed_10m', 0):.1f} mph",
        }
    except httpx.HTTPStatusError as e:
        return {"error": f"API error: {e.response.status_code}", "city": city}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}", "city": city}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "city": city}
