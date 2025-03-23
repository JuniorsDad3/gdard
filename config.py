# config.py
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc://{user}:{password}@{server}/{database}"
        "?driver={driver}"
        "&Encrypt=yes"
        "&TrustServerCertificate=no"
    ).format(
        user=quote_plus(os.getenv("DB_USER")),
        password=quote_plus(os.getenv("DB_PASSWORD")),
        server=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),  # Corrected indentation
        driver=os.getenv("DB_DRIVER").replace(" ", "+"),
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Corrected indentation

    # Additional Configurations
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    SOCKETIO_SECRET = os.getenv('SOCKETIO_SECRET')
