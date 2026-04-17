# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()
# API_KEY = os.getenv("OPENWEATHER_API_KEY")

# def get_weather_data(city="Mumbai"):
#     url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
#     response = requests.get(url)
#     if response.status_code == 200:
#         data = response.json()
#         return {
#             "temp": data['main']['temp'],
#             "humidity": data['main']['humidity'],
#             "rainfall": data.get('rain', {}).get('1h', 0)
#         }
#     return None

# def calculate_risk(weather):
#     if not weather:
#         return "Unavailable"
#     # Leaf Blight risk thresholds: Temp 20-28°C, Humidity > 80%
#     risk = 0
#     if 20 <= weather['temp'] <= 28:
#         risk += 40
#     if weather['humidity'] > 80:
#         risk += 40
#     if weather['rainfall'] > 5:
#         risk += 20
    
#     if risk >= 70:
#         return "High Risk - Immediate action needed"
#     elif risk >= 40:
#         return "Medium Risk - Prepare preventive measures"
#     else:
#         return "Low Risk - Normal monitoring"


import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_location():
    response = requests.get('https://ipinfo.io/json')
    data = response.json()
    return data.get('city', 'Mumbai')

def get_weather_data():
    city = get_location()
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "temp": data['main']['temp'],
            "humidity": data['main']['humidity'],
            "rainfall": data.get('rain', {}).get('1h', 0),
            "city": city
        }
    return None

def calculate_risk(weather):
    if not weather:
        return "Unavailable"
    risk = 0
    if 20 <= weather['temp'] <= 28:
        risk += 40
    if weather['humidity'] > 80:
        risk += 40
    if weather['rainfall'] > 5:
        risk += 20
    
    if risk >= 70:
        return "High Risk - Immediate action needed"
    elif risk >= 40:
        return "Medium Risk - Prepare preventive measures"
    else:
        return "Low Risk - Normal monitoring"