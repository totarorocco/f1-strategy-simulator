import streamlit as st
import pandas as pd
import time
import json
import os
from typing import Dict, List, Any, Optional, Tuple

from data_collector import DataCollector
from models.race_state import RaceState
from models.strategy import StrategySimulator
from utils.visualizations import create_strategy_timeline, create_position_chart, create_tire_performance_chart

st.set_page_config(
    page_title="F1 Strategy Simulator",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main() -> None:
    """
    Main application function that initializes the F1 Strategy Simulator interface.
    
    This function sets up the Streamlit UI, initializes session state,
    handles race selection, and displays either live race data or demo mode.
    """
    st.title("🏎️ F1 Strategy Simulator")
    st.markdown("*Real-time F1 race strategy optimizer with Monte Carlo simulations*")
    
    # Initialize session state
    try:
        if 'data_collector' not in st.session_state:
            st.session_state.data_collector = DataCollector()
        if 'race_state' not in st.session_state:
            st.session_state.race_state = RaceState()
        if 'strategy_simulator' not in st.session_state:
            st.session_state.strategy_simulator = StrategySimulator()
    except Exception as e:
        st.error(f"Error initializing application components: {str(e)}")
        st.stop()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Simulation parameters
        st.subheader("🎮 Simulation Parameters")
        num_simulations = st.slider("Number of simulations", 100, 2000, 1000)
        consider_weather = st.checkbox("Weather integration", value=True)
        safety_car_probability = st.slider("Safety car probability", 0.0, 1.0, 0.15)
        
        # Manual refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Main content area - Demo mode only
    display_demo_mode()
    
    # Footer with credentials - Optimized for dark theme
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 20px; background-color: rgba(255, 24, 1, 0.08); border: 1px solid rgba(255, 24, 1, 0.2); border-radius: 12px; margin-top: 40px; backdrop-filter: blur(10px);">
            <p style="margin: 0; font-size: 14px; color: #E0E0E0; font-weight: 500;">
                <strong style="color: #FFFFFF;">F1 Strategy Simulator</strong> | Built with ❤️ for Formula 1 fans and data enthusiasts
            </p>
            <p style="margin: 8px 0 0 0; font-size: 13px; color: #B0B0B0;">
                <strong style="color: #D0D0D0;">Rocco Totaro</strong> - <a href="mailto:rt2959@columbia.edu" style="color: #FF6B6B; text-decoration: none; border-bottom: 1px solid rgba(255, 107, 107, 0.3); transition: all 0.3s ease;">rt2959@columbia.edu</a>
            </p>
            <p style="margin: 8px 0 0 0; font-size: 12px; color: #909090;">
                Project: <a href="https://github.com/totarorocco/f1-strategy-simulator" style="color: #FF6B6B; text-decoration: none; border-bottom: 1px solid rgba(255, 107, 107, 0.3); transition: all 0.3s ease;" target="_blank">GitHub Repository</a>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )



def display_demo_mode() -> None:
    """
    Display demo interface when no live race sessions are available.
    
    Shows simulated race data with strategy analysis and visualizations
    for demonstration and development purposes.
    """
    
    st.info("🎮 Demo Mode - Interactive F1 Strategy Simulator with 2024 season data")
    
    # Demo race selector - load all tracks from tracks.json
    demo_races = get_all_tracks_for_demo()
    
    # Add filter options
    col1, col2 = st.columns(2)
    with col1:
        circuit_types = sorted(list(set([race.get('circuit_type', 'unknown') for race in demo_races])))
        selected_type = st.selectbox(
            "Filter by Circuit Type",
            ['All Types'] + [t.title() for t in circuit_types]
        )
    
    with col2:
        regions = {
            'Europe': ['Austria', 'Belgium', 'Hungary', 'Italy', 'Monaco', 'Netherlands', 'Spain', 'United Kingdom'],
            'Americas': ['Brazil', 'Canada', 'Mexico', 'United States'],
            'Asia Pacific': ['Australia', 'Japan', 'Singapore'],
            'Middle East': ['Bahrain', 'Qatar', 'Saudi Arabia', 'United Arab Emirates']
        }
        selected_region = st.selectbox("Filter by Region", ['All Regions'] + list(regions.keys()))
    
    # Filter races based on selections
    filtered_races = demo_races
    if selected_type != 'All Types':
        filtered_races = [race for race in filtered_races if race.get('circuit_type', '').title() == selected_type]
    
    if selected_region != 'All Regions':
        region_countries = regions[selected_region]
        filtered_races = [race for race in filtered_races if race.get('country') in region_countries]
    
    if not filtered_races:
        st.warning("No tracks match the selected filters. Showing all tracks.")
        filtered_races = demo_races
    
    selected_demo = st.selectbox(
        f"Select Demo Race ({len(filtered_races)} available)",
        filtered_races,
        format_func=lambda x: f"{x['name']} ({x['country']}) - {x['laps']} laps"
    )
    
    # Generate demo data
    demo_data = generate_demo_data(selected_demo)
    
    # Strategy recommendations (using demo strategies)
    st.subheader("🧠 Strategy Recommendations")
    
    with st.spinner("Running demo strategy simulations..."):
        # Get demo strategies
        demo_strategies = get_demo_strategies()
    
    # Final Recommendation Section for Demo
    if demo_strategies:
        best_strategy = demo_strategies[0]
        
        # Create an eye-catching recommendation box
        st.markdown("### 🏆 **FINAL RECOMMENDATION**")
        
        with st.container():
            st.markdown(f"""
            <div style="background-color: #0E1117; border: 2px solid #FF1801; border-radius: 10px; padding: 20px; margin: 10px 0;">
                <h3 style="color: #FF1801; margin: 0 0 15px 0;">🎯 Optimal Strategy: {best_strategy['num_stops']}-Stop</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                    <div>
                        <strong>Expected Time:</strong> {best_strategy['total_time']:.1f}s advantage<br>
                        <strong>Risk Level:</strong> {get_risk_description(best_strategy['risk_score'])}<br>
                        <strong>Confidence:</strong> {best_strategy.get('confidence', 0.8):.0%}
                    </div>
                    <div>
                        <strong>Tire Sequence:</strong> {' → '.join(best_strategy['tire_sequence'])}<br>
                        <strong>Pit Laps:</strong> {', '.join(map(str, best_strategy['stop_laps'])) if best_strategy['stop_laps'] else 'No stops'}<br>
                        <strong>Weather Adjusted:</strong> {'Yes' if best_strategy.get('weather_adjusted') else 'No'}
                    </div>
                </div>
                <div style="background-color: #1E1E1E; padding: 10px; border-radius: 5px;">
                    <strong>💡 Key Reasoning:</strong> {generate_strategy_reasoning(best_strategy, demo_data, True, 0.15)}
                </div>
                <div style="background-color: #1A4B8C; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>⏰ Next Action:</strong> {generate_next_action_recommendation(best_strategy, demo_data)}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Display demo content (similar to live race but with static data)
    st.subheader(f"📊 {selected_demo['name']} Analysis")
    
    # Track information section
    st.markdown("### 🏁 Track Information")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Circuit Type", selected_demo.get('circuit_type', 'Unknown').title())
    with col2:
        st.metric("Total Laps", selected_demo['laps'])
    with col3:
        abrasiveness = selected_demo.get('track_characteristics', {}).get('abrasiveness', 1.0)
        st.metric("Tire Wear", f"{abrasiveness:.1f}x")
    with col4:
        overtaking = selected_demo.get('track_characteristics', {}).get('overtaking_difficulty', 1.0)
        difficulty_desc = "Easy" if overtaking < 1.3 else "Medium" if overtaking < 2.0 else "Hard"
        st.metric("Overtaking", difficulty_desc)
    with col5:
        drs_zones = selected_demo.get('track_characteristics', {}).get('drs_zones', 2)
        st.metric("DRS Zones", drs_zones)
    
    # Current race info
    st.markdown("### ⏱️ Race Status")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Lap", f"{demo_data['current_lap']}/{demo_data['total_laps']}")
    with col2:
        st.metric("Laps Remaining", demo_data['total_laps'] - demo_data['current_lap'])
    with col3:
        weather_temp = demo_data.get('weather', {}).get('track_temp', 'N/A')
        st.metric("Track Temp", f"{weather_temp}°C" if weather_temp != 'N/A' else 'N/A')
    with col4:
        rainfall = demo_data.get('weather', {}).get('rainfall', False)
        st.metric("Weather", "🌧️ Rain" if rainfall else "☀️ Dry")
    
    # Weather details
    if demo_data.get('weather'):
        weather = demo_data['weather']
        st.markdown("### 🌤️ Weather Conditions")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Air Temp", f"{weather.get('air_temp', 'N/A')}°C")
        with col2:
            st.metric("Humidity", f"{weather.get('humidity', 'N/A')}%")
        with col3:
            st.metric("Wind Speed", f"{weather.get('wind_speed', 'N/A')} km/h")
        with col4:
            rain_prob = selected_demo.get('weather_patterns', {}).get('rain_probability', 0.1)
            st.metric("Rain Probability", f"{rain_prob:.1%}")
    
    # Live positions table
    st.subheader("🏁 Current Positions")
    if demo_data['positions']:
        positions_df = pd.DataFrame(demo_data['positions'])
        st.dataframe(
            positions_df[['position', 'driver_name', 'team', 'gap', 'tire_compound', 'tire_age']],
            use_container_width=True,
            hide_index=True
        )
    
    # Driver-specific strategy analysis for demo
    st.subheader("👤 Driver-Specific Strategy Analysis")
    
    # Driver selection for demo
    if demo_data['positions']:
        demo_drivers = [(pos.get('driver_name', f"Driver {i+1}"), i+1, pos) 
                       for i, pos in enumerate(demo_data['positions'])]
        
        selected_demo_driver = st.selectbox(
            "Select Driver for Personalized Strategy",
            demo_drivers,
            format_func=lambda x: f"P{x[2].get('position', '?')} {x[0]} ({x[2].get('team', 'Unknown')})"
        )
        
        if selected_demo_driver:
            driver_strategy = generate_driver_specific_strategy(
                selected_demo_driver[2], demo_data, 500,  # Fewer simulations for demo
                True, 0.15
            )
            
            if driver_strategy:
                display_driver_strategy(selected_demo_driver, driver_strategy, demo_data)
    
    # Alternative strategies comparison
    if demo_strategies and len(demo_strategies) > 1:
        st.subheader("📋 Alternative Strategies")
        col1, col2, col3 = st.columns(3)
        
        for i, strategy in enumerate(demo_strategies[1:4]):  # Show strategies 2-4
            with [col1, col2, col3][i]:
                st.metric(
                    f"Alternative #{i+1}",
                    f"+{strategy['total_time'] - demo_strategies[0]['total_time']:.1f}s",
                    f"Risk: {strategy['risk_score']:.1f}"
                )
                st.write(f"**Stops:** {strategy['num_stops']}")
                st.write(f"**Tires:** {' → '.join(strategy['tire_sequence'])}")
                if strategy['stop_laps']:
                    st.write(f"**Stop laps:** {', '.join(map(str, strategy['stop_laps']))}")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Strategy Timeline")
        try:
            if demo_strategies:
                fig_timeline = create_strategy_timeline(demo_strategies[:5], demo_data['total_laps'])
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("No strategy data available")
        except Exception as e:
            st.error(f"Error creating strategy timeline: {str(e)}")
    
    with col2:
        st.subheader("🏎️ Position Chart")
        try:
            if demo_data['positions']:
                fig_positions = create_position_chart(demo_data['positions'])
                st.plotly_chart(fig_positions, use_container_width=True)
            else:
                st.info("No position data available")
        except Exception as e:
            st.error(f"Error creating position chart: {str(e)}")
    
    # Tire performance analysis
    st.subheader("🏁 Tire Performance Analysis")
    try:
        if demo_data.get('tire_data'):
            fig_tire = create_tire_performance_chart(demo_data['tire_data'])
            st.plotly_chart(fig_tire, use_container_width=True)
            
            # Add tire strategy insights for demo mode
            st.markdown("### 🔧 Tire Strategy Insights")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_stint_length = sum(len(data.get('stints', [])) for data in demo_data['tire_data'].values()) / len(demo_data['tire_data'])
                st.metric("Avg. Stints per Driver", f"{avg_stint_length:.1f}")
            
            with col2:
                current_compounds = []
                for data in demo_data['tire_data'].values():
                    if data.get('current_stint'):
                        current_compounds.append(data['current_stint']['compound'])
                most_common = max(set(current_compounds), key=current_compounds.count) if current_compounds else 'unknown'
                st.metric("Most Used Compound", most_common.title())
            
            with col3:
                total_pit_stops = sum(data.get('total_pit_stops', 0) for data in demo_data['tire_data'].values())
                st.metric("Total Pit Stops", total_pit_stops)
        else:
            st.info("Tire data not available in demo mode")
    except Exception as e:
        st.error(f"Error creating tire performance chart: {str(e)}")
    
    st.markdown("*This is demo data for development and testing purposes.*")

def get_demo_strategies() -> List[Dict[str, Any]]:
    """
    Get demo strategy data for demonstration purposes.
    
    Returns:
        List of dictionary objects containing demo strategy data including
        strategy ID, number of stops, tire sequences, timing, and risk scores.
    """
    
    demo_strategies = [
        {
            'strategy_id': "demo_1_stop",
            'num_stops': 1,
            'stop_laps': [35],
            'tire_sequence': ["medium", "hard"],
            'total_time': 120.5,
            'risk_score': 1.2,
            'weather_adjusted': False,
            'confidence': 0.85
        },
        {
            'strategy_id': "demo_2_stop",
            'num_stops': 2,
            'stop_laps': [25, 45],
            'tire_sequence': ["soft", "medium", "hard"],
            'total_time': 118.7,
            'risk_score': 2.1,
            'weather_adjusted': False,
            'confidence': 0.78
        },
        {
            'strategy_id': "demo_aggressive",
            'num_stops': 2,
            'stop_laps': [20, 40],
            'tire_sequence': ["soft", "soft", "medium"],
            'total_time': 116.3,
            'risk_score': 3.5,
            'weather_adjusted': False,
            'confidence': 0.65
        },
        {
            'strategy_id': "demo_conservative",
            'num_stops': 1,
            'stop_laps': [40],
            'tire_sequence': ["hard", "medium"],
            'total_time': 125.2,
            'risk_score': 0.8,
            'weather_adjusted': False,
            'confidence': 0.92
        },
        {
            'strategy_id': "demo_weather",
            'num_stops': 3,
            'stop_laps': [15, 30, 50],
            'tire_sequence': ["intermediate", "soft", "medium", "hard"],
            'total_time': 135.8,
            'risk_score': 4.2,
            'weather_adjusted': True,
            'confidence': 0.45
        }
    ]
    
    return demo_strategies

def generate_demo_data(race_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate sample race data for demo mode.
    
    Args:
        race_info: Dictionary containing race information (name, track, laps)
        
    Returns:
        Dictionary containing simulated race data including current lap,
        driver positions, weather data, and tire information.
    """
    
    import random
    
    drivers = [
        "Max Verstappen", "Lewis Hamilton", "Charles Leclerc", "Lando Norris",
        "Oscar Piastri", "Carlos Sainz", "George Russell", "Fernando Alonso"
    ]
    
    teams = [
        "Red Bull Racing", "Mercedes", "Ferrari", "McLaren",
        "McLaren", "Ferrari", "Mercedes", "Aston Martin"
    ]
    
    compounds = ["soft", "medium", "hard"]
    
    demo_positions = []
    for i, (driver, team) in enumerate(zip(drivers, teams)):
        demo_positions.append({
            "position": i + 1,
            "driver_name": driver,
            "team": team,
            "gap": f"+{random.uniform(0, 30):.1f}s" if i > 0 else "Leader",
            "tire_compound": random.choice(compounds),
            "tire_age": random.randint(1, 25)
        })
    
    # Generate realistic tire stint data
    current_lap = random.randint(20, 40)
    tire_data = {}
    
    for i, (driver, team) in enumerate(zip(drivers, teams)):
        driver_number = i + 1
        
        # Generate realistic stint history
        stints = []
        lap_counter = 1
        stint_number = 1
        
        while lap_counter < current_lap:
            # Random stint length based on tire compound
            if stint_number == 1:
                compound = random.choice(['medium', 'hard'])
                max_stint = 25
            else:
                compound = random.choice(['soft', 'medium', 'hard'])
                max_stint = {'soft': 18, 'medium': 25, 'hard': 35}[compound]
            
            stint_length = min(random.randint(12, max_stint), current_lap - lap_counter + 1)
            lap_end = min(lap_counter + stint_length - 1, current_lap)
            
            stint = {
                'compound': compound,
                'lap_start': lap_counter,
                'lap_end': lap_end if lap_end < current_lap else 0,  # 0 means current stint
                'stint_number': stint_number,
                'tyre_age_at_start': 0,
                'stint_length': stint_length,
                'is_current': lap_end >= current_lap
            }
            
            stints.append(stint)
            
            if lap_end >= current_lap:
                break
                
            lap_counter = lap_end + 1
            stint_number += 1
        
        tire_data[driver_number] = {
            'stints': stints,
            'current_stint': stints[-1] if stints else None,
            'total_pit_stops': len(stints) - 1
        }
    
    # Generate track-specific weather
    weather_patterns = race_info.get('weather_patterns', {})
    if weather_patterns:
        temp_range = weather_patterns.get('typical_track_temp_c', [25, 45])
        track_temp = random.randint(temp_range[0], temp_range[1])
        air_temp_range = weather_patterns.get('typical_air_temp_c', [20, 35])
        air_temp = random.randint(air_temp_range[0], air_temp_range[1])
        rain_prob = weather_patterns.get('rain_probability', 0.1)
        rainfall = random.random() < rain_prob
    else:
        track_temp = random.randint(25, 45)
        air_temp = random.randint(20, 35)
        rainfall = False
    
    return {
        "current_lap": current_lap,
        "total_laps": race_info['laps'],
        "positions": demo_positions,
        "weather": {
            "track_temp": track_temp,
            "air_temp": air_temp,
            "rainfall": rainfall,
            "humidity": random.randint(40, 80),
            "wind_speed": random.randint(5, 20)
        },
        "tire_data": tire_data,
        "track_info": race_info
    }

def get_risk_description(risk_score: float) -> str:
    """
    Convert numeric risk score to descriptive text.
    
    Args:
        risk_score: Numeric risk score from strategy simulation
        
    Returns:
        Human-readable risk description
    """
    if risk_score <= 1.0:
        return "🟢 Low Risk"
    elif risk_score <= 2.0:
        return "🟡 Medium Risk"
    elif risk_score <= 3.0:
        return "🟠 High Risk"
    else:
        return "🔴 Very High Risk"

def generate_strategy_reasoning(strategy: Dict[str, Any], race_data: Optional[Dict[str, Any]], 
                              consider_weather: bool, safety_car_prob: float) -> str:
    """
    Generate human-readable reasoning for why a strategy is recommended.
    
    Args:
        strategy: The recommended strategy data
        race_data: Current race state data
        consider_weather: Whether weather is being considered
        safety_car_prob: Safety car probability
        
    Returns:
        Formatted reasoning string
    """
    reasons = []
    
    # Analyze number of stops
    if strategy['num_stops'] == 0:
        reasons.append("No-stop strategy maximizes track position")
    elif strategy['num_stops'] == 1:
        reasons.append("Single stop balances speed with minimal time loss")
    elif strategy['num_stops'] == 2:
        reasons.append("Two stops allow for aggressive tire strategy")
    else:
        reasons.append("Multiple stops for maximum tire performance")
    
    # Analyze tire sequence
    if 'soft' in strategy['tire_sequence']:
        reasons.append("soft tires provide speed advantage")
    if 'hard' in strategy['tire_sequence']:
        reasons.append("hard tires ensure durability for long stints")
    
    # Weather considerations
    if consider_weather and strategy.get('weather_adjusted'):
        reasons.append("adapted for potential weather changes")
    
    # Safety car considerations
    if safety_car_prob > 0.2:
        reasons.append("accounts for high safety car probability")
    
    # Risk assessment
    if strategy['risk_score'] < 1.5:
        reasons.append("minimizes risk of tire degradation")
    
    # Confidence level
    confidence = strategy.get('confidence', 0.8)
    if confidence > 0.85:
        reasons.append("high confidence based on current conditions")
    
    return ". ".join(reasons).capitalize() + "."

def get_all_tracks_for_demo() -> List[Dict[str, Any]]:
    """
    Load all tracks from tracks.json for demo mode selection.
    
    Returns:
        List of track dictionaries with demo race information
    """
    
    try:
        # Load tracks data
        tracks_file = os.path.join(os.path.dirname(__file__), 'data', 'tracks.json')
        with open(tracks_file, 'r') as f:
            tracks_data = json.load(f)
        
        demo_races = []
        
        # Convert tracks data to demo race format
        for track_key, track_info in tracks_data.items():
            demo_race = {
                'name': f"{track_info['name']} 2024",
                'track': track_info['name'],
                'track_key': track_key,
                'laps': track_info['lap_count'],
                'country': track_info['country'],
                'circuit_type': track_info['circuit_type'],
                'track_characteristics': track_info.get('track_characteristics', {}),
                'weather_patterns': track_info.get('weather_patterns', {}),
                'coordinates': track_info.get('coordinates', {})
            }
            demo_races.append(demo_race)
        
        # Sort by country for better organization
        demo_races.sort(key=lambda x: x['country'])
        
        return demo_races
        
    except Exception as e:
        print(f"Error loading tracks data: {e}")
        # Fallback to original limited selection
        return [
            {"name": "Monaco GP 2024", "track": "Monaco", "laps": 78, "country": "Monaco"},
            {"name": "Silverstone GP 2024", "track": "Silverstone", "laps": 52, "country": "United Kingdom"},
            {"name": "Monza GP 2024", "track": "Monza", "laps": 53, "country": "Italy"}
        ]

def generate_driver_specific_strategy(driver_data: Dict[str, Any], race_data: Dict[str, Any], 
                                     num_simulations: int, consider_weather: bool, 
                                     safety_car_prob: float) -> Optional[Dict[str, Any]]:
    """
    Generate personalized strategy recommendations for a specific driver.
    
    Args:
        driver_data: Dictionary containing driver's current race data
        race_data: Overall race state data
        num_simulations: Number of simulations to run
        consider_weather: Whether to consider weather factors
        safety_car_prob: Safety car probability
        
    Returns:
        Dictionary containing driver-specific strategy recommendation
    """
    
    try:
        # Extract driver-specific information
        current_position = driver_data.get('position', 10)
        current_tire = driver_data.get('tire_compound', 'medium')
        tire_age = driver_data.get('tire_age', 10)
        gap_to_leader = parse_gap_to_numeric(driver_data.get('gap', '0s'))
        team = driver_data.get('team', 'Unknown')
        
        # Create modified race state focusing on this driver's situation
        driver_focused_state = create_driver_focused_race_state(
            driver_data, race_data, current_position, current_tire, tire_age
        )
        
        # Generate strategies with driver-specific considerations
        strategies = generate_driver_optimized_strategies(
            driver_focused_state, num_simulations, consider_weather, 
            safety_car_prob, current_position, team
        )
        
        if strategies:
            best_strategy = strategies[0]
            
            # Add driver-specific analysis
            position_gain_potential = calculate_position_gain_potential(
                current_position, best_strategy, race_data
            )
            
            # Calculate risk vs reward for this specific driver
            risk_reward_analysis = analyze_risk_vs_reward(
                best_strategy, current_position, gap_to_leader, tire_age
            )
            
            return {
                'strategy': best_strategy,
                'current_state': {
                    'position': current_position,
                    'tire': current_tire,
                    'tire_age': tire_age,
                    'gap_to_leader': gap_to_leader,
                    'team': team
                },
                'position_gain_potential': position_gain_potential,
                'risk_reward': risk_reward_analysis,
                'alternatives': strategies[1:4] if len(strategies) > 1 else []
            }
            
    except Exception as e:
        print(f"Error generating driver-specific strategy: {e}")
        return None

def display_driver_strategy(driver_info: Tuple, driver_strategy: Dict[str, Any], 
                          race_data: Dict[str, Any]) -> None:
    """
    Display the driver-specific strategy analysis in the UI.
    
    Args:
        driver_info: Tuple containing (driver_name, driver_number, driver_data)
        driver_strategy: Generated strategy data for the driver
        race_data: Overall race data
    """
    
    try:
        driver_name, driver_number, driver_data = driver_info
        strategy = driver_strategy['strategy']
        current_state = driver_strategy['current_state']
        
        # Driver-specific recommendation box
        st.markdown(f"### 🏎️ **{driver_name} - Personalized Strategy**")
    except Exception as e:
        st.error(f"Error displaying driver strategy: {e}")
        return
    
    with st.container():
        try:
            # Get the reasoning text first to avoid issues in the f-string
            reasoning_text = generate_driver_specific_reasoning(driver_strategy, race_data)
            risk_description = get_risk_description(strategy['risk_score'])
            
            # Use Streamlit native components instead of HTML to avoid rendering issues
            st.markdown("#### 📊 Current Situation")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Position:** P{current_state['position']}")
                st.write(f"**Gap to Leader:** {current_state['gap_to_leader']:.1f}s")
                st.write(f"**Team:** {current_state['team']}")
            
            with col2:
                st.write(f"**Current Tire:** {current_state['tire'].title()}")
                st.write(f"**Tire Age:** {current_state['tire_age']} laps")
                st.write(f"**Risk Level:** {risk_description}")
            
            st.markdown("#### 🎯 Recommended Strategy")
            
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Strategy:** {strategy['num_stops']}-stop")
                    st.write(f"**Tire Sequence:** {' → '.join(strategy['tire_sequence'])}")
                    st.write(f"**Expected Time Gain:** {strategy['total_time']:.1f}s")
                
                with col2:
                    st.write(f"**Pit Laps:** {', '.join(map(str, strategy['stop_laps'])) if strategy['stop_laps'] else 'No stops'}")
                    st.write(f"**Confidence:** {strategy.get('confidence', 0.8):.0%}")
                    st.write(f"**Position Gain Potential:** +{driver_strategy['position_gain_potential']} positions")
            
            st.markdown("#### 💡 Strategy Reasoning")
            st.info(reasoning_text)
        except Exception as e:
            st.error(f"Error rendering strategy display: {e}")
            # Fallback to simple display
            st.subheader(f"🏎️ {driver_name} - Strategy")
            st.write(f"Position: P{current_state['position']}")
            st.write(f"Strategy: {strategy['num_stops']}-stop")
            st.write(f"Tire Sequence: {' → '.join(strategy['tire_sequence'])}")
    
    # Risk vs Reward Analysis
    if driver_strategy.get('risk_reward'):
        st.markdown("#### ⚖️ Risk vs Reward Analysis")
        col1, col2, col3 = st.columns(3)
        
        risk_reward = driver_strategy['risk_reward']
        with col1:
            st.metric("Reward Potential", f"+{risk_reward['reward_score']:.1f} points")
        with col2:
            st.metric("Risk Factor", f"{risk_reward['risk_factor']:.1f}/10")
        with col3:
            recommendation = "GO FOR IT! 🚀" if risk_reward['recommendation'] == 'aggressive' else \
                           "BALANCED APPROACH 📊" if risk_reward['recommendation'] == 'balanced' else \
                           "PLAY IT SAFE 🛡️"
            st.metric("Recommendation", recommendation)

def generate_next_action_recommendation(strategy: Dict[str, Any], race_data: Optional[Dict[str, Any]]) -> str:
    """
    Generate actionable next step recommendations based on the optimal strategy.
    
    Args:
        strategy: The recommended strategy data
        race_data: Current race state data
        
    Returns:
        Formatted next action recommendation string
    """
    
    if not strategy.get('stop_laps'):
        return "Continue on current tires until race end - no pit stops planned"
    
    current_lap = race_data.get('current_lap', 30) if race_data else 30
    next_pit_lap = None
    
    # Find the next pit stop
    for pit_lap in strategy['stop_laps']:
        if pit_lap > current_lap:
            next_pit_lap = pit_lap
            break
    
    if next_pit_lap:
        laps_to_pit = next_pit_lap - current_lap
        
        if laps_to_pit <= 2:
            return f"🚨 PIT NOW! Target lap {next_pit_lap} is in {laps_to_pit} lap{'s' if laps_to_pit != 1 else ''}"
        elif laps_to_pit <= 5:
            return f"🟡 Prepare to pit in {laps_to_pit} laps (lap {next_pit_lap})"
        else:
            return f"📅 Next pit window: Lap {next_pit_lap} ({laps_to_pit} laps from now)"
    else:
        return "✅ All planned pit stops completed - run to finish on current tires"

def parse_gap_to_numeric(gap_str: str) -> float:
    """Convert gap string to numeric seconds"""
    if not gap_str or gap_str.lower() in ['leader', 'l']:
        return 0.0
    try:
        return float(gap_str.replace('+', '').replace('s', ''))
    except:
        return 0.0

def create_driver_focused_race_state(_driver_data: Dict[str, Any], race_data: Dict[str, Any], 
                                   position: int, tire: str, tire_age: int) -> Dict[str, Any]:
    """Create a race state focused on specific driver's situation"""
    
    # Simplified race state for driver-specific analysis
    return {
        'current_lap': race_data.get('current_lap', 30),
        'total_laps': race_data.get('total_laps', 70),
        'current_position': position,
        'current_tire': tire,
        'tire_age': tire_age,
        'weather': race_data.get('weather', {}),
        'track_temp': race_data.get('weather', {}).get('track_temp', 30)
    }

def generate_driver_optimized_strategies(driver_state: Dict[str, Any], _num_simulations: int,
                                       consider_weather: bool, _safety_car_prob: float,
                                       position: int, team: str) -> List[Dict[str, Any]]:
    """Generate strategies optimized for specific driver's situation"""
    
    # Generate base strategies with position-specific optimizations
    strategies = []
    
    # Strategy 1: Conservative (if in points)
    if position <= 10:
        strategies.append({
            'strategy_id': f'conservative_{team}',
            'num_stops': 1,
            'stop_laps': [driver_state['current_lap'] + 15],
            'tire_sequence': ['medium', 'hard'],
            'total_time': 120.0 + (position * 2),  # Position penalty
            'risk_score': 1.0,
            'confidence': 0.85,
            'weather_adjusted': consider_weather
        })
    
    # Strategy 2: Aggressive (if outside points or fighting for position)
    if position > 6:
        strategies.append({
            'strategy_id': f'aggressive_{team}',
            'num_stops': 2,
            'stop_laps': [driver_state['current_lap'] + 8, driver_state['current_lap'] + 25],
            'tire_sequence': ['soft', 'soft', 'medium'],
            'total_time': 115.0 + (position * 1.5),
            'risk_score': 3.5,
            'confidence': 0.65,
            'weather_adjusted': consider_weather
        })
    
    # Strategy 3: Balanced
    strategies.append({
        'strategy_id': f'balanced_{team}',
        'num_stops': 1,
        'stop_laps': [driver_state['current_lap'] + 20],
        'tire_sequence': ['soft', 'medium'],
        'total_time': 118.0 + (position * 1.8),
        'risk_score': 2.0,
        'confidence': 0.75,
        'weather_adjusted': consider_weather
    })
    
    # Strategy 4: Tire advantage (if current tires are old)
    if driver_state.get('tire_age', 0) > 20:
        strategies.append({
            'strategy_id': f'tire_refresh_{team}',
            'num_stops': 1,
            'stop_laps': [driver_state['current_lap'] + 3],
            'tire_sequence': ['soft', 'hard'],
            'total_time': 116.0 + (position * 1.2),
            'risk_score': 2.5,
            'confidence': 0.80,
            'weather_adjusted': consider_weather
        })
    
    # Sort by total time (accounting for position)
    strategies.sort(key=lambda x: x['total_time'])
    return strategies

def calculate_position_gain_potential(current_position: int, strategy: Dict[str, Any], 
                                    _race_data: Dict[str, Any]) -> int:
    """Calculate potential position gain from strategy"""
    
    # Base calculation on strategy aggressiveness and current position
    base_gain = 0
    
    if strategy['num_stops'] == 0:
        base_gain = max(0, min(2, (20 - current_position) // 3))
    elif strategy['num_stops'] == 1:
        base_gain = max(0, min(3, (20 - current_position) // 2))
    elif strategy['num_stops'] >= 2:
        base_gain = max(0, min(5, (20 - current_position)))
    
    # Adjust based on risk level
    if strategy['risk_score'] > 3.0:
        base_gain += 1  # High risk, high reward
    elif strategy['risk_score'] < 1.5:
        base_gain = max(0, base_gain - 1)  # Conservative approach
    
    return min(base_gain, 20 - current_position)  # Can't gain more positions than available

def analyze_risk_vs_reward(strategy: Dict[str, Any], position: int, 
                         gap_to_leader: float, tire_age: int) -> Dict[str, Any]:
    """Analyze risk vs reward for the strategy"""
    
    # Calculate reward score (0-10)
    reward_score = 0
    if position > 10:  # Outside points
        reward_score = min(10, (21 - position) * 0.8)
    elif position > 6:  # Fighting for better points
        reward_score = min(8, (11 - position) * 0.6)
    else:  # In good position
        reward_score = min(6, (7 - position) * 0.4)
    
    # Calculate risk factor (0-10)
    risk_factor = strategy['risk_score'] * 2
    if tire_age > 25:
        risk_factor += 1  # Old tires add risk
    if gap_to_leader > 60:
        risk_factor = max(0, risk_factor - 1)  # Less risk if far behind
    
    # Determine recommendation
    if reward_score > 7 and risk_factor < 6:
        recommendation = 'aggressive'
    elif reward_score > 4 and risk_factor < 4:
        recommendation = 'balanced'
    else:
        recommendation = 'conservative'
    
    return {
        'reward_score': reward_score,
        'risk_factor': min(10, risk_factor),
        'recommendation': recommendation
    }

def generate_driver_specific_reasoning(driver_strategy: Dict[str, Any], 
                                     _race_data: Dict[str, Any]) -> str:
    """Generate reasoning specific to the driver's situation"""
    
    strategy = driver_strategy['strategy']
    current_state = driver_strategy['current_state']
    position = current_state['position']
    
    reasons = []
    
    # Position-based reasoning
    if position <= 3:
        reasons.append("maintain podium position with minimal risk")
    elif position <= 6:
        reasons.append("secure valuable championship points")
    elif position <= 10:
        reasons.append("fight for points-paying position")
    else:
        reasons.append("aggressive approach needed to break into points")
    
    # Tire-based reasoning
    tire_age = current_state['tire_age']
    if tire_age > 20:
        reasons.append("fresh tires will provide significant pace advantage")
    elif tire_age < 10:
        reasons.append("current tires still have good performance")
    
    # Strategy-specific reasoning
    if strategy['num_stops'] == 0:
        reasons.append("track position is crucial at this circuit")
    elif strategy['num_stops'] >= 2:
        reasons.append("multiple stops allow for maximum tire performance")
    
    # Risk assessment
    if strategy['risk_score'] > 3.0:
        reasons.append("high-risk strategy justified by championship situation")
    elif strategy['risk_score'] < 1.5:
        reasons.append("conservative approach protects current position")
    
    return ". ".join(reasons).capitalize() + "."

if __name__ == "__main__":
    main()