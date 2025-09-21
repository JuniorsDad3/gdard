import requests
from flask import current_app
from datetime import datetime

class IoTManager:
    @staticmethod
    def get_sensor_data(farm_id):
        url = f"https://api.smartagriculture.io/v1/sensors?farm_id={farm_id}&api_key={current_app.config['IOT_API_KEY']}"
        try:
            response = requests.get(url)
            data = response.json()
            
            # Store in Excel
            excel_db = ExcelDatabase()
            df = pd.DataFrame(data['readings'])
            with pd.ExcelWriter(current_app.config['EXCEL_DB_PATH'], 
                              engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name='sensor_data', index=False)
            
            return data
        except Exception as e:
            current_app.logger.error(f"Error fetching sensor data: {e}")
            return None
    
    @staticmethod
    def analyze_soil_health(farm_id):
        # AI-powered soil analysis
        sensor_data = IoTManager.get_sensor_data(farm_id)
        # Implement ML model here (would use actual model in production)
        recommendations = {
            'fertility': 'Moderate',
            'recommended_crops': ['Maize', 'Beans', 'Sunflower'],
            'fertilizer': 'NPK 10-20-10',
            'water_requirements': 'Moderate irrigation needed'
        }
        return recommendations