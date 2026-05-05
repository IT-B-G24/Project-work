import requests
import random
import time

url = "http://127.0.0.1:5000/predict"

while True:
    data = {
        "panel_voltage": round(random.uniform(45, 55), 2),
        "panel_current": round(random.uniform(3, 7), 2),
        "battery_voltage": round(random.uniform(45, 55), 2),
        "inverter_temp": round(random.uniform(25, 65), 2),
        "load_current": round(random.uniform(1, 6), 2)
    }

    try:
        response = requests.post(url, json=data)
        print("Sent:", data, "| Prediction:", response.json())
    except Exception as e:
        print("Error sending data:", e)

    time.sleep(2)