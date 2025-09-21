# app/weather.py
import os
import requests
from flask import current_app

def get_weather_data(location):
    API_KEY = current_app.config['WEATHER_API_KEY']
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': location,
        'units': 'metric',
        'appid': API_KEY
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        return {
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon']
        }
    except Exception as e:
        current_app.logger.error(f"Weather API Error: {str(e)}")
        return None