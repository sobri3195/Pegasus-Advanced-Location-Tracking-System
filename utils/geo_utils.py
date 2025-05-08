import math
import requests
from config.config import GEOCODING_API_KEY, WEATHER_API_KEY

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the Haversine distance between two points 
    specified by latitude/longitude in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def is_within_radius(lat1, lon1, lat2, lon2, radius_km):
    """Check if two points are within a certain radius of each other"""
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    return distance <= radius_km

def geocode_address(address):
    """Convert an address to latitude and longitude using a geocoding service"""
    if not GEOCODING_API_KEY:
        return None
    
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GEOCODING_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return {
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': data['results'][0]['formatted_address']
            }
    except Exception as e:
        print(f"Error geocoding address: {e}")
    
    return None

def reverse_geocode(latitude, longitude):
    """Convert latitude and longitude to an address"""
    if not GEOCODING_API_KEY:
        return None
    
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={GEOCODING_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            return data['results'][0]['formatted_address']
    except Exception as e:
        print(f"Error reverse geocoding: {e}")
    
    return None

def get_weather(latitude, longitude):
    """Get current weather conditions for a location"""
    if not WEATHER_API_KEY:
        return None
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon']
            }
    except Exception as e:
        print(f"Error getting weather: {e}")
    
    return None

def generate_directions_url(from_lat, from_lon, to_lat, to_lon, mode='driving'):
    """Generate a Google Maps directions URL"""
    return f"https://www.google.com/maps/dir/?api=1&origin={from_lat},{from_lon}&destination={to_lat},{to_lon}&travelmode={mode}" 