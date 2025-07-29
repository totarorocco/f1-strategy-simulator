from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

@dataclass
class DriverInfo:
    driver_number: int
    driver_name: str
    team_name: str
    position: int
    gap_to_leader: str
    current_tire: str
    tire_age: int
    pit_stops: int = 0
    last_pit_lap: int = 0

@dataclass
class PitStop:
    driver_number: int
    lap: int
    pit_duration: float
    tire_compound_before: str
    tire_compound_after: str
    position_before: int
    position_after: int
    timestamp: str

@dataclass
class WeatherData:
    air_temperature: Optional[float] = None
    track_temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    rainfall: bool = False
    pressure: Optional[float] = None



class RaceState:
    """
    Maintains the current state of a live F1 race including positions, timing, weather, and historical data.
    Handles real-time updates and provides data validation.
    """
    
    def __init__(self):
        # Race session information
        self.current_lap: int = 0
        self.total_laps: int = 0
        self.race_start_time: Optional[datetime] = None
        
        # Driver data
        self.drivers: Dict[int, DriverInfo] = {}  # driver_number -> DriverInfo
        self.position_history: List[Dict[int, int]] = []  # List of lap -> {driver_number: position}
        
        # Pit stop data
        self.pit_stops: List[PitStop] = []
        self.tire_stints: Dict[int, List[Dict[str, Any]]] = {}  # driver_number -> list of stints
        
        # Weather and track conditions
        self.weather_data: WeatherData = WeatherData()
        self.weather_history: List[Tuple[int, WeatherData]] = []  # (lap, weather_data)
        
        # Timing data
        self.lap_times: Dict[int, List[float]] = {}  # driver_number -> list of lap times
        self.sector_times: Dict[int, List[Tuple[float, float, float]]] = {}  # driver_number -> list of (s1, s2, s3)
        
        # Race incidents and safety car
        self.safety_car_periods: List[Tuple[int, int]] = []  # List of (start_lap, end_lap)
        self.virtual_safety_car_periods: List[Tuple[int, int]] = []
        self.red_flag_periods: List[Tuple[int, int]] = []
        
        # Data validation flags
        self._last_update: Optional[datetime] = None
        self._data_quality: Dict[str, bool] = {
            "positions": False,
            "timing": False,
            "weather": False,
            "tire_data": False
        }
    
    def update(self, live_data: Dict[str, Any]) -> bool:
        """
        Update race state with new live data from data collector.
        
        Args:
            live_data: Dictionary containing latest race data
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        
        try:
            # Update race progress
            if 'current_lap' in live_data:
                self.current_lap = live_data['current_lap']
            if 'total_laps' in live_data:
                self.total_laps = live_data['total_laps']
            
            # Update driver positions
            if 'positions' in live_data and live_data['positions']:
                self._update_positions(live_data['positions'])
                self._data_quality["positions"] = True
            
            # Update pit stop data
            if 'pit_stops' in live_data and live_data['pit_stops']:
                self._update_pit_stops(live_data['pit_stops'])
            
            # Update tire data
            if 'tire_data' in live_data and live_data['tire_data']:
                self._update_tire_data(live_data['tire_data'])
                self._data_quality["tire_data"] = True
            
            # Update weather
            if 'weather' in live_data and live_data['weather']:
                self._update_weather(live_data['weather'])
                self._data_quality["weather"] = True
            
            # Update timing data
            if 'car_data' in live_data and live_data['car_data']:
                self._update_timing_data(live_data['car_data'])
                self._data_quality["timing"] = True
            
            self._last_update = datetime.now()
            return True
            
        except Exception as e:
            print(f"Error updating race state: {e}")
            return False
    

    
    def _update_positions(self, positions_data: List[Dict[str, Any]]) -> None:
        """Update driver positions and information"""
        
        current_positions = {}
        
        for pos_data in positions_data:
            driver_number = pos_data.get('driver_number')
            if not driver_number:
                continue
            
            # Update or create driver info
            if driver_number not in self.drivers:
                self.drivers[driver_number] = DriverInfo(
                    driver_number=driver_number,
                    driver_name=pos_data.get('driver_name', f'Driver {driver_number}'),
                    team_name=pos_data.get('team', 'Unknown Team'),
                    position=pos_data.get('position', 0),
                    gap_to_leader=pos_data.get('gap', 'N/A'),
                    current_tire=pos_data.get('tire_compound', 'unknown'),
                    tire_age=pos_data.get('tire_age', 0)
                )
            else:
                # Update existing driver info
                driver = self.drivers[driver_number]
                driver.position = pos_data.get('position', driver.position)
                driver.gap_to_leader = pos_data.get('gap', driver.gap_to_leader)
                driver.current_tire = pos_data.get('tire_compound', driver.current_tire)
                driver.tire_age = pos_data.get('tire_age', driver.tire_age)
            
            current_positions[driver_number] = pos_data.get('position', 0)
        
        # Store position history for analysis
        if current_positions and self.current_lap > 0:
            self.position_history.append(current_positions.copy())
    
    def _update_pit_stops(self, pit_data: List[Dict[str, Any]]) -> None:
        """Update pit stop information"""
        
        for pit_info in pit_data:
            driver_number = pit_info.get('driver_number')
            lap = pit_info.get('lap', 0)
            
            if not driver_number or lap <= 0:
                continue
            
            # Check if this pit stop already exists
            existing_stop = any(
                ps.driver_number == driver_number and ps.lap == lap 
                for ps in self.pit_stops
            )
            
            if not existing_stop:
                pit_stop = PitStop(
                    driver_number=driver_number,
                    lap=lap,
                    pit_duration=pit_info.get('pit_duration', 0.0),
                    tire_compound_before=pit_info.get('tire_compound_before', 'unknown'),
                    tire_compound_after=pit_info.get('tire_compound_after', 'unknown'),
                    position_before=pit_info.get('position_before', 0),
                    position_after=pit_info.get('position_after', 0),
                    timestamp=pit_info.get('timestamp', '')
                )
                
                self.pit_stops.append(pit_stop)
                
                # Update driver pit stop count
                if driver_number in self.drivers:
                    self.drivers[driver_number].pit_stops += 1
                    self.drivers[driver_number].last_pit_lap = lap
    
    def _update_tire_data(self, tire_data: Dict[str, Any]) -> None:
        """Update tire stint information"""
        
        for driver_number_str, stints in tire_data.items():
            try:
                driver_number = int(driver_number_str)
                self.tire_stints[driver_number] = stints
                
                # Update current tire info in driver data
                if driver_number in self.drivers and stints:
                    current_stint = stints[-1]  # Most recent stint
                    self.drivers[driver_number].current_tire = current_stint.get('compound', 'unknown')
                    
                    # Calculate tire age
                    stint_start = current_stint.get('lap_start', 0)
                    if stint_start > 0 and self.current_lap > 0:
                        self.drivers[driver_number].tire_age = max(0, self.current_lap - stint_start + 1)
                        
            except (ValueError, TypeError):
                continue
    
    def _update_weather(self, weather_data: Dict[str, Any]) -> None:
        """Update weather information"""
        
        self.weather_data = WeatherData(
            air_temperature=weather_data.get('air_temperature'),
            track_temperature=weather_data.get('track_temperature'),
            humidity=weather_data.get('humidity'),
            wind_speed=weather_data.get('wind_speed'),
            wind_direction=weather_data.get('wind_direction'),
            rainfall=weather_data.get('rainfall', False),
            pressure=weather_data.get('pressure')
        )
        
        # Store weather history
        if self.current_lap > 0:
            self.weather_history.append((self.current_lap, self.weather_data))
    
    def _update_timing_data(self, car_data: List[Dict[str, Any]]) -> None:
        """Update lap times and sector data"""
        
        # Process car data for timing information
        for data_point in car_data:
            driver_number = data_point.get('driver_number')
            if not driver_number:
                continue
            
            # Initialize timing data structures if needed
            if driver_number not in self.lap_times:
                self.lap_times[driver_number] = []
            if driver_number not in self.sector_times:
                self.sector_times[driver_number] = []
    
    def get_driver_by_position(self, position: int) -> Optional[DriverInfo]:
        """Get driver information by current position"""
        
        for driver in self.drivers.values():
            if driver.position == position:
                return driver
        return None
    
    def get_drivers_by_team(self, team_name: str) -> List[DriverInfo]:
        """Get all drivers from a specific team"""
        
        return [driver for driver in self.drivers.values() if driver.team_name == team_name]
    
    def get_position_changes(self, laps_back: int = 5) -> Dict[int, int]:
        """
        Calculate position changes over the last N laps.
        
        Args:
            laps_back: Number of laps to look back
            
        Returns:
            Dict mapping driver_number to position change (positive = gained positions)
        """
        
        if len(self.position_history) < 2:
            return {}
        
        current_positions = self.position_history[-1]
        compare_index = max(0, len(self.position_history) - laps_back - 1)
        past_positions = self.position_history[compare_index]
        
        position_changes = {}
        for driver_number in current_positions:
            if driver_number in past_positions:
                # Position change is negative because lower position number is better
                change = past_positions[driver_number] - current_positions[driver_number]
                position_changes[driver_number] = change
        
        return position_changes
    
    def get_recent_pit_stops(self, last_n_laps: int = 5) -> List[PitStop]:
        """Get pit stops from the last N laps"""
        
        cutoff_lap = max(0, self.current_lap - last_n_laps)
        return [ps for ps in self.pit_stops if ps.lap >= cutoff_lap]
    
    def is_safety_car_active(self) -> bool:
        """Check if safety car is currently active"""
        
        for start_lap, end_lap in self.safety_car_periods:
            if start_lap <= self.current_lap <= end_lap:
                return True
        return False
    
    def get_tire_age_for_driver(self, driver_number: int) -> int:
        """Get current tire age for a specific driver"""
        
        if driver_number in self.drivers:
            return self.drivers[driver_number].tire_age
        return 0
    
    def get_current_tire_for_driver(self, driver_number: int) -> str:
        """Get current tire compound for a specific driver"""
        
        if driver_number in self.drivers:
            return self.drivers[driver_number].current_tire
        return 'unknown'
    
    def is_valid(self) -> bool:
        """Check if race state has valid data for strategy simulation"""
        
        return (
            self.current_lap > 0 and
            self.total_laps > 0 and
            len(self.drivers) > 0 and
            any(self._data_quality.values())
        )
    
    def get_race_progress(self) -> float:
        """Get race progress as percentage (0.0 to 1.0)"""
        
        if self.total_laps <= 0:
            return 0.0
        return min(1.0, self.current_lap / self.total_laps)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current race state"""
        
        return {
            "session_name": self.session_info.session_name if self.session_info else "Unknown",
            "current_lap": self.current_lap,
            "total_laps": self.total_laps,
            "progress": f"{self.get_race_progress():.1%}",
            "drivers_count": len(self.drivers),
            "pit_stops_total": len(self.pit_stops),
            "weather": {
                "track_temp": self.weather_data.track_temperature,
                "air_temp": self.weather_data.air_temperature,
                "rainfall": self.weather_data.rainfall
            },
            "data_quality": self._data_quality,
            "last_update": self._last_update.isoformat() if self._last_update else None
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete race state as JSON-serializable dictionary"""
        
        return {
            "session_info": self.session_info.__dict__ if self.session_info else None,
            "race_progress": {
                "current_lap": self.current_lap,
                "total_laps": self.total_laps,
                "session_status": self.session_status
            },
            "drivers": {str(k): v.__dict__ for k, v in self.drivers.items()},
            "pit_stops": [ps.__dict__ for ps in self.pit_stops],
            "weather": self.weather_data.__dict__,
            "tire_stints": self.tire_stints,
            "data_quality": self._data_quality,
            "timestamp": datetime.now().isoformat()
        }