import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from utils.config import Config
from utils.helpers import cache_data, format_api_response



class DataCollector:
    """
    Handles all API integrations for F1 data collection.
    Supports OpenF1 (real-time), Ergast (historical), and Open-Meteo (weather) APIs.
    """
    
    def __init__(self):
        self.openf1_base_url = Config.OPENF1_BASE_URL
        self.ergast_base_url = Config.ERGAST_BASE_URL
        self.weather_base_url = Config.WEATHER_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'F1-Strategy-Simulator/1.0'})
        
        # Cache settings
        self.cache_duration = Config.CACHE_DURATION
        self._cache = {}
    
    def get_historical_data(self, year: int, round_number: int = None) -> Dict[str, Any]:
        """Get historical race data from Ergast API"""
        
        try:
            if round_number:
                url = f"{self.ergast_base_url}/{year}/{round_number}/results.json"
            else:
                url = f"{self.ergast_base_url}/{year}/results.json"
            
            response = self._make_request(url)
            return response if response else {}
            
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return {}
    
    def get_track_weather_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get weather forecast for track location"""
        
        try:
            url = f"{self.weather_base_url}/forecast"
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'hourly': 'temperature_2m,precipitation,wind_speed_10m',
                'forecast_days': 1
            }
            
            response = self._make_request(url, params)
            return response if response else {}
            
        except Exception as e:
            print(f"Error fetching weather forecast: {e}")
            return {}
    
    def _make_request(self, url: str, params: Dict = None, limit: int = None) -> Any:
        """Make HTTP request with caching and error handling"""
        
        # Create cache key
        cache_key = f"{url}_{str(params)}_{limit}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        try:
            # Add limit to params if specified
            if limit and params:
                params['limit'] = limit
            elif limit:
                params = {'limit': limit}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            self._cache[cache_key] = (data, time.time())
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from {url}: {e}")
            return None
    

    
    def clear_cache(self):
        """Clear the internal cache"""
        self._cache.clear()