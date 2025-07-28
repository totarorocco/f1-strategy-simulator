import os
from typing import Dict, Any, List

class Config:
    """
    Configuration and constants for F1 Strategy Simulator.
    Handles API URLs, simulation parameters, and application settings.
    """
    
    # API Configuration
    OPENF1_BASE_URL = "https://api.openf1.org/v1"
    ERGAST_BASE_URL = "http://ergast.com/api/f1"
    WEATHER_BASE_URL = "https://api.open-meteo.com/v1"
    
    # Cache settings (in seconds)
    CACHE_DURATION = 30  # 30 seconds for live data
    HISTORICAL_CACHE_DURATION = 3600  # 1 hour for historical data
    
    # Simulation parameters
    DEFAULT_SIMULATIONS = 1000
    MAX_SIMULATIONS = 5000
    MIN_SIMULATIONS = 100
    
    # Strategy simulation settings
    MAX_PIT_STOPS = 4
    MIN_STINT_LENGTH = 3  # Minimum laps per stint
    PIT_STOP_TIME_LOSS = 25.0  # seconds
    PIT_STOP_VARIANCE = 2.0  # seconds variance
    
    # Tire model parameters
    TIRE_COMPOUNDS = {
        'soft': {
            'base_degradation': 0.08,
            'cliff_point': 15,
            'pace_delta': -0.8,
            'temp_sensitivity': 0.02
        },
        'medium': {
            'base_degradation': 0.05,
            'cliff_point': 25,
            'pace_delta': 0.0,
            'temp_sensitivity': 0.015
        },
        'hard': {
            'base_degradation': 0.03,
            'cliff_point': 35,
            'pace_delta': 0.6,
            'temp_sensitivity': 0.01
        },
        'intermediate': {
            'base_degradation': 0.06,
            'cliff_point': 20,
            'pace_delta': 1.5,
            'temp_sensitivity': 0.025
        },
        'wet': {
            'base_degradation': 0.07,
            'cliff_point': 18,
            'pace_delta': 2.0,
            'temp_sensitivity': 0.03
        }
    }
    
    # Track characteristics (default values)
    DEFAULT_TRACK_CHARACTERISTICS = {
        'abrasiveness': 1.0,
        'overtaking_difficulty': 1.0,
        'pit_stop_time_loss': 25.0,
        'typical_safety_car_laps': 5,
        'drs_zones': 2,
        'elevation_change': 50  # meters
    }
    
    # Weather parameters
    WEATHER_UPDATE_INTERVAL = 300  # 5 minutes
    RAIN_PROBABILITY_THRESHOLD = 0.3
    WET_TIRE_ADVANTAGE_IN_RAIN = 30.0  # seconds per lap
    
    # Safety car probabilities by track type
    SAFETY_CAR_PROBABILITIES = {
        'street': 0.25,  # Monaco, Singapore, Baku
        'permanent': 0.15,  # Silverstone, Spa, Monza
        'semi_permanent': 0.20,  # Austin, Mexico City
        'default': 0.15
    }
    
    # Fuel consumption rates (kg per lap by track type)
    FUEL_CONSUMPTION_RATES = {
        'high_speed': 3.2,  # Monza, Spa
        'medium_speed': 2.8,  # Silverstone, Barcelona
        'low_speed': 2.4,  # Monaco, Hungary
        'default': 2.8
    }
    
    # Circuit database
    CIRCUITS = {
        'bahrain': {
            'name': 'Bahrain International Circuit',
            'country': 'Bahrain',
            'laps': 57,
            'lap_length': 5.412,
            'type': 'permanent',
            'abrasiveness': 1.2,
            'fuel_consumption': 'medium_speed',
            'coordinates': [26.0325, 50.5106]
        },
        'jeddah': {
            'name': 'Jeddah Corniche Circuit',
            'country': 'Saudi Arabia',
            'laps': 50,
            'lap_length': 6.174,
            'type': 'street',
            'abrasiveness': 0.8,
            'fuel_consumption': 'high_speed',
            'coordinates': [21.6319, 39.1044]
        },
        'melbourne': {
            'name': 'Albert Park Circuit',
            'country': 'Australia',
            'laps': 58,
            'lap_length': 5.278,
            'type': 'semi_permanent',
            'abrasiveness': 1.0,
            'fuel_consumption': 'medium_speed',
            'coordinates': [-37.8497, 144.9681]
        },
        'imola': {
            'name': 'Autodromo Enzo e Dino Ferrari',
            'country': 'Italy',
            'laps': 63,
            'lap_length': 4.909,
            'type': 'permanent',
            'abrasiveness': 1.1,
            'fuel_consumption': 'medium_speed',
            'coordinates': [44.3439, 11.7167]
        },
        'miami': {
            'name': 'Miami International Autodrome',
            'country': 'United States',
            'laps': 57,
            'lap_length': 5.412,
            'type': 'street',
            'abrasiveness': 0.9,
            'fuel_consumption': 'medium_speed',
            'coordinates': [25.9581, -80.2389]
        },
        'monaco': {
            'name': 'Circuit de Monaco',
            'country': 'Monaco',
            'laps': 78,
            'lap_length': 3.337,
            'type': 'street',
            'abrasiveness': 0.7,
            'fuel_consumption': 'low_speed',
            'coordinates': [43.7347, 7.4206]
        },
        'spain': {
            'name': 'Circuit de Barcelona-Catalunya',
            'country': 'Spain',
            'laps': 66,
            'lap_length': 4.675,
            'type': 'permanent',
            'abrasiveness': 1.3,
            'fuel_consumption': 'medium_speed',
            'coordinates': [41.5700, 2.2611]
        },
        'canada': {
            'name': 'Circuit Gilles-Villeneuve',
            'country': 'Canada',
            'laps': 70,
            'lap_length': 4.361,
            'type': 'semi_permanent',
            'abrasiveness': 0.8,
            'fuel_consumption': 'high_speed',
            'coordinates': [45.5000, -73.5225]
        },
        'austria': {
            'name': 'Red Bull Ring',
            'country': 'Austria',
            'laps': 71,
            'lap_length': 4.318,
            'type': 'permanent',
            'abrasiveness': 1.0,
            'fuel_consumption': 'medium_speed',
            'coordinates': [47.2197, 14.7647]
        },
        'silverstone': {
            'name': 'Silverstone Circuit',
            'country': 'United Kingdom',
            'laps': 52,
            'lap_length': 5.891,
            'type': 'permanent',
            'abrasiveness': 1.2,
            'fuel_consumption': 'high_speed',
            'coordinates': [52.0786, -1.0169]
        },
        'hungary': {
            'name': 'Hungaroring',
            'country': 'Hungary',
            'laps': 70,
            'lap_length': 4.381,
            'type': 'permanent',
            'abrasiveness': 0.9,
            'fuel_consumption': 'low_speed',
            'coordinates': [47.5789, 19.2486]
        },
        'spa': {
            'name': 'Circuit de Spa-Francorchamps',
            'country': 'Belgium',
            'laps': 44,
            'lap_length': 7.004,
            'type': 'permanent',
            'abrasiveness': 1.1,
            'fuel_consumption': 'high_speed',
            'coordinates': [50.4372, 5.9714]
        },
        'zandvoort': {
            'name': 'Circuit Zandvoort',
            'country': 'Netherlands',
            'laps': 72,
            'lap_length': 4.259,
            'type': 'permanent',
            'abrasiveness': 1.0,
            'fuel_consumption': 'medium_speed',
            'coordinates': [52.3886, 4.5411]
        },
        'monza': {
            'name': 'Autodromo Nazionale di Monza',
            'country': 'Italy',
            'laps': 53,
            'lap_length': 5.793,
            'type': 'permanent',
            'abrasiveness': 0.8,
            'fuel_consumption': 'high_speed',
            'coordinates': [45.6156, 9.2811]
        },
        'singapore': {
            'name': 'Marina Bay Street Circuit',
            'country': 'Singapore',
            'laps': 61,
            'lap_length': 5.063,
            'type': 'street',
            'abrasiveness': 0.9,
            'fuel_consumption': 'low_speed',
            'coordinates': [1.2914, 103.8640]
        },
        'suzuka': {
            'name': 'Suzuka International Racing Course',
            'country': 'Japan',
            'laps': 53,
            'lap_length': 5.807,
            'type': 'permanent',
            'abrasiveness': 1.1,
            'fuel_consumption': 'medium_speed',
            'coordinates': [34.8431, 136.5408]
        },
        'qatar': {
            'name': 'Losail International Circuit',
            'country': 'Qatar',
            'laps': 57,
            'lap_length': 5.380,
            'type': 'permanent',
            'abrasiveness': 1.3,
            'fuel_consumption': 'medium_speed',
            'coordinates': [25.4900, 51.4542]
        },
        'austin': {
            'name': 'Circuit of the Americas',
            'country': 'United States',
            'laps': 56,
            'lap_length': 5.513,
            'type': 'permanent',
            'abrasiveness': 1.2,
            'fuel_consumption': 'medium_speed',
            'coordinates': [30.1328, -97.6411]
        },
        'mexico': {
            'name': 'Autodromo Hermanos Rodriguez',
            'country': 'Mexico',
            'laps': 71,
            'lap_length': 4.304,
            'type': 'permanent',
            'abrasiveness': 1.0,
            'fuel_consumption': 'medium_speed',
            'coordinates': [19.4042, -99.0907]
        },
        'interlagos': {
            'name': 'Autodromo Jose Carlos Pace',
            'country': 'Brazil',
            'laps': 71,
            'lap_length': 4.309,
            'type': 'permanent',
            'abrasiveness': 1.1,
            'fuel_consumption': 'medium_speed',
            'coordinates': [-23.7036, -46.6997]
        },
        'vegas': {
            'name': 'Las Vegas Strip Circuit',
            'country': 'United States',
            'laps': 50,
            'lap_length': 6.201,
            'type': 'street',
            'abrasiveness': 0.8,
            'fuel_consumption': 'high_speed',
            'coordinates': [36.1147, -115.1728]
        },
        'abu_dhabi': {
            'name': 'Yas Marina Circuit',
            'country': 'United Arab Emirates',
            'laps': 58,
            'lap_length': 5.281,
            'type': 'permanent',
            'abrasiveness': 1.0,
            'fuel_consumption': 'medium_speed',
            'coordinates': [24.4672, 54.6031]
        }
    }
    
    # UI Configuration
    REFRESH_INTERVALS = [5, 10, 15, 30, 60]  # seconds
    DEFAULT_REFRESH_INTERVAL = 10
    
    # Chart colors
    TIRE_COLORS = {
        'soft': '#FF0000',    # Red
        'medium': '#FFFF00',  # Yellow
        'hard': '#FFFFFF',    # White
        'intermediate': '#00FF00',  # Green
        'wet': '#0000FF'      # Blue
    }
    
    TEAM_COLORS = {
        'Red Bull Racing': '#1E3A8A',
        'Ferrari': '#DC2626',
        'Mercedes': '#00D2BE',
        'McLaren': '#F59E0B',
        'Aston Martin': '#059669',
        'Alpine': '#EC4899',
        'Williams': '#3B82F6',
        'AlphaTauri': '#6366F1',
        'Alfa Romeo': '#991B1B',
        'Haas': '#6B7280'
    }
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        'excellent': 0.0,      # seconds off optimal
        'good': 0.5,
        'average': 1.0,
        'poor': 2.0,
        'terrible': 3.0
    }
    
    # Risk assessment parameters
    RISK_FACTORS = {
        'tire_cliff': 2.0,      # Risk multiplier for being past tire cliff
        'weather_change': 1.5,  # Risk multiplier for weather uncertainty
        'safety_car': 1.2,      # Risk multiplier for safety car probability
        'overtaking': 1.3,      # Risk multiplier for difficult overtaking tracks
        'fuel_critical': 2.5    # Risk multiplier for running out of fuel
    }
    
    @classmethod
    def get_circuit_info(cls, circuit_key: str) -> Dict[str, Any]:
        """Get circuit information by key"""
        return cls.CIRCUITS.get(circuit_key, {})
    
    @classmethod
    def get_tire_compound_info(cls, compound: str) -> Dict[str, Any]:
        """Get tire compound parameters"""
        return cls.TIRE_COMPOUNDS.get(compound.lower(), cls.TIRE_COMPOUNDS['medium'])
    
    @classmethod
    def get_safety_car_probability(cls, circuit_type: str) -> float:
        """Get safety car probability for circuit type"""
        return cls.SAFETY_CAR_PROBABILITIES.get(circuit_type, cls.SAFETY_CAR_PROBABILITIES['default'])
    
    @classmethod
    def get_fuel_consumption_rate(cls, consumption_type: str) -> float:
        """Get fuel consumption rate by type"""
        return cls.FUEL_CONSUMPTION_RATES.get(consumption_type, cls.FUEL_CONSUMPTION_RATES['default'])
    
    @classmethod
    def validate_simulation_count(cls, count: int) -> int:
        """Validate and clamp simulation count to allowed range"""
        return max(cls.MIN_SIMULATIONS, min(cls.MAX_SIMULATIONS, count))
    
    @classmethod
    def get_environment_config(cls) -> Dict[str, Any]:
        """Get configuration from environment variables"""
        return {
            'debug_mode': os.getenv('F1_DEBUG', 'false').lower() == 'true',
            'cache_disabled': os.getenv('F1_DISABLE_CACHE', 'false').lower() == 'true',
            'api_timeout': int(os.getenv('F1_API_TIMEOUT', '10')),
            'max_workers': int(os.getenv('F1_MAX_WORKERS', '4')),
            'log_level': os.getenv('F1_LOG_LEVEL', 'INFO').upper()
        }
    
    @classmethod
    def get_all_circuit_names(cls) -> List[str]:
        """Get list of all available circuit names"""
        return [info['name'] for info in cls.CIRCUITS.values()]
    
    @classmethod
    def get_circuit_by_name(cls, name: str) -> Dict[str, Any]:
        """Get circuit info by full name"""
        for key, info in cls.CIRCUITS.items():
            if info['name'].lower() == name.lower():
                return {key: info}
        return {}