import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"


def _request_json(url, params):
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _weather_condition(code, is_day):
    conditions = {
        0: ("Clear sky", "☀️" if is_day else "🌙"),
        1: ("Mainly clear", "🌤️" if is_day else "🌙"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Foggy", "🌫️"),
        48: ("Foggy", "🌫️"),
        51: ("Light drizzle", "🌦️"),
        53: ("Drizzle", "🌧️"),
        55: ("Heavy drizzle", "🌧️"),
        56: ("Freezing drizzle", "🌧️"),
        57: ("Freezing drizzle", "🌧️"),
        61: ("Light rain", "🌦️"),
        63: ("Rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        66: ("Freezing rain", "🌧️"),
        67: ("Heavy freezing rain", "🌧️"),
        71: ("Light snow", "🌨️"),
        73: ("Snow", "❄️"),
        75: ("Heavy snow", "❄️"),
        77: ("Snow grains", "❄️"),
        80: ("Rain showers", "🌦️"),
        81: ("Rain showers", "🌧️"),
        82: ("Heavy rain showers", "🌧️"),
        85: ("Snow showers", "🌨️"),
        86: ("Heavy snow showers", "❄️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm with hail", "⛈️"),
        99: ("Thunderstorm with hail", "⛈️"),
    }
    return conditions.get(code, ("Unknown conditions", "🌡️"))


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/weather")
def weather():
    city = request.args.get("city", "").strip()

    if not city:
        return jsonify({"error": "Enter a city name to search."}), 400
    if len(city) > 100:
        return jsonify({"error": "City name must be 100 characters or fewer."}), 400

    try:
        geocoding = _request_json(
            GEOCODING_API_URL,
            {"name": city, "count": 1, "language": "en", "format": "json"},
        )
    except requests.RequestException:
        app.logger.exception("Could not reach the city search service.")
        return jsonify({"error": "Could not reach the weather service. Please try again."}), 502
    except ValueError:
        app.logger.exception("City search service returned invalid JSON.")
        return jsonify({"error": "Received an invalid response. Please try again."}), 502

    locations = geocoding.get("results", [])
    if not locations:
        return jsonify({"error": "City not found. Check the spelling and try again."}), 404

    location = locations[0]
    try:
        data = _request_json(
            WEATHER_API_URL,
            {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "is_day,weather_code,wind_speed_10m"
                ),
                "timezone": "auto",
                "wind_speed_unit": "kmh",
            },
        )
    except requests.RequestException:
        app.logger.exception("Could not reach Open-Meteo.")
        return jsonify({"error": "Weather data is temporarily unavailable. Please try again."}), 502
    except ValueError:
        app.logger.exception("Open-Meteo returned invalid JSON.")
        return jsonify({"error": "Received an invalid weather response. Please try again."}), 502

    try:
        current = data["current"]
        condition, icon = _weather_condition(
            int(current["weather_code"]),
            bool(current["is_day"]),
        )
        result = {
            "city": location["name"],
            "country": location.get("country", ""),
            "temperature": round(current["temperature_2m"]),
            "feels_like": round(current["apparent_temperature"]),
            "humidity": current["relative_humidity_2m"],
            "wind_speed": round(current["wind_speed_10m"], 1),
            "condition": condition,
            "icon": icon,
        }
    except (KeyError, IndexError, TypeError, ValueError):
        app.logger.exception("Open-Meteo response did not contain expected fields.")
        return jsonify({"error": "Received incomplete weather data. Please try again."}), 502

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
