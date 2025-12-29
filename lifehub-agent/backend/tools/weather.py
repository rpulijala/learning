"""Weather tool - returns dummy weather data."""

from langchain_core.tools import tool


@tool
def get_weather(city: str) -> dict:
    """Get the current weather for a city.
    
    Args:
        city: The name of the city to get weather for.
        
    Returns:
        A dictionary with temperature and conditions.
    """
    # Dummy implementation - returns static data for now
    return {
        "city": city,
        "temp": "72F",
        "conditions": "clear",
        "humidity": "45%",
    }
