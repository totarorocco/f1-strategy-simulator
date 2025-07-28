import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from utils.config import Config
from utils.helpers import cache_data, format_api_response

@dataclass
class SessionInfo:
    session_key: int
    session_name: str
    date_start: str
    date_end: str
    meeting_name: str
    location: str
    country_name: str
    circuit_short_name: str

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
    
    def get_available_sessions(self) -> List[SessionInfo]:
        """Get list of available F1 sessions from OpenF1 API"""
        
        try:
            # Get current and recent sessions
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Last 7 days
            
            url = f"{self.openf1_base_url}/sessions"
            params = {
                'date_start>=': start_date.strftime('%Y-%m-%d'),
                'date_end<=': end_date.strftime('%Y-%m-%d')
            }
            
            response = self._make_request(url, params)
            if not response:
                return []
            
            sessions = []
            for session_data in response:
                sessions.append(SessionInfo(
                    session_key=session_data.get('session_key'),
                    session_name=session_data.get('session_name', ''),
                    date_start=session_data.get('date_start', ''),
                    date_end=session_data.get('date_end', ''),
                    meeting_name=session_data.get('meeting_name', ''),
                    location=session_data.get('location', ''),
                    country_name=session_data.get('country_name', ''),
                    circuit_short_name=session_data.get('circuit_short_name', '')
                ))
            
            return sessions
            
        except Exception as e:
            print(f"Error fetching available sessions: {e}")
            return []
    
    def get_live_race_data(self, session_key: int) -> Dict[str, Any]:
        """Get comprehensive live race data for a specific session"""
        
        race_data = {
            'session_key': session_key,
            'current_lap': 0,
            'total_laps': 0,
            'positions': [],
            'pit_stops': [],
            'tire_data': {},
            'weather': {},
            'car_data': {},
            'session_status': 'unknown'
        }
        
        try:
            # Get session info
            session_info = self._get_session_info(session_key)
            if session_info:
                race_data.update(session_info)
            
            # Get live positions
            positions = self._get_live_positions(session_key)
            race_data['positions'] = positions
            
            # Get pit stop data
            pit_stops = self._get_pit_stops(session_key)
            race_data['pit_stops'] = pit_stops
            
            # Get tire stint data
            tire_data = self._get_tire_stints(session_key)
            race_data['tire_data'] = tire_data
            
            # Get weather data
            weather = self._get_weather_data(session_key)
            race_data['weather'] = weather
            
            # Get car telemetry data
            car_data = self._get_car_data(session_key)
            race_data['car_data'] = car_data
            
        except Exception as e:
            print(f"Error collecting live race data: {e}")
        
        return race_data
    
    def _get_session_info(self, session_key: int) -> Dict[str, Any]:
        """Get session information"""
        
        url = f"{self.openf1_base_url}/sessions"
        params = {'session_key': session_key}
        
        response = self._make_request(url, params)
        if response and len(response) > 0:
            session = response[0]
            return {
                'session_name': session.get('session_name', ''),
                'meeting_name': session.get('meeting_name', ''),
                'location': session.get('location', ''),
                'country_name': session.get('country_name', ''),
                'circuit_short_name': session.get('circuit_short_name', ''),
                'date_start': session.get('date_start', ''),
                'date_end': session.get('date_end', ''),
                'session_status': session.get('session_status', 'unknown')
            }
        return {}
    
    def _get_live_positions(self, session_key: int) -> List[Dict[str, Any]]:
        """Get current driver positions"""
        
        url = f"{self.openf1_base_url}/position"
        params = {'session_key': session_key}
        
        response = self._make_request(url, params)
        if not response:
            return []
        
        # Get the most recent positions
        latest_positions = {}
        for pos_data in response:
            driver_number = pos_data.get('driver_number')
            date = pos_data.get('date', '')
            
            if driver_number and (driver_number not in latest_positions or date > latest_positions[driver_number].get('date', '')):
                latest_positions[driver_number] = pos_data
        
        # Get driver information
        drivers_info = self._get_drivers_info(session_key)
        drivers_dict = {d.get('driver_number'): d for d in drivers_info}
        
        # Combine position and driver data
        positions = []
        for driver_number, pos_data in latest_positions.items():
            driver_info = drivers_dict.get(driver_number, {})
            
            positions.append({
                'position': pos_data.get('position', 0),
                'driver_number': driver_number,
                'driver_name': f"{driver_info.get('first_name', '')} {driver_info.get('last_name', '')}".strip(),
                'team': driver_info.get('team_name', ''),
                'gap': self._calculate_gap(pos_data, latest_positions),
                'tire_compound': 'unknown',  # Will be updated by tire data
                'tire_age': 0
            })
        
        # Sort by position
        positions.sort(key=lambda x: x['position'])
        return positions
    
    def _get_drivers_info(self, session_key: int) -> List[Dict[str, Any]]:
        """Get driver information for the session"""
        
        url = f"{self.openf1_base_url}/drivers"
        params = {'session_key': session_key}
        
        response = self._make_request(url, params)
        return response if response else []
    
    def _get_pit_stops(self, session_key: int) -> List[Dict[str, Any]]:
        """Get pit stop data"""
        
        url = f"{self.openf1_base_url}/pit"
        params = {'session_key': session_key}
        
        response = self._make_request(url, params)
        return response if response else []
    
    def _get_tire_stints(self, session_key: int) -> Dict[str, Any]:
        """Get tire stint data with enhanced processing"""
        
        url = f"{self.openf1_base_url}/stints"
        params = {'session_key': session_key}
        
        response = self._make_request(url, params)
        if not response:
            return {}
        
        # Process tire data by driver with enhanced information
        tire_data = {}
        for stint in response:
            driver_number = stint.get('driver_number')
            if driver_number:
                if driver_number not in tire_data:
                    tire_data[driver_number] = {
                        'stints': [],
                        'current_stint': None,
                        'total_pit_stops': 0
                    }
                
                stint_info = {
                    'compound': stint.get('compound', 'unknown').lower(),
                    'lap_start': stint.get('lap_start', 0),
                    'lap_end': stint.get('lap_end', 0),
                    'stint_number': stint.get('stint_number', 0),
                    'tyre_age_at_start': stint.get('tyre_age_at_start', 0),
                    'stint_length': 0,
                    'is_current': False
                }
                
                # Calculate stint length
                if stint_info['lap_end'] > 0:
                    stint_info['stint_length'] = stint_info['lap_end'] - stint_info['lap_start'] + 1
                
                tire_data[driver_number]['stints'].append(stint_info)
                tire_data[driver_number]['total_pit_stops'] = len(tire_data[driver_number]['stints']) - 1
        
        # Determine current stint for each driver
        for driver_number, data in tire_data.items():
            if data['stints']:
                # Current stint is typically the last one or one with no end lap
                current_stint = None
                for stint in data['stints']:
                    if stint['lap_end'] == 0 or stint['lap_end'] > stint['lap_start']:
                        current_stint = stint
                
                if current_stint:
                    current_stint['is_current'] = True
                    data['current_stint'] = current_stint
                else:
                    # If no current stint found, use the last one
                    data['stints'][-1]['is_current'] = True
                    data['current_stint'] = data['stints'][-1]
        
        return tire_data
    
    def _get_weather_data(self, session_key: int) -> Dict[str, Any]:
        """Get weather data for the session"""
        
        # Try to get weather from OpenF1 first
        url = f"{self.openf1_base_url}/weather"
        params = {'session_key': session_key}
        
        response = self._make_request(url, params)
        if response and len(response) > 0:
            latest_weather = max(response, key=lambda x: x.get('date', ''))
            return {
                'air_temperature': latest_weather.get('air_temperature'),
                'track_temperature': latest_weather.get('track_temperature'),
                'humidity': latest_weather.get('humidity'),
                'pressure': latest_weather.get('pressure'),
                'wind_direction': latest_weather.get('wind_direction'),
                'wind_speed': latest_weather.get('wind_speed'),
                'rainfall': latest_weather.get('rainfall', 0) > 0
            }
        
        return {}
    
    def _get_car_data(self, session_key: int) -> Dict[str, Any]:
        """Get car telemetry data"""
        
        url = f"{self.openf1_base_url}/car_data"
        params = {
            'session_key': session_key,
            'speed>=': 0  # Filter for meaningful data
        }
        
        response = self._make_request(url, params, limit=100)  # Limit for performance
        return response if response else []
    
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
    
    def _calculate_gap(self, driver_pos: Dict, all_positions: Dict) -> str:
        """Calculate gap to leader or car ahead"""
        
        position = driver_pos.get('position', 0)
        if position <= 1:
            return "Leader"
        
        # Find leader (position 1)
        leader_pos = None
        for pos_data in all_positions.values():
            if pos_data.get('position') == 1:
                leader_pos = pos_data
                break
        
        if not leader_pos:
            return "N/A"
        
        # Calculate gap (simplified - would need more sophisticated timing in real implementation)
        return f"+{position * 0.5:.1f}s"  # Placeholder calculation
    
    def clear_cache(self):
        """Clear the internal cache"""
        self._cache.clear()