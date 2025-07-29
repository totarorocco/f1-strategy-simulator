# F1 Strategy Simulator 🏎️

A real-time F1 race strategy optimizer that predicts optimal pit stops using Monte Carlo simulations and compares strategies against actual team decisions. Built for live race analysis with actionable insights.

![F1 Strategy Simulator](https://img.shields.io/badge/F1-Strategy%20Simulator-red?style=for-the-badge&logo=formula1)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)

## 🎯 Project Goal

Build a comprehensive F1 race strategy optimizer that works during live races, providing teams and fans with data-driven insights into optimal pit stop strategies using advanced Monte Carlo simulations.

## ⚡ Quick Start

### What Does It Do?
The F1 Strategy Simulator is an interactive tool that analyzes Formula 1 race strategies using advanced Monte Carlo simulations. It helps you understand optimal pit stop timing, tire management, and race strategy decisions that teams make during Grand Prix events.

**Key Features:**
- 🧠 **Strategy Analysis**: Simulates 1000+ different race strategies to find the optimal approach
- 🏎️ **Tire Management**: Models tire degradation and performance over race distance
- 🌦️ **Weather Integration**: Considers weather impact on strategy decisions
- 📊 **Interactive Visualizations**: Charts showing strategy timelines and performance comparisons
- 🎯 **Driver-Specific Analysis**: Personalized strategy recommendations for individual drivers

### How to Use It

#### 1. Installation
```bash
# Clone the repository
git clone https://github.com/totarorocco/f1-strategy-simulator.git
cd f1-strategy-simulator

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

#### 2. Getting Started
1. **Open the App**: Navigate to `http://localhost:8501` in your browser
2. **Select a Track**: Choose from 24 F1 circuits (Monaco, Silverstone, Spa, etc.)
3. **Configure Parameters**: Adjust simulation settings in the sidebar:
   - Number of simulations (100-2000)
   - Weather integration (on/off)
   - Safety car probability (0-100%)
4. **Analyze Strategies**: View optimal pit stop recommendations and alternative approaches

#### 3. Understanding the Results
- **🏆 Final Recommendation**: The best strategy with expected time advantage and risk level
- **📊 Strategy Timeline**: Visual chart showing when to pit and which tires to use
- **👤 Driver Analysis**: Select any driver for personalized strategy recommendations
- **📈 Performance Metrics**: Track temperature, safety car risk, and race progress

#### 4. Key Metrics Explained
- **Risk Score**: 1-5 scale (1=conservative, 5=aggressive)
- **Time Advantage**: Seconds gained/lost compared to baseline strategy
- **Tire Sequence**: Recommended tire compounds and pit stop timing
- **Confidence**: How reliable the strategy recommendation is (0-100%)

### Example Use Case
**Scenario**: You're watching the Monaco Grand Prix and want to understand if a driver should pit now or stay out longer.

1. Select "Monaco" from the track dropdown
2. Set current lap and conditions
3. View the strategy timeline showing optimal pit windows
4. Compare different approaches (1-stop vs 2-stop strategies)
5. See the risk vs reward analysis for each option

The simulator will show you exactly when the optimal pit stop should occur and why, helping you understand the complex strategy decisions that make F1 racing so fascinating!

## 🚀 Features

### Core Functionality
- **Interactive Race Simulation**: Comprehensive strategy analysis for any F1 circuit
- **Tire Degradation Modeling**: Advanced algorithms considering compound, temperature, and fuel load
- **Monte Carlo Strategy Simulation**: 1000+ strategy combinations for optimal race planning
- **Multi-stop Strategy Analysis**: 1-stop, 2-stop, and 3-stop strategy comparisons
- **Weather Integration**: Weather impact modeling on strategy decisions

### Visualizations
- Interactive strategy timeline showing tire strategies
- Driver position and gap analysis
- Tire performance degradation graphs
- Pit window predictions and optimal timing
- Track-specific strategy patterns

### Intelligence Features
- Safety car probability modeling
- Risk factor assessment and reward analysis
- Track-specific winning pattern analysis
- Weather-adjusted strategy recommendations

## 🛠️ Technical Stack

- **Language**: Python 3.8+
- **Web Framework**: Streamlit
- **APIs**: OpenF1 (real-time), Ergast (historical), Open-Meteo (weather)
- **Deployment**: Streamlit Cloud
- **Data Processing**: Pandas, NumPy
- **Visualizations**: Plotly

## 📊 API Integration

### OpenF1 API (Historical Data)
```
Base URL: https://api.openf1.org/v1/
Endpoints:
- /sessions - Session information
- /drivers - Driver details
- /position - Position data
- /car_data - Telemetry data
- /pit - Pit stop information
- /stints - Tire stint data
```

### Ergast API (Historical Data)
```
Base URL: http://ergast.com/api/f1/
Endpoints:
- /{year}/results.json - Race results
- /{year}/{round}/pitstops.json - Pit stop history
- /circuits.json - Track information
```

### Open-Meteo API (Weather)
```
Base URL: https://api.open-meteo.com/v1/
Endpoint:
- /forecast - Weather predictions with temperature and precipitation
```

## 🧮 Algorithms & Models

### Tire Degradation Formula
```python
lap_time_loss = base_degradation * tire_age * (1 + temp_factor * (track_temp - 30)) - fuel_burn_gain
```

### Strategy Optimization Process
1. Generate random strategies with different stop counts
2. Simulate full race considering:
   - Tire degradation over time
   - Fuel burn effects
   - Track position loss during stops
   - Traffic and overtaking difficulty
3. Rank strategies by total race time and risk factors

### Safety Car Probability
- Historical data analysis for track-specific probabilities
- Dynamic adjustment based on:
  - Lap 1 incident rates
  - Weather conditions
  - Recent incidents

## 📁 Project Structure

```
f1-strategy-simulator/
├── app.py                 # Main Streamlit application
├── data_collector.py      # API integration module
├── models/
│   ├── tire_model.py     # Tire degradation calculations
│   ├── strategy.py       # Strategy generation and simulation
│   └── race_state.py     # Live race tracking
├── utils/
│   ├── config.py         # Configuration and constants
│   ├── visualizations.py # Plotly chart components
│   └── helpers.py        # Utility functions
├── data/
│   ├── tracks.json       # Track characteristics database
│   └── historical/       # Cached historical race data
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml       # Streamlit configuration
```

## 🎮 User Interface

### Main Dashboard Components
- **Header**: F1 Strategy Simulator with current race information
- **Sidebar**: Race selector, refresh rate controls, simulation parameters
- **Main Area**:
  - Live race positions table
  - Strategy recommendations with confidence scores
  - Interactive strategy timeline chart
- **Metrics Row**: Key statistics (laps remaining, weather, safety car probability)

## 📈 Data Models

### Race Strategy
```python
{
    'strategy_id': str,
    'num_stops': int,
    'stop_laps': List[int],
    'tire_sequence': List[str],  # ['medium', 'hard', 'soft']
    'total_time': float,
    'risk_score': float,
    'weather_adjusted': bool
}
```

### Tire Performance
```python
{
    'compound': str,
    'age_laps': int,
    'degradation_rate': float,
    'estimated_pace_loss': float,
    'cliff_point': int  # Performance drop threshold
}
```

### Race State
```python
{
    'lap': int,
    'positions': Dict[str, int],
    'tire_data': Dict[str, TireInfo],
    'gaps': Dict[str, float],
    'recent_stops': List[PitStop],
    'weather': WeatherData
}
```

## 🎯 Success Metrics

- **Prediction Accuracy**: 70%+ correct pit stop predictions within 3-lap window
- **Performance**: Strategy generation within 2 seconds
- **Reliability**: Fast strategy generation and analysis
- **Validation**: Strategies match actual winning approaches

## 🏁 MVP Roadmap

### Phase 1 ✅ COMPLETED
**Must Have:**
- [x] Interactive race simulation
- [x] Basic tire degradation model
- [x] Strategy simulator (1000+ simulations)
- [x] Core visualization (strategy timeline)

**Nice to Have:**
- [x] Weather integration
- [x] Track-specific analysis
- [x] Advanced visualizations
- [x] Safety car predictions

### Phase 2
- [ ] Team-specific strategy customization
- [ ] Driver skill factor integration
- [ ] Fuel saving calculations
- [ ] Multi-race championship optimization
- [ ] Machine learning model improvements

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Environment Setup
```bash
# Create virtual environment
python -m venv f1-strategy-env
source f1-strategy-env/bin/activate  # On Windows: f1-strategy-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
1. Copy `config.template.py` to `config.py`
2. Add any required API keys (all APIs used are free)
3. Adjust simulation parameters as needed

### Running the Application
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## 📊 Usage Examples

### Race Strategy Analysis
1. Select a track from the dropdown (24 F1 circuits available)
2. Configure simulation parameters and conditions
3. View optimal strategy recommendations
4. Compare different approaches and analyze trade-offs

### Track-Specific Analysis
1. Choose any F1 circuit from the selection
2. Analyze optimal strategies for that track
3. Compare different approach outcomes
4. Study track-specific patterns and characteristics

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Development Notes

- Built with 2024 season data and track characteristics
- Implements aggressive caching to minimize API calls
- Includes graceful degradation for API downtime
- Focuses on clear visualizations and user-friendly interface
- Designed for F1 fans and strategy enthusiasts

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenF1**: For providing comprehensive real-time F1 data
- **Ergast**: For historical F1 database access
- **Open-Meteo**: For weather data integration
- **Streamlit**: For the excellent web framework
- **F1 Community**: For inspiration and feedback

## 📧 Contact

**Rocco Totaro** - [rt2959@columbia.edu](mailto:rt2959@columbia.edu)

Project Link: [https://github.com/totarorocco/f1-strategy-simulator](https://github.com/totarorocco/f1-strategy-simulator)

---

*Built with ❤️ for Formula 1 fans and data enthusiasts*