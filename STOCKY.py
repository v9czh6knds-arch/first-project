"""
Chart components using Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from config import THRESHOLDS

def create_gauge_chart(score: float, label: str) -> go.Figure:
    """Create a gauge chart for sentiment score"""
    
    # Determine color based on score
    if score >= THRESHOLDS['very_bullish']:
        gauge_color = "#27ae60"  # Dark green
        zone_color = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#27ae60"]
    elif score >= THRESHOLDS['bullish']:
        gauge_color = "#2ecc71"  # Green
        zone_color = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#2ecc71"]
    elif score >= THRESHOLDS['neutral']:
        gauge_color = "#f1c40f"  # Yellow
        zone_color = ["#e74c3c", "#e67e22", "#f1c40f", "#f1c40f", "#f1c40f"]
    elif score >= THRESHOLDS['bearish']:
        gauge_color = "#e67e22"  # Orange
        zone_color = ["#e74c3c", "#e67e22", "#e67e22", "#e67e22", "#e67e22"]
    else:
        gauge_color = "#e74c3c"  # Red
        zone_color = ["#e74c3c", "#e74c3c", "#e74c3c", "#e74c3c", "#e74c3c"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': f"<span style='font-size:24px; font-weight:bold;'>{label}</span>",
            'font': {'size': 20}
        },
        delta={'reference': 0, 'font': {'size': 20}},
        gauge={
            'axis': {
                'range': [-100, 100],
                'tickwidth': 1,
                'tickcolor': "darkblue",
                'tickfont': {'size': 12}
            },
            'bar': {
                'color': gauge_color,
                'thickness': 0.5
            },
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [-100, THRESHOLDS['very_bearish']], 'color': zone_color[0]},
                {'range': [THRESHOLDS['very_bearish'], THRESHOLDS['bearish']], 'color': zone_color[1]},
                {'range': [THRESHOLDS['bearish'], THRESHOLDS['neutral']], 'color': zone_color[2]},
                {'range': [THRESHOLDS['neutral'], THRESHOLDS['bullish']], 'color': zone_color[3]},
                {'range': [THRESHOLDS['bullish'], 100], 'color': zone_color[4]}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(t=50, b=50, l=50, r=50),
        font={'family': "Arial, sans-serif"}
    )
    
    return fig

def create_sentiment_timeline(data: pd.DataFrame) -> go.Figure:
    """Create timeline chart of sentiment scores"""
    
    if data.empty:
        # Return empty figure
        return go.Figure()
    
    fig = go.Figure()
    
    # Add sentiment line
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['sentiment_score'],
        mode='lines+markers',
        name='Sentiment Score',
        line=dict(color='blue', width=2),
        marker=dict(size=6, color='blue'),
        hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                     '<b>Score</b>: %{y:.1f}<extra></extra>'
    ))
    
    # Add threshold areas
    fig.add_hrect(
        y0=THRESHOLDS['bullish'], y1=100,
        fillcolor="rgba(46, 204, 113, 0.2)",
        layer="below", line_width=0,
        annotation_text="Bullish",
        annotation_position="top left"
    )
    
    fig.add_hrect(
        y0=THRESHOLDS['neutral'], y1=THRESHOLDS['bullish'],
        fillcolor="rgba(241, 196, 15, 0.2)",
        layer="below", line_width=0,
        annotation_text="Neutral"
    )
    
    fig.add_hrect(
        y0=-100, y1=THRESHOLDS['neutral'],
        fillcolor="rgba(231, 76, 60, 0.2)",
        layer="below", line_width=0,
        annotation_text="Bearish",
        annotation_position="bottom left"
    )
    
    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5
    )
    
    fig.update_layout(
        title="Sentiment Score Over Time",
        xaxis_title="Date",
        yaxis_title="Sentiment Score",
        height=400,
        hovermode="x unified",
        showlegend=True,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=12)
    )
    
    return fig

def create_component_radar_chart(components: Dict[str, float]) -> go.Figure:
    """Create radar chart for sentiment components"""
    
    categories = list(components.keys())
    values = list(components.values())
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],  # Close the polygon
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(52, 152, 219, 0.3)',
        line_color='rgb(52, 152, 219)',
        line_width=2,
        name="Component Scores"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[-100, 100]
            ),
            angularaxis=dict(
                tickfont=dict(size=12)
            )
        ),
        showlegend=False,
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig