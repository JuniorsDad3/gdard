# ai/crop_predictor.py
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

class YieldPredictor:
    def __init__(self):
        self.model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(6,)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1)
        ])
        self.scaler = StandardScaler()
        
    def train(self, X_train, y_train):
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.compile(optimizer='adam', loss='mse')
        self.model.fit(X_scaled, y_train, epochs=50)
        
    def predict(self, soil_ph, rainfall, temp, crop_type, elevation, farm_size):
        inputs = [[soil_ph, rainfall, temp, crop_type, elevation, farm_size]]
        scaled_inputs = self.scaler.transform(inputs)
        return self.model.predict(scaled_inputs)[0][0]