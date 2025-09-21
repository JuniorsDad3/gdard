import os
<<<<<<< HEAD
=======
from pathlib import Path
>>>>>>> ce58d1a7f94c377313b41c7b43df280d045bcbd2
from dotenv import load_dotenv

load_dotenv()

class Config:
<<<<<<< HEAD
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///gdard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'itradeafrika@gmail.com'
    MAIL_PASSWORD = 'xxwvccxuwxjvqfow'
    
    # Smart Tech Settings
    IOT_API_KEY = os.environ.get('IOT_API_KEY', 'default_iot_key')
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', 'default_weather_key')
    GIS_API_KEY = os.environ.get('GIS_API_KEY', 'default_gis_key')
    
    # Excel Database Path
    EXCEL_DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'agriculture_data.xlsx')
=======
    # Flask security key
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Path to Excel “database”
    EXCEL_DB_PATH = os.getenv("EXCEL_DB_PATH", "/data/GDARD.xlsx")

    # Optional API keys
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    SOCKETIO_SECRET = os.getenv("SOCKETIO_SECRET")

    # Email settings (Flask-Mail)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "itradeafrika@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "xxwvccxuwxjvqfow")
>>>>>>> ce58d1a7f94c377313b41c7b43df280d045bcbd2
