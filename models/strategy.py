import random
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.tire_model import TireModel, TireCompound, TirePerformance
from models.race_state import RaceState

@dataclass
class RaceStrategy:
    strategy_id: str
    num_stops: int
    stop_laps: List[int]
    tire_sequence: List[str]
    total_time: float
    risk_score: float
    weather_adjusted: bool
    confidence: float = 0.0
    expected_position: int = 0
    fuel_savings: float = 0.0
    safety_car_factor: float = 0.0

class StrategySimulator:
    """
    Monte Carlo strategy simulator that generates and evaluates race strategies.
    Considers tire degradation, pit stop time loss, traffic, weather, and safety car probability.
    """
    
    def __init__(self):
        self.tire_model = TireModel()
        
        # Strategy simulation parameters
        self.pit_stop_time_loss = 25.0  # seconds lost in pit stop
        self.pit_stop_variance = 2.0    # variance in pit stop times
        self.track_position_loss = 2    # positions lost during pit stop
        self.overtaking_difficulty = 1.5  # factor for overtaking time penalty
        
        # Safety car parameters
        self.safety_car_avg_duration = 5  # average laps under safety car
        self.safety_car_pit_advantage = 15.0  # seconds saved if pitting under SC
        
        # Weather parameters
        self.rain_probability_threshold = 0.3
        self.wet_tire_advantage_in_rain = 30.0  # seconds per lap advantage for correct tires
        
        # Track-specific parameters (will be loaded from track database)
        self.track_characteristics = {
            'abrasiveness': 1.0,
            'overtaking_difficulty': 1.0,
            'pit_stop_time_loss': 25.0,
            'typical_safety_car_laps': 5
        }
    
    def simulate_strategies(
        self,
        race_state: RaceState,
        num_simulations: int = 1000,
        consider_weather: bool = True,
        safety_car_prob: float = 0.15,
        max_stops: int = 3
    ) -> List[RaceStrategy]:
        """
        Run Monte Carlo simulation to find optimal race strategies.
        
        Args:
            race_state: Current state of the race
            num_simulations: Number of strategy combinations to test
            consider_weather: Whether to factor in weather predictions
            safety_car_prob: Probability of safety car per lap
            max_stops: Maximum number of pit stops to consider
            
        Returns:
            List of RaceStrategy objects sorted by total time
        """
        
        if not race_state.is_valid():
            return self._generate_demo_strategies()
        
        # Generate strategy combinations
        strategy_combinations = self._generate_strategy_combinations(
            current_lap=race_state.current_lap,
            total_laps=race_state.total_laps,
            max_stops=max_stops,
            num_simulations=num_simulations
        )
        
        # Simulate strategies in parallel for performance
        strategies = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_strategy = {
                executor.submit(
                    self._simulate_single_strategy,
                    strategy_combo,
                    race_state,
                    consider_weather,
                    safety_car_prob
                ): strategy_combo for strategy_combo in strategy_combinations
            }
            
            for future in as_completed(future_to_strategy):
                try:
                    strategy = future.result()
                    if strategy:
                        strategies.append(strategy)
                except Exception as e:
                    print(f"Strategy simulation error: {e}")
        
        # Sort by total time and return top strategies
        strategies.sort(key=lambda x: x.total_time)
        return strategies[:20]  # Return top 20 strategies
    
    def _generate_strategy_combinations(
        self,
        current_lap: int,
        total_laps: int,
        max_stops: int,
        num_simulations: int
    ) -> List[Dict[str, Any]]:
        """Generate diverse strategy combinations for simulation"""
        
        combinations = []
        remaining_laps = total_laps - current_lap
        
        # Available tire compounds
        compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]
        
        for num_stops in range(0, max_stops + 1):
            strategies_for_stops = min(num_simulations // (max_stops + 1), 100)
            
            for _ in range(strategies_for_stops):
                strategy = self._generate_random_strategy(
                    num_stops=num_stops,
                    current_lap=current_lap,
                    total_laps=total_laps,
                    compounds=compounds
                )
                combinations.append(strategy)
        
        # Ensure we have enough combinations
        while len(combinations) < num_simulations:
            strategy = self._generate_random_strategy(
                num_stops=random.randint(0, max_stops),
                current_lap=current_lap,
                total_laps=total_laps,
                compounds=compounds
            )
            combinations.append(strategy)
        
        return combinations[:num_simulations]
    
    def _generate_random_strategy(
        self,
        num_stops: int,
        current_lap: int,
        total_laps: int,
        compounds: List[TireCompound]
    ) -> Dict[str, Any]:
        """Generate a single random strategy"""
        
        remaining_laps = total_laps - current_lap
        
        # Generate random stop laps
        stop_laps = []
        if num_stops > 0:
            # Distribute stops across remaining laps with some randomness
            stop_positions = np.linspace(0.2, 0.8, num_stops)  # Between 20% and 80% of remaining race
            for pos in stop_positions:
                lap = current_lap + int(pos * remaining_laps) + random.randint(-3, 3)
                lap = max(current_lap + 1, min(total_laps - 1, lap))
                stop_laps.append(lap)
            
            stop_laps = sorted(list(set(stop_laps)))  # Remove duplicates and sort
        
        # Generate tire sequence
        tire_sequence = []
        for i in range(num_stops + 1):
            # Smart tire selection based on stint position
            if i == 0:  # First stint
                tire_sequence.append(random.choice([TireCompound.MEDIUM, TireCompound.HARD]))
            elif i == len(stop_laps):  # Final stint
                tire_sequence.append(random.choice([TireCompound.SOFT, TireCompound.MEDIUM]))
            else:  # Middle stints
                tire_sequence.append(random.choice(compounds))
        
        return {
            'num_stops': num_stops,
            'stop_laps': stop_laps,
            'tire_sequence': tire_sequence
        }
    
    def _simulate_single_strategy(
        self,
        strategy_combo: Dict[str, Any],
        race_state: RaceState,
        consider_weather: bool,
        safety_car_prob: float
    ) -> Optional[RaceStrategy]:
        """Simulate a single strategy and calculate its performance"""
        
        try:
            num_stops = strategy_combo['num_stops']
            stop_laps = strategy_combo['stop_laps']
            tire_sequence = strategy_combo['tire_sequence']
            
            # Calculate strategy performance
            total_time = 0.0
            risk_score = 0.0
            current_lap = race_state.current_lap
            total_laps = race_state.total_laps
            
            # Simulate each stint
            stint_start_lap = current_lap
            for stint_idx in range(len(tire_sequence)):
                compound = tire_sequence[stint_idx]
                
                # Determine stint end lap
                if stint_idx < len(stop_laps):
                    stint_end_lap = stop_laps[stint_idx]
                else:
                    stint_end_lap = total_laps
                
                stint_length = stint_end_lap - stint_start_lap
                if stint_length <= 0:
                    continue
                
                # Simulate stint performance
                stint_time, stint_risk = self._simulate_stint(
                    compound=compound,
                    stint_length=stint_length,
                    stint_start_lap=stint_start_lap,
                    race_state=race_state,
                    consider_weather=consider_weather
                )
                
                total_time += stint_time
                risk_score += stint_risk
                
                # Add pit stop time (except for last stint)
                if stint_idx < len(stop_laps):
                    pit_time = self._calculate_pit_stop_time(
                        lap=stop_laps[stint_idx],
                        safety_car_prob=safety_car_prob
                    )
                    total_time += pit_time
                
                stint_start_lap = stint_end_lap
            
            # Calculate additional metrics
            confidence = self._calculate_strategy_confidence(strategy_combo, race_state)
            weather_adjusted = consider_weather and self._is_weather_adjusted_strategy(tire_sequence)
            
            # Create strategy object
            strategy = RaceStrategy(
                strategy_id=f"strat_{num_stops}_{hash(str(strategy_combo)) % 10000}",
                num_stops=num_stops,
                stop_laps=stop_laps,
                tire_sequence=[c.value for c in tire_sequence],
                total_time=total_time,
                risk_score=risk_score,
                weather_adjusted=weather_adjusted,
                confidence=confidence
            )
            
            return strategy
            
        except Exception as e:
            print(f"Error simulating strategy: {e}")
            return None
    
    def _simulate_stint(
        self,
        compound: TireCompound,
        stint_length: int,
        stint_start_lap: int,
        race_state: RaceState,
        consider_weather: bool
    ) -> Tuple[float, float]:
        """Simulate performance of a single stint"""
        
        # Get track conditions
        track_temp = race_state.weather_data.get('track_temperature', 30.0)
        is_wet = race_state.weather_data.get('rainfall', False) if consider_weather else False
        
        # Predict tire performance over stint
        stint_performance = self.tire_model.predict_stint_performance(
            compound=compound,
            stint_length=stint_length,
            starting_fuel=100.0 - (stint_start_lap / race_state.total_laps * 60),  # Fuel decreases over race
            track_temp=track_temp,
            track_abrasiveness=self.track_characteristics['abrasiveness'],
            is_wet=is_wet
        )
        
        # Calculate total time and risk for stint
        total_stint_time = 0.0
        stint_risk = 0.0
        
        for lap_performance in stint_performance:
            # Base lap time effect
            total_stint_time += lap_performance.estimated_pace_loss
            
            # Risk factors
            if lap_performance.age_laps > lap_performance.cliff_point:
                stint_risk += 1.0  # High risk past cliff
            
            if lap_performance.grip_level < 0.4:
                stint_risk += 0.5  # Risk of poor grip
            
            # Weather-related adjustments
            if is_wet and compound not in [TireCompound.INTERMEDIATE, TireCompound.WET]:
                total_stint_time += 2.0  # Penalty for wrong tires in wet
                stint_risk += 2.0
        
        return total_stint_time, stint_risk
    
    def _calculate_pit_stop_time(self, lap: int, safety_car_prob: float) -> float:
        """Calculate pit stop time including safety car probability"""
        
        base_pit_time = self.pit_stop_time_loss
        
        # Add random variance
        variance = random.gauss(0, self.pit_stop_variance)
        pit_time = base_pit_time + variance
        
        # Safety car advantage calculation
        safety_car_chance = random.random() < safety_car_prob
        if safety_car_chance:
            pit_time -= self.safety_car_pit_advantage * 0.5  # Partial advantage
        
        return max(15.0, pit_time)  # Minimum pit time
    
    def _calculate_strategy_confidence(
        self,
        strategy: Dict[str, Any],
        race_state: RaceState
    ) -> float:
        """Calculate confidence score for a strategy (0-1)"""
        
        confidence = 0.8  # Base confidence
        
        # Penalize too many stops
        if strategy['num_stops'] > 2:
            confidence -= 0.1
        
        # Penalize very late or very early stops
        remaining_laps = race_state.total_laps - race_state.current_lap
        for stop_lap in strategy['stop_laps']:
            relative_position = (stop_lap - race_state.current_lap) / remaining_laps
            if relative_position < 0.1 or relative_position > 0.9:
                confidence -= 0.1
        
        # Bonus for balanced strategy
        if len(strategy['tire_sequence']) >= 2:
            if TireCompound.MEDIUM in strategy['tire_sequence']:
                confidence += 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def _is_weather_adjusted_strategy(self, tire_sequence: List[TireCompound]) -> bool:
        """Check if strategy includes weather-appropriate tires"""
        wet_compounds = [TireCompound.INTERMEDIATE, TireCompound.WET]
        return any(compound in wet_compounds for compound in tire_sequence)
    
    def _generate_demo_strategies(self) -> List[RaceStrategy]:
        """Generate demo strategies when no real race data is available"""
        
        demo_strategies = [
            RaceStrategy(
                strategy_id="demo_1_stop",
                num_stops=1,
                stop_laps=[35],
                tire_sequence=["medium", "hard"],
                total_time=120.5,
                risk_score=1.2,
                weather_adjusted=False,
                confidence=0.85
            ),
            RaceStrategy(
                strategy_id="demo_2_stop",
                num_stops=2,
                stop_laps=[25, 45],
                tire_sequence=["soft", "medium", "hard"],
                total_time=118.7,
                risk_score=2.1,
                weather_adjusted=False,
                confidence=0.78
            ),
            RaceStrategy(
                strategy_id="demo_aggressive",
                num_stops=2,
                stop_laps=[20, 40],
                tire_sequence=["soft", "soft", "medium"],
                total_time=116.3,
                risk_score=3.5,
                weather_adjusted=False,
                confidence=0.65
            ),
            RaceStrategy(
                strategy_id="demo_conservative",
                num_stops=1,
                stop_laps=[40],
                tire_sequence=["hard", "medium"],
                total_time=125.2,
                risk_score=0.8,
                weather_adjusted=False,
                confidence=0.92
            ),
            RaceStrategy(
                strategy_id="demo_weather",
                num_stops=3,
                stop_laps=[15, 30, 50],
                tire_sequence=["intermediate", "soft", "medium", "hard"],
                total_time=135.8,
                risk_score=4.2,
                weather_adjusted=True,
                confidence=0.45
            )
        ]
        
        return demo_strategies
    
    def analyze_strategy_comparison(
        self,
        strategies: List[RaceStrategy],
        current_strategy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Compare strategies and provide insights"""
        
        if not strategies:
            return {"error": "No strategies to analyze"}
        
        best_strategy = strategies[0]
        worst_strategy = strategies[-1]
        
        analysis = {
            "total_strategies": len(strategies),
            "best_strategy": asdict(best_strategy),
            "worst_strategy": asdict(worst_strategy),
            "time_difference": worst_strategy.total_time - best_strategy.total_time,
            "risk_analysis": {
                "lowest_risk": min(s.risk_score for s in strategies),
                "highest_risk": max(s.risk_score for s in strategies),
                "average_risk": np.mean([s.risk_score for s in strategies])
            },
            "stop_distribution": {
                "0_stops": len([s for s in strategies if s.num_stops == 0]),
                "1_stop": len([s for s in strategies if s.num_stops == 1]),
                "2_stops": len([s for s in strategies if s.num_stops == 2]),
                "3_stops": len([s for s in strategies if s.num_stops == 3])
            },
            "weather_strategies": len([s for s in strategies if s.weather_adjusted])
        }
        
        return analysis