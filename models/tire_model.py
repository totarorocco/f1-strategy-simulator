import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class TireCompound(Enum):
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    INTERMEDIATE = "intermediate"
    WET = "wet"

@dataclass
class TirePerformance:
    compound: TireCompound
    age_laps: int
    degradation_rate: float
    estimated_pace_loss: float
    cliff_point: int
    optimal_window: Tuple[int, int]  # (start_lap, end_lap)
    grip_level: float

class TireModel:
    """
    Advanced tire degradation model considering compound, temperature, fuel load, and track characteristics.
    Based on the formula: lap_time_loss = base_degradation * tire_age * (1 + temp_factor * (track_temp - 30)) - fuel_burn_gain
    """
    
    def __init__(self):
        # Base degradation rates per compound (seconds per lap per tire age)
        self.base_degradation_rates = {
            TireCompound.SOFT: 0.08,     # Fastest but degrades quickly
            TireCompound.MEDIUM: 0.05,   # Balanced performance
            TireCompound.HARD: 0.03,     # Slowest but most durable
            TireCompound.INTERMEDIATE: 0.06,
            TireCompound.WET: 0.07
        }
        
        # Performance cliff points (lap count where performance drops significantly)
        self.cliff_points = {
            TireCompound.SOFT: 15,
            TireCompound.MEDIUM: 25,
            TireCompound.HARD: 35,
            TireCompound.INTERMEDIATE: 20,
            TireCompound.WET: 18
        }
        
        # Initial pace advantage/disadvantage vs medium compound
        self.base_pace_delta = {
            TireCompound.SOFT: -0.8,     # 0.8s faster per lap when fresh
            TireCompound.MEDIUM: 0.0,    # Baseline
            TireCompound.HARD: 0.6,      # 0.6s slower per lap when fresh
            TireCompound.INTERMEDIATE: 1.5,
            TireCompound.WET: 2.0
        }
        
        # Temperature sensitivity factors
        self.temp_sensitivity = {
            TireCompound.SOFT: 0.02,     # More sensitive to temperature
            TireCompound.MEDIUM: 0.015,
            TireCompound.HARD: 0.01,     # Less sensitive
            TireCompound.INTERMEDIATE: 0.025,
            TireCompound.WET: 0.03
        }
        
        # Fuel burn advantage (seconds gained per lap due to lighter car)
        self.fuel_burn_gain_per_lap = 0.035  # Approximately 3.5 kg fuel = 0.035s improvement
    
    def calculate_tire_performance(
        self,
        compound: TireCompound,
        age_laps: int,
        track_temp: float = 30.0,
        fuel_load: float = 100.0,
        track_abrasiveness: float = 1.0,
        is_wet: bool = False
    ) -> TirePerformance:
        """
        Calculate comprehensive tire performance metrics.
        
        Args:
            compound: Tire compound being used
            age_laps: Number of laps the tire has been used
            track_temp: Track temperature in Celsius
            fuel_load: Current fuel load as percentage (100% = full tank)
            track_abrasiveness: Track wear factor (1.0 = normal, >1.0 = more abrasive)
            is_wet: Whether track conditions are wet
            
        Returns:
            TirePerformance object with all calculated metrics
        """
        
        # Adjust compound for wet conditions
        if is_wet and compound in [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]:
            compound = TireCompound.INTERMEDIATE
        
        # Base degradation calculation
        base_degradation = self.base_degradation_rates[compound]
        
        # Temperature factor
        temp_factor = self.temp_sensitivity[compound] * (track_temp - 30)
        
        # Track abrasiveness factor
        abrasiveness_factor = track_abrasiveness
        
        # Fuel burn advantage (decreases over stint)
        fuel_advantage = self.fuel_burn_gain_per_lap * ((100 - fuel_load) / 100)
        
        # Calculate degradation with all factors
        degradation_per_lap = base_degradation * (1 + temp_factor) * abrasiveness_factor
        
        # Total degradation over tire life
        total_degradation = degradation_per_lap * age_laps
        
        # Apply cliff effect if past cliff point
        cliff_point = self.cliff_points[compound]
        if age_laps > cliff_point:
            cliff_penalty = (age_laps - cliff_point) * 0.1  # Exponential degradation
            total_degradation += cliff_penalty
        
        # Calculate final pace loss (base pace + degradation - fuel advantage)
        base_pace = self.base_pace_delta[compound]
        estimated_pace_loss = base_pace + total_degradation - fuel_advantage
        
        # Calculate grip level (0-1 scale)
        grip_level = max(0.1, 1.0 - (total_degradation / 3.0))  # Minimum 10% grip
        
        # Determine optimal usage window
        optimal_start = max(1, age_laps - 5)
        optimal_end = min(cliff_point, age_laps + 10)
        
        return TirePerformance(
            compound=compound,
            age_laps=age_laps,
            degradation_rate=degradation_per_lap,
            estimated_pace_loss=estimated_pace_loss,
            cliff_point=cliff_point,
            optimal_window=(optimal_start, optimal_end),
            grip_level=grip_level
        )
    
    def predict_stint_performance(
        self,
        compound: TireCompound,
        stint_length: int,
        starting_fuel: float = 100.0,
        track_temp: float = 30.0,
        track_abrasiveness: float = 1.0,
        is_wet: bool = False
    ) -> List[TirePerformance]:
        """
        Predict tire performance over an entire stint.
        
        Args:
            compound: Tire compound for the stint
            stint_length: Number of laps in the stint
            starting_fuel: Fuel load at start of stint (percentage)
            track_temp: Track temperature
            track_abrasiveness: Track wear factor
            is_wet: Wet conditions flag
            
        Returns:
            List of TirePerformance objects for each lap in the stint
        """
        
        performance_data = []
        
        for lap in range(1, stint_length + 1):
            # Calculate current fuel load (decreases linearly)
            current_fuel = starting_fuel * (1 - (lap - 1) / stint_length)
            
            performance = self.calculate_tire_performance(
                compound=compound,
                age_laps=lap,
                track_temp=track_temp,
                fuel_load=current_fuel,
                track_abrasiveness=track_abrasiveness,
                is_wet=is_wet
            )
            
            performance_data.append(performance)
        
        return performance_data
    
    def compare_compounds(
        self,
        age_laps: int,
        track_temp: float = 30.0,
        fuel_load: float = 100.0,
        track_abrasiveness: float = 1.0,
        is_wet: bool = False
    ) -> Dict[TireCompound, TirePerformance]:
        """
        Compare performance of all tire compounds at given conditions.
        
        Returns:
            Dictionary mapping each compound to its performance metrics
        """
        
        comparison = {}
        
        compounds_to_test = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]
        if is_wet:
            compounds_to_test = [TireCompound.INTERMEDIATE, TireCompound.WET]
        
        for compound in compounds_to_test:
            performance = self.calculate_tire_performance(
                compound=compound,
                age_laps=age_laps,
                track_temp=track_temp,
                fuel_load=fuel_load,
                track_abrasiveness=track_abrasiveness,
                is_wet=is_wet
            )
            comparison[compound] = performance
        
        return comparison
    
    def get_optimal_stint_length(
        self,
        compound: TireCompound,
        max_pace_loss: float = 2.0,
        track_temp: float = 30.0,
        track_abrasiveness: float = 1.0
    ) -> int:
        """
        Calculate optimal stint length before pace loss exceeds threshold.
        
        Args:
            compound: Tire compound to analyze
            max_pace_loss: Maximum acceptable pace loss in seconds
            track_temp: Track temperature
            track_abrasiveness: Track wear factor
            
        Returns:
            Optimal stint length in laps
        """
        
        for lap in range(1, 60):  # Test up to 60 laps
            performance = self.calculate_tire_performance(
                compound=compound,
                age_laps=lap,
                track_temp=track_temp,
                fuel_load=50.0,  # Mid-stint fuel load
                track_abrasiveness=track_abrasiveness
            )
            
            if performance.estimated_pace_loss > max_pace_loss:
                return max(1, lap - 1)
        
        return 60  # Maximum stint length
    
    def simulate_tire_strategy(
        self,
        strategy: List[Tuple[TireCompound, int]],  # List of (compound, stint_length)
        track_temp: float = 30.0,
        track_abrasiveness: float = 1.0,
        is_wet: bool = False
    ) -> Dict[str, float]:
        """
        Simulate a complete tire strategy and return performance metrics.
        
        Args:
            strategy: List of (compound, stint_length) tuples
            track_temp: Track temperature
            track_abrasiveness: Track wear factor
            is_wet: Wet conditions flag
            
        Returns:
            Dictionary with strategy performance metrics
        """
        
        total_time = 0.0
        total_laps = 0
        degradation_penalty = 0.0
        grip_scores = []
        
        for stint_num, (compound, stint_length) in enumerate(strategy):
            stint_performance = self.predict_stint_performance(
                compound=compound,
                stint_length=stint_length,
                starting_fuel=100.0 - (stint_num * 25),  # Fuel decreases each stint
                track_temp=track_temp,
                track_abrasiveness=track_abrasiveness,
                is_wet=is_wet
            )
            
            for lap_performance in stint_performance:
                total_time += lap_performance.estimated_pace_loss
                total_laps += 1
                grip_scores.append(lap_performance.grip_level)
                
                # Add degradation penalty for excessive wear
                if lap_performance.estimated_pace_loss > 2.0:
                    degradation_penalty += 0.5
        
        average_grip = np.mean(grip_scores) if grip_scores else 0.0
        
        return {
            'total_time_loss': total_time,
            'total_laps': total_laps,
            'average_pace_loss': total_time / max(1, total_laps),
            'degradation_penalty': degradation_penalty,
            'average_grip': average_grip,
            'strategy_risk': degradation_penalty + (2.0 - average_grip)
        }