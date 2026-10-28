
import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("Weather MCP Server")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


@mcp.tool()
def get_current_weather(city: str) -> dict:
    """Get the current weather for a city, including temperature,
    feels-like temperature, humidity, wind speed, and conditions."""

    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY is missing from .env"}

    try:
        response = requests.get(
            BASE_URL,
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            },
            timeout=15,
        )

        if response.status_code != 200:
            try:
                details = response.json().get("message", "Weather API request failed")
            except ValueError:
                details = "Weather API request failed"

            return {
                "error": details,
                "city": city,
                "status_code": response.status_code,
            }

        data = response.json()

        return {
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country"),
            "temperature_c": data.get("main", {}).get("temp"),
            "feels_like_c": data.get("main", {}).get("feels_like"),
            "humidity_percent": data.get("main", {}).get("humidity"),
            "wind_speed_mps": data.get("wind", {}).get("speed"),
            "conditions": [
                item.get("description")
                for item in data.get("weather", [])
            ],
        }

    except requests.RequestException as e:
        return {"error": f"Unable to retrieve weather: {e}"}




FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


@mcp.tool()
def get_forecast(city: str) -> dict:
    """Get the next five 3-hour weather forecast entries for a city."""

    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY is missing from .env"}

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=15,
        )

        if response.status_code != 200:
            try:
                details = response.json().get(
                    "message", "Forecast request failed"
                )
            except ValueError:
                details = "Forecast request failed"

            return {
                "error": details,
                "status_code": response.status_code,
                "city": city,
            }

        data = response.json()
        forecast = []

        # Return the first five forecast entries
        for item in data.get("list", [])[:5]:
            weather = item.get("weather", [{}])[0]

            forecast.append({
                "datetime": item.get("dt_txt"),
                "temperature_c": item.get("main", {}).get("temp"),
                "feels_like_c": item.get("main", {}).get("feels_like"),
                "humidity_percent": item.get("main", {}).get("humidity"),
                "conditions": weather.get("description"),
                "wind_speed_mps": item.get("wind", {}).get("speed"),
                "rain_probability": item.get("pop"),
            })

        return {
            "city": data.get("city", {}).get("name", city),
            "country": data.get("city", {}).get("country"),
            "forecast": forecast,
        }

    except requests.RequestException as e:
        return {"error": f"Unable to retrieve forecast: {e}"}





if __name__ == "__main__":
    mcp.run(transport="stdio")
