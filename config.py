# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask security key
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Path to Excel “database”
EXCEL_DB_PATH = os.getenv("EXCEL_DB_PATH", "/data/GDARD.xlsx")

    # Optional API keys
    WEATHER_API_KEY   = os.getenv("WEATHER_API_KEY")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    SOCKETIO_SECRET   = os.getenv("SOCKETIO_SECRET")

    # Email settings (Flask-Mail)
    MAIL_SERVER   = os.getenv("MAIL_SERVER",   "smtp.gmail.com")
    MAIL_PORT     = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS  = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL  = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "itradeafrika@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "xxwvccxuwxjvqfow")
