import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from utils.config import Config

def create_strategy_timeline(strategies: List[Dict[str, Any]], total_laps: int) -> go.Figure:
    """
    Create an interactive timeline visualization showing different pit stop strategies.
    
    Args:
        strategies: List of strategy dictionaries
        total_laps: Total number of laps in the race
        
    Returns:
        Plotly figure object
    """
    
    fig = go.Figure()
    
    # Colors for different strategies
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, strategy in enumerate(strategies[:5]):  # Show top 5 strategies
        strategy_id = strategy.get('strategy_id', f'Strategy {i+1}')
        stop_laps = strategy.get('stop_laps', [])
        tire_sequence = strategy.get('tire_sequence', [])
        total_time = strategy.get('total_time', 0)
        risk_score = strategy.get('risk_score', 0)
        
        # Create segments for each stint
        x_values = []
        y_values = []
        colors_for_strategy = []
        hover_text = []
        
        current_lap = 1
        for stint_idx, tire in enumerate(tire_sequence):
            # Determine end lap for this stint
            if stint_idx < len(stop_laps):
                end_lap = stop_laps[stint_idx]
            else:
                end_lap = total_laps
            
            # Add line segment for this stint
            x_values.extend([current_lap, end_lap, None])
            y_values.extend([i, i, None])
            
            # Add hover information
            stint_length = end_lap - current_lap
            hover_text.extend([
                f"Strategy: {strategy_id}<br>"
                f"Stint {stint_idx + 1}: {tire.title()}<br>"
                f"Laps {current_lap}-{end_lap} ({stint_length} laps)<br>"
                f"Total Time: {total_time:.1f}s<br>"
                f"Risk Score: {risk_score:.1f}",
                "",
                ""
            ])
            
            current_lap = end_lap
        
        # Add the strategy line
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name=f"{strategy_id} ({total_time:.1f}s)",
            line=dict(width=8, color=colors[i % len(colors)]),
            marker=dict(size=8),
            hovertext=hover_text,
            hoverinfo='text'
        ))
        
        # Add pit stop markers
        for pit_lap in stop_laps:
            fig.add_trace(go.Scatter(
                x=[pit_lap],
                y=[i],
                mode='markers',
                marker=dict(
                    symbol='diamond',
                    size=12,
                    color='red',
                    line=dict(width=2, color='darkred')
                ),
                showlegend=False,
                hovertext=f"Pit Stop at Lap {pit_lap}",
                hoverinfo='text'
            ))
    
    # Customize layout
    fig.update_layout(
        title="Race Strategy Timeline Comparison",
        xaxis_title="Race Lap",
        yaxis_title="Strategy",
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(strategies[:5]))),
            ticktext=[f"Strategy {i+1}" for i in range(len(strategies[:5]))]
        ),
        hovermode='closest',
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_position_chart(positions_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a horizontal bar chart showing current race positions.
    
    Args:
        positions_data: List of driver position data
        
    Returns:
        Plotly figure object
    """
    
    # Sort by position
    sorted_positions = sorted(positions_data, key=lambda x: x.get('position', 99))
    
    drivers = [f"P{pos.get('position', '?')} {pos.get('driver_name', 'Unknown')}" for pos in sorted_positions]
    gaps = []
    tire_colors = []
    
    for pos in sorted_positions:
        gap = pos.get('gap', 'N/A')
        if gap == 'Leader':
            gaps.append(0)
        else:
            try:
                # Extract numeric part from gap string (e.g., "+1.5s" -> 1.5)
                gap_numeric = float(gap.replace('+', '').replace('s', ''))
                gaps.append(gap_numeric)
            except:
                gaps.append(0)
        
        # Get tire color
        tire_compound = pos.get('tire_compound', 'unknown').lower()
        tire_colors.append(Config.TIRE_COLORS.get(tire_compound, '#808080'))
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=drivers,
        x=gaps,
        orientation='h',
        marker=dict(color=tire_colors),
        text=[f"{gap}s ({pos.get('tire_compound', '?')}, {pos.get('tire_age', 0)} laps)" 
              for gap, pos in zip(gaps, sorted_positions)],
        textposition='outside',
        hovertemplate="<b>%{y}</b><br>" +
                      "Gap to Leader: %{x:.1f}s<br>" +
                      "Tire: %{customdata[0]} (%{customdata[1]} laps)<br>" +
                      "Team: %{customdata[2]}<extra></extra>",
        customdata=[[pos.get('tire_compound', 'Unknown'), 
                     pos.get('tire_age', 0), 
                     pos.get('team', 'Unknown')] for pos in sorted_positions]
    ))
    
    fig.update_layout(
        title="Current Race Positions",
        xaxis_title="Gap to Leader (seconds)",
        yaxis_title="Position",
        height=max(400, len(drivers) * 25),
        yaxis=dict(autorange="reversed"),
        showlegend=False
    )
    
    return fig

def create_tire_performance_chart(tire_data: Dict[str, Any]) -> go.Figure:
    """
    Create a chart showing tire performance and degradation over time.
    
    Args:
        tire_data: Dictionary containing tire stint data for drivers
        
    Returns:
        Plotly figure object
    """
    
    fig = make_subplots(
        rows=3, 
        cols=1,
        subplot_titles=('Current Tire Age by Driver', 'Tire Degradation Curves', 'Compound Usage Distribution'),
        vertical_spacing=0.12,
        row_heights=[0.3, 0.4, 0.3]
    )
    
    # Chart 1: Current tire age by driver
    drivers = []
    tire_ages = []
    compounds = []
    pit_stops = []
    
    # Handle both old and new tire data structure
    for driver_num, data in tire_data.items():
        if isinstance(data, dict) and 'current_stint' in data:
            # New structure
            current_stint = data.get('current_stint')
            if current_stint:
                drivers.append(f"Driver {driver_num}")
                
                # Calculate current tire age (assuming current lap 30 if not provided)
                lap_start = current_stint.get('lap_start', 0)
                current_lap = 30  # This could be passed as parameter in future
                tire_age = max(0, current_lap - lap_start + 1)
                tire_ages.append(tire_age)
                
                compound = current_stint.get('compound', 'unknown')
                compounds.append(compound)
                pit_stops.append(data.get('total_pit_stops', 0))
        elif isinstance(data, list) and data:
            # Old structure - use most recent stint
            current_stint = data[-1]
            drivers.append(f"Driver {driver_num}")
            
            lap_start = current_stint.get('lap_start', 0)
            tire_age = max(0, 30 - lap_start + 1)
            tire_ages.append(tire_age)
            
            compound = current_stint.get('compound', 'unknown')
            compounds.append(compound)
            pit_stops.append(len(data) - 1)
    
    # Color bars by tire compound
    bar_colors = [Config.TIRE_COLORS.get(comp.lower(), '#808080') for comp in compounds]
    
    fig.add_trace(
        go.Bar(
            x=drivers,
            y=tire_ages,
            marker=dict(color=bar_colors),
            name="Current Tire Age",
            text=[f"{age} laps<br>({comp})<br>{stops} stops" 
                  for age, comp, stops in zip(tire_ages, compounds, pit_stops)],
            textposition='outside',
            hovertemplate="<b>%{x}</b><br>" +
                         "Tire Age: %{y} laps<br>" +
                         "Compound: %{customdata[0]}<br>" +
                         "Pit Stops: %{customdata[1]}<extra></extra>",
            customdata=list(zip(compounds, pit_stops))
        ),
        row=1, col=1
    )
    
    # Chart 2: Tire stint timeline (showing degradation curve concept)
    if drivers:
        # Create a sample degradation curve for visualization
        laps = list(range(1, 31))
        
        # Different degradation curves for each compound
        degradation_curves = {
            'soft': [i * 0.08 for i in laps],
            'medium': [i * 0.05 for i in laps], 
            'hard': [i * 0.03 for i in laps]
        }
        
        for compound, degradation in degradation_curves.items():
            fig.add_trace(
                go.Scatter(
                    x=laps,
                    y=degradation,
                    mode='lines',
                    name=f"{compound.title()} Degradation",
                    line=dict(color=Config.TIRE_COLORS.get(compound, '#808080'), width=3),
                    hovertemplate=f"<b>{compound.title()} Tire</b><br>" +
                                 "Lap: %{x}<br>" +
                                 "Performance Loss: %{y:.2f}s<extra></extra>"
                ),
                row=2, col=1
            )
        
        # Add cliff points
        cliff_points = {'soft': 15, 'medium': 25, 'hard': 35}
        for compound, cliff_lap in cliff_points.items():
            if cliff_lap <= 30:
                fig.add_vline(
                    x=cliff_lap, 
                    line_dash="dash", 
                    line_color=Config.TIRE_COLORS.get(compound, '#808080'),
                    opacity=0.7,
                    row=2, col=1
                )
    
    # Chart 3: Compound usage distribution (using bar chart instead of pie)
    if compounds:
        compound_counts = {}
        for comp in compounds:
            compound_counts[comp] = compound_counts.get(comp, 0) + 1
        
        compound_names = [comp.title() for comp in compound_counts.keys()]
        compound_values = list(compound_counts.values())
        compound_colors = [Config.TIRE_COLORS.get(comp.lower(), '#808080') for comp in compound_counts.keys()]
        
        fig.add_trace(
            go.Bar(
                x=compound_names,
                y=compound_values,
                marker=dict(color=compound_colors),
                name="Compound Usage",
                text=[f"{val} driver{'s' if val != 1 else ''}" for val in compound_values],
                textposition='outside',
                hovertemplate="<b>%{x}</b><br>" +
                             "Drivers: %{y}<br>" +
                             "Percentage: %{customdata:.1f}%<extra></extra>",
                customdata=[val/len(compounds)*100 for val in compound_values]
            ),
            row=3, col=1
        )
    
    fig.update_layout(
        title="Tire Performance Analysis",
        height=800,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Update axis labels
    fig.update_yaxes(title_text="Tire Age (laps)", row=1, col=1)
    fig.update_yaxes(title_text="Performance Loss (seconds)", row=2, col=1)
    fig.update_xaxes(title_text="Lap Number", row=2, col=1)
    fig.update_yaxes(title_text="Number of Drivers", row=3, col=1)
    fig.update_xaxes(title_text="Tire Compound", row=3, col=1)
    
    return fig

def create_lap_time_comparison(lap_times_data: Dict[int, List[float]], 
                             selected_drivers: Optional[List[int]] = None) -> go.Figure:
    """
    Create a line chart comparing lap times between drivers.
    
    Args:
        lap_times_data: Dictionary mapping driver numbers to lists of lap times
        selected_drivers: Optional list of driver numbers to display
        
    Returns:
        Plotly figure object
    """
    
    fig = go.Figure()
    
    drivers_to_show = selected_drivers or list(lap_times_data.keys())[:8]  # Limit to 8 drivers
    colors = px.colors.qualitative.Set1
    
    for i, driver_num in enumerate(drivers_to_show):
        if driver_num in lap_times_data:
            lap_times = lap_times_data[driver_num]
            laps = list(range(1, len(lap_times) + 1))
            
            fig.add_trace(go.Scatter(
                x=laps,
                y=lap_times,
                mode='lines+markers',
                name=f"Driver {driver_num}",
                line=dict(color=colors[i % len(colors)]),
                marker=dict(size=4),
                hovertemplate="<b>Driver %{customdata}</b><br>" +
                              "Lap: %{x}<br>" +
                              "Time: %{y:.3f}s<extra></extra>",
                customdata=[driver_num] * len(lap_times)
            ))
    
    fig.update_layout(
        title="Lap Time Comparison",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_strategy_risk_matrix(strategies: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a scatter plot showing strategy risk vs performance.
    
    Args:
        strategies: List of strategy dictionaries
        
    Returns:
        Plotly figure object
    """
    
    if not strategies:
        return go.Figure().add_annotation(text="No strategy data available")
    
    times = [s.get('total_time', 0) for s in strategies]
    risks = [s.get('risk_score', 0) for s in strategies]
    labels = [s.get('strategy_id', f'Strategy {i+1}') for i, s in enumerate(strategies)]
    stops = [s.get('num_stops', 0) for s in strategies]
    
    # Create color scale based on number of stops
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    stop_colors = [colors[min(stop, len(colors)-1)] for stop in stops]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=risks,
        y=times,
        mode='markers',
        marker=dict(
            size=12,
            color=stop_colors,
            line=dict(width=2, color='white'),
            opacity=0.7
        ),
        text=labels,
        textposition="middle center",
        hovertemplate="<b>%{text}</b><br>" +
                      "Risk Score: %{x:.1f}<br>" +
                      "Total Time: %{y:.1f}s<br>" +
                      "Pit Stops: %{customdata}<extra></extra>",
        customdata=stops
    ))
    
    # Add quadrant lines
    if times and risks:
        avg_time = np.mean(times)
        avg_risk = np.mean(risks)
        
        fig.add_hline(y=avg_time, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=avg_risk, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add quadrant labels
        fig.add_annotation(x=max(risks)*0.8, y=min(times)*1.02, text="High Risk<br>Fast", 
                          showarrow=False, font=dict(size=10, color="gray"))
        fig.add_annotation(x=min(risks)*1.1, y=min(times)*1.02, text="Low Risk<br>Fast", 
                          showarrow=False, font=dict(size=10, color="gray"))
        fig.add_annotation(x=min(risks)*1.1, y=max(times)*0.98, text="Low Risk<br>Slow", 
                          showarrow=False, font=dict(size=10, color="gray"))
        fig.add_annotation(x=max(risks)*0.8, y=max(times)*0.98, text="High Risk<br>Slow", 
                          showarrow=False, font=dict(size=10, color="gray"))
    
    fig.update_layout(
        title="Strategy Risk vs Performance Matrix",
        xaxis_title="Risk Score",
        yaxis_title="Total Time (seconds)",
        height=500,
        showlegend=False
    )
    
    return fig

def create_weather_timeline(weather_history: List[Tuple[int, Dict[str, Any]]]) -> go.Figure:
    """
    Create a timeline showing weather conditions throughout the race.
    
    Args:
        weather_history: List of (lap, weather_data) tuples
        
    Returns:
        Plotly figure object
    """
    
    if not weather_history:
        return go.Figure().add_annotation(text="No weather data available")
    
    laps = [lap for lap, _ in weather_history]
    track_temps = [weather.get('track_temperature', 0) for _, weather in weather_history]
    air_temps = [weather.get('air_temperature', 0) for _, weather in weather_history]
    rainfall = [weather.get('rainfall', False) for _, weather in weather_history]
    
    fig = make_subplots(
        rows=2, 
        cols=1,
        subplot_titles=('Temperature', 'Rainfall'),
        vertical_spacing=0.15,
        shared_xaxes=True
    )
    
    # Temperature chart
    fig.add_trace(
        go.Scatter(
            x=laps, 
            y=track_temps, 
            mode='lines+markers',
            name='Track Temperature',
            line=dict(color='red'),
            marker=dict(size=4)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=laps, 
            y=air_temps, 
            mode='lines+markers',
            name='Air Temperature',
            line=dict(color='blue'),
            marker=dict(size=4)
        ),
        row=1, col=1
    )
    
    # Rainfall chart
    rainfall_numeric = [1 if rain else 0 for rain in rainfall]
    fig.add_trace(
        go.Scatter(
            x=laps, 
            y=rainfall_numeric, 
            mode='lines+markers',
            name='Rainfall',
            line=dict(color='green', width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(0,255,0,0.2)'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title="Weather Conditions Timeline",
        height=500,
        xaxis_title="Lap Number"
    )
    
    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
    fig.update_yaxes(title_text="Rain (Yes/No)", row=2, col=1, tickvals=[0, 1], ticktext=['No', 'Yes'])
    
    return fig

def create_pit_stop_analysis(pit_stops: List[Dict[str, Any]]) -> go.Figure:
    """
    Create visualization analyzing pit stop performance.
    
    Args:
        pit_stops: List of pit stop data
        
    Returns:
        Plotly figure object
    """
    
    if not pit_stops:
        return go.Figure().add_annotation(text="No pit stop data available")
    
    # Group pit stops by lap
    pit_counts = {}
    for stop in pit_stops:
        lap = stop.get('lap', 0)
        pit_counts[lap] = pit_counts.get(lap, 0) + 1
    
    laps = sorted(pit_counts.keys())
    counts = [pit_counts[lap] for lap in laps]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=laps,
        y=counts,
        marker=dict(color='orange'),
        name='Pit Stops per Lap',
        hovertemplate="Lap %{x}: %{y} pit stops<extra></extra>"
    ))
    
    fig.update_layout(
        title="Pit Stop Activity by Lap",
        xaxis_title="Lap Number",
        yaxis_title="Number of Pit Stops",
        height=400
    )
    
    return fig