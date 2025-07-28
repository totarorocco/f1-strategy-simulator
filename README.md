# F1 Strategy Simulator 🏎️

A real-time F1 race strategy optimizer that predicts optimal pit stops using Monte Carlo simulations and compares strategies against actual team decisions. Built for live race analysis with actionable insights.

![F1 Strategy Simulator](https://img.shields.io/badge/F1-Strategy%20Simulator-red?style=for-the-badge&logo=formula1)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)

## 🎯 Project Goal

Build a comprehensive F1 race strategy optimizer that works during live races, providing teams and fans with data-driven insights into optimal pit stop strategies using advanced Monte Carlo simulations.

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/f1-strategy-simulator.git
cd f1-strategy-simulator

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## 🚀 Features

### Core Functionality
- **Real-time Race Tracking**: Live position updates every 5 seconds during races
- **Tire Degradation Modeling**: Advanced algorithms considering compound, temperature, and fuel load
- **Monte Carlo Strategy Simulation**: 1000+ strategy combinations for optimal race planning
- **Multi-stop Strategy Analysis**: 1-stop, 2-stop, and 3-stop strategy comparisons
- **Weather Integration**: Real-time weather impact on strategy decisions

### Visualizations
- Interactive strategy timeline showing tire strategies
- Live gap charts between drivers
- Tire performance degradation graphs
- Pit window predictions for next 10 laps
- Historical track-specific analysis

### Intelligence Features
- Safety car probability modeling
- Risk factor assessment
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

### OpenF1 API (Real-time Data)
```
Base URL: https://api.openf1.org/v1/
Endpoints:
- /sessions - Current session information
- /drivers - Driver details
- /position - Real-time positions
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

### Live Race State
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
- **Reliability**: Real-time updates without lag
- **Validation**: Strategies match actual winning approaches

## 🏁 MVP Roadmap

### Phase 1 (Weekend Sprint - 20 hours)
**Must Have:**
- [x] Live position tracking
- [x] Basic tire degradation model
- [x] Simple strategy simulator (100 simulations)
- [x] Core visualization (strategy timeline)

**Nice to Have:**
- [ ] Weather integration
- [ ] Historical analysis dashboard
- [ ] Advanced visualizations
- [ ] Safety car predictions

### Phase 2 (Future Enhancements)
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

### Live Race Analysis
1. Select current race from dropdown
2. Monitor real-time positions and tire data
3. View strategy recommendations
4. Compare with actual team decisions

### Historical Analysis
1. Choose past race from archive
2. Analyze winning strategies
3. Compare different approach outcomes
4. Study track-specific patterns

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Development Notes

- Start with hardcoded 2024 season data for testing
- Implement aggressive caching to minimize API calls
- Include graceful degradation for API downtime
- Focus on clear visualizations over complex algorithms initially
- Design for F1 fans, not just technical users

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

Project Link: [https://github.com/yourusername/f1-strategy-simulator](https://github.com/yourusername/f1-strategy-simulator)

---

*Built with ❤️ for Formula 1 fans and data enthusiasts*