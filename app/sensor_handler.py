# iot/sensor_handler.py
import boto3
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

class SensorManager:
    def __init__(self):
        self.client = AWSIoTMQTTClient("GDARDClient")
        self.client.configureEndpoint("YOUR_ENDPOINT", 8883)
        self.client.configureCredentials("rootCA.pem", "private.key", "certificate.pem")
        
    def publish_reading(self, device_id, temp, moisture):
        payload = {
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "temperature": temp,
            "soil_moisture": moisture
        }
        self.client.publish("gard/sensor-data", json.dumps(payload), 1)