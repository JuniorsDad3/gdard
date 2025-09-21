import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from flask import current_app

class PredictiveAnalytics:
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'yield_predictor.pkl')
    
    @staticmethod
    def train_yield_prediction_model():
        # In a real app, this would use historical farm data
        # This is a simplified version
        try:
            excel_db = ExcelDatabase()
            data = pd.read_excel(current_app.config['EXCEL_DB_PATH'], sheet_name='farms')
            
            # Simulate training data
            X = data[['size', 'irrigation', 'sensors_installed']]
            y = data['size'] * 100  # Simulated yield
            
            model = RandomForestRegressor(n_estimators=100)
            model.fit(X, y)
            
            # Save the model
            os.makedirs(os.path.dirname(PredictiveAnalytics.MODEL_PATH), exist_ok=True)
            joblib.dump(model, PredictiveAnalytics.MODEL_PATH)
            return True
        except Exception as e:
            current_app.logger.error(f"Error training model: {e}")
            return False
    
    @staticmethod
    def predict_yield(farm_id):
        try:
            excel_db = ExcelDatabase()
            farms = pd.read_excel(current_app.config['EXCEL_DB_PATH'], sheet_name='farms')
            farm = farms[farms['id'] == farm_id].iloc[0]
            
            if not os.path.exists(PredictiveAnalytics.MODEL_PATH):
                PredictiveAnalytics.train_yield_prediction_model()
            
            model = joblib.load(PredictiveAnalytics.MODEL_PATH)
            features = [[farm['size'], farm['irrigation'], farm['sensors_installed']]]
            prediction = model.predict(features)
            
            return {
                'predicted_yield': prediction[0],
                'confidence': 0.85,  # Would calculate actual confidence in real app
                'recommendations': PredictiveAnalytics._generate_recommendations(farm, prediction[0])
            }
        except Exception as e:
            current_app.logger.error(f"Prediction failed: {e}")
            return None
    
    @staticmethod
    def _generate_recommendations(farm, predicted_yield):
        # Generate AI-powered recommendations
        recs = []
        if predicted_yield < farm['size'] * 80:
            recs.append("Yield prediction below average. Recommend soil testing.")
        if farm['irrigation'] == 'none':
            recs.append("No irrigation detected. Installing irrigation could increase yield by 30-50%.")
        if farm['sensors_installed'] < 3:
            recs.append("More IoT sensors could provide better data for yield optimization.")
        return recs if recs else ["Current practices appear optimal. Maintain current operations."]