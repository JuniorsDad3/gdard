import os
from dotenv import load_dotenv

load_dotenv()

class Config:
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