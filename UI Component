"""
Reusable card components inspired by dataprofessor/dashboard-kit
"""

import streamlit as st
from typing import Optional

class MetricCard:
    """Metric card for displaying key metrics"""
    
    def __init__(self, title: str, value: str, change: Optional[float] = None, 
                 icon: str = "📊", help_text: str = ""):
        self.title = title
        self.value = value
        self.change = change
        self.icon = icon
        self.help_text = help_text
    
    def render(self):
        """Render the metric card"""
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.markdown(f"<h1 style='text-align: center;'>{self.icon}</h1>", 
                       unsafe_allow_html=True)
        
        with col2:
            if self.change is not None:
                st.metric(
                    label=self.title,
                    value=self.value,
                    delta=f"{self.change:+.1f}%" if self.change != 0 else None,
                    help=self.help_text
                )
            else:
                st.metric(
                    label=self.title,
                    value=self.value,
                    help=self.help_text
                )

class ComponentCard:
    """Card for sentiment components"""
    
    def __init__(self, title: str, score: float, weight: float, 
                 icon: str = "📊", description: str = ""):
        self.title = title
        self.score = score
        self.weight = weight
        self.icon = icon
        self.description = description
        
        # Determine color based on score
        if score >= 20:
            self.color = "#2ecc71"  # Green
            self.status = "Positive"
        elif score <= -20:
            self.color = "#e74c3c"  # Red
            self.status = "Negative"
        else:
            self.color = "#f39c12"  # Orange
            self.status = "Neutral"
    
    def render(self):
        """Render the component card"""
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {self.color}20, #ffffff);
            border: 1px solid {self.color}40;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: {self.color};">{self.icon} {self.title}</h4>
                <span style="
                    background-color: {self.color};
                    color: white;
                    padding: 0.2rem 0.5rem;
                    border-radius: 12px;
                    font-size: 0.8rem;
                ">
                    {self.status}
                </span>
            </div>
            <h2 style="margin: 0.5rem 0; color: {self.color};">{self.score:.1f}</h2>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                <span>Weight: {self.weight*100:.0f}%</span>
                <span>Score Range: -100 to 100</span>
            </div>
            <p style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">
                {self.description}
            </p>
        </div>
        """, unsafe_allow_html=True)