"""
📊 MASI Market Sentiment Dashboard
Combining dataprofessor/dashboard-kit layout with demo-stockpeers features
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration with dataprofessor style
st.set_page_config(
    page_title="MASI Market Sentiment Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import custom modules
try:
    from bl_client import BloombergClient
    from sentiment_calculator import MASISentimentCalculator
    from data_handler import DataHandler
    from config import SENTIMENT_WEIGHTS, THRESHOLDS
    from components.header import render_header
    from components.sidebar import render_sidebar
    from components.cards import MetricCard, ComponentCard
    from components.charts import create_gauge_chart, create_sentiment_timeline
    from utils.cache import cache_data, get_cached_data
    from utils.formatters import format_number, format_percentage
except ImportError as e:
    st.error(f"Import error: {e}")
    logger.error(f"Import error: {e}")
    st.stop()

# Load CSS (dataprofessor style)
def load_css():
    """Load custom CSS styles"""
    try:
        css_path = Path("styling.CSS")
        if css_path.exists():
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"Could not load CSS: {str(e)}")

class MASIDashboard:
    def __init__(self):
        """Initialize the dashboard"""
        self.data_handler = DataHandler()
        self.bloomberg_client = BloombergClient()
        self.calculator = MASISentimentCalculator()
        self.current_date = datetime.now().date()
        self.selected_date = self.current_date
        
        # Initialize session state
        if 'bloomberg_connected' not in st.session_state:
            st.session_state.bloomberg_connected = False
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "Dashboard"
        
    def setup_sidebar(self):
        """Setup sidebar navigation and controls (inspired by dashboard-kit)"""
        with st.sidebar:
            st.image("assets/logo.png", width=120)
            st.title("MASI Dashboard")
            
            # Date selector
            st.subheader("📅 Date Selection")
            self.selected_date = st.date_input(
                "Analysis Date",
                value=self.current_date,
                max_value=self.current_date,
                help="Select date for analysis"
            )
            
            # Data source selector
            st.subheader("🔌 Data Source")
            use_bloomberg = st.checkbox(
                "Use Bloomberg Live Data",
                value=st.session_state.bloomberg_connected,
                help="Connect to Bloomberg Terminal for real-time data"
            )
            
            if use_bloomberg and not st.session_state.bloomberg_connected:
                if st.button("Connect to Bloomberg"):
                    with st.spinner("Connecting to Bloomberg..."):
                        if self.bloomberg_client.connect():
                            st.session_state.bloomberg_connected = True
                            st.success("Connected to Bloomberg!")
                        else:
                            st.error("Failed to connect to Bloomberg")
                            st.session_state.bloomberg_connected = False
            
            # Navigation (dashboard-kit style)
            st.subheader("📱 Navigation")
            tabs = [
                "📈 Dashboard",
                "📊 Market Analysis", 
                "📅 Historical Data",
                "⚙️ Configuration",
                "🔍 Backtesting"
            ]
            
            selected_tab = st.radio(
                "Select Page",
                tabs,
                label_visibility="collapsed"
            )
            st.session_state.current_tab = selected_tab
            
            # Quick stats in sidebar
            st.divider()
            st.subheader("⚡ Quick Stats")
            
            # Try to get latest sentiment
            try:
                latest_data = self.data_handler.get_latest_sentiment()
                if latest_data:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Latest Score", f"{latest_data['score']:.1f}")
                    with col2:
                        st.metric("Trend", latest_data['trend'])
            except:
                pass
            
            # Footer
            st.divider()
            st.caption("© 2025 MASI Sentiment Dashboard")
            st.caption("Data: Bloomberg Terminal")
    
    def fetch_market_data(self):
        """Fetch market data from selected source"""
        cache_key = f"market_data_{self.selected_date}"
        cached_data = get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Convert date to datetime
            selected_datetime = datetime.combine(self.selected_date, datetime.min.time())
            
            if st.session_state.bloomberg_connected:
                # Fetch from Bloomberg
                market_data = self.bloomberg_client.get_masi_data(selected_datetime)
                
                if market_data:
                    # Get moving averages
                    ma_data = self.bloomberg_client.get_moving_averages(selected_datetime)
                    if ma_data:
                        market_data.update(ma_data)
            else:
                # Use historical/synthetic data
                market_data = self.data_handler.get_historical_data(self.selected_date)
            
            # Cache the data
            if market_data:
                cache_data(cache_key, market_data, ttl=3600)  # Cache for 1 hour
            
            return market_data
            
        except Exception as e:
            st.error(f"Error fetching market data: {str(e)}")
            logger.error(f"Error fetching market data: {str(e)}")
            return None
    
    def calculate_and_display(self, market_data):
        """Calculate and display sentiment results"""
        if not market_data:
            return None
        
        # Calculate sentiment
        sentiment_result = self.calculator.calculate_sentiment(market_data, self.selected_date)
        
        # Cache the result
        cache_key = f"sentiment_{self.selected_date}"
        cache_data(cache_key, sentiment_result, ttl=3600)
        
        return sentiment_result
    
    def render_dashboard_tab(self):
        """Render main dashboard (inspired by dataprofessor/dashboard-kit)"""
        st.title("📈 MASI Sentiment Dashboard")
        
        # Fetch data
        market_data = self.fetch_market_data()
        
        if not market_data:
            st.warning("No market data available for selected date.")
            return
        
        # Calculate sentiment
        with st.spinner("Calculating sentiment..."):
            sentiment_result = self.calculate_and_display(market_data)
        
        if not sentiment_result:
            return
        
        # Top metrics row (dashboard-kit style)
        st.subheader("📊 Market Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            MetricCard(
                title="MASI Close",
                value=format_number(market_data.get('close', 0)),
                change=market_data.get('change_pct', 0),
                icon="📊"
            ).render()
        
        with col2:
            MetricCard(
                title="Volume",
                value=format_number(market_data.get('volume', 0), suffix="M"),
                change=market_data.get('volume_change', 0),
                icon="📈"
            ).render()
        
        with col3:
            MetricCard(
                title="Advances",
                value=str(market_data.get('advances', 0)),
                icon="🔼"
            ).render()
        
        with col4:
            MetricCard(
                title="Declines",
                value=str(market_data.get('declines', 0)),
                icon="🔽"
            ).render()
        
        # Main sentiment gauge (center of dashboard)
        st.divider()
        st.subheader("🎯 Market Sentiment Indicator")
        
        col_left, col_center, col_right = st.columns([1, 2, 1])
        
        with col_center:
            # Create gauge chart
            gauge_fig = create_gauge_chart(
                sentiment_result['overall_score'],
                sentiment_result['sentiment_label']
            )
            st.plotly_chart(gauge_fig, use_container_width=True)
        
        # Sentiment components (demo-stockpeers style)
        st.divider()
        st.subheader("📋 Sentiment Components")
        
        components = sentiment_result['components']
        
        comp_cols = st.columns(4)
        component_info = [
            ("Breadth", components['breadth_score'], SENTIMENT_WEIGHTS['breadth'], "📊", "Market breadth analysis"),
            ("Momentum", components['momentum_score'], SENTIMENT_WEIGHTS['momentum'], "🚀", "Price momentum indicators"),
            ("Trend", components['trend_score'], SENTIMENT_WEIGHTS['trend'], "📈", "Trend analysis"),
            ("Volume", components['volume_score'], SENTIMENT_WEIGHTS['volume'], "💧", "Volume analysis")
        ]
        
        for idx, (name, score, weight, icon, desc) in enumerate(component_info):
            with comp_cols[idx]:
                ComponentCard(
                    title=name,
                    score=score,
                    weight=weight,
                    icon=icon,
                    description=desc
                ).render()
        
        # Technical levels row
        st.divider()
        st.subheader("🔧 Technical Levels")
        
        tech_levels = sentiment_result['technical_levels']
        
        tech_cols = st.columns(6)
        tech_info = [
            ("Resistance R2", tech_levels.get('resistance_r2', 0)),
            ("Resistance R1", tech_levels.get('resistance_r1', 0)),
            ("Pivot Point", tech_levels.get('pivot_point', 0)),
            ("Support S1", tech_levels.get('support_s1', 0)),
            ("Support S2", tech_levels.get('support_s2', 0)),
            ("MA 50", tech_levels.get('ma_50', 0))
        ]
        
        for idx, (name, value) in enumerate(tech_info):
            with tech_cols[idx]:
                st.metric(
                    label=name,
                    value=format_number(value),
                    delta=format_percentage((value - market_data.get('close', 1)) / market_data.get('close', 1) * 100)
                )
    
    def render_market_analysis_tab(self):
        """Render market analysis page (demo-stockpeers style)"""
        st.title("📊 Market Analysis")
        
        # Fetch data
        market_data = self.fetch_market_data()
        
        if not market_data:
            return
        
        # Create tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Price Action", 
            "📊 Breadth Analysis", 
            "📉 Technical Indicators",
            "📋 Summary"
        ])
        
        with tab1:
            self._render_price_action(market_data)
        
        with tab2:
            self._render_breadth_analysis(market_data)
        
        with tab3:
            self._render_technical_indicators(market_data)
        
        with tab4:
            self._render_market_summary(market_data)
    
    def _render_price_action(self, market_data):
        """Render price action analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Daily Range")
            # Create OHLC visualization
            fig = go.Figure(data=go.Ohlc(
                x=[self.selected_date],
                open=[market_data.get('open', 0)],
                high=[market_data.get('high', 0)],
                low=[market_data.get('low', 0)],
                close=[market_data.get('close', 0)]
            ))
            
            fig.update_layout(
                title="Price Action",
                yaxis_title="Price",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Volume Analysis")
            # Volume bar chart
            volume_data = {
                'Today': market_data.get('volume', 0),
                '20D Avg': market_data.get('volume_avg_20d', 0)
            }
            
            fig = px.bar(
                x=list(volume_data.keys()),
                y=list(volume_data.values()),
                title="Volume Comparison",
                labels={'x': 'Period', 'y': 'Volume'}
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_breadth_analysis(self, market_data):
        """Render market breadth analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Advance/Decline")
            ad_data = {
                'Advances': market_data.get('advances', 0),
                'Declines': market_data.get('declines', 0),
                'Unchanged': market_data.get('unchanged', 0)
            }
            
            fig = px.pie(
                values=list(ad_data.values()),
                names=list(ad_data.keys()),
                title="Advance/Decline Ratio"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("New Highs/Lows")
            hl_data = {
                'New Highs': market_data.get('new_highs', 0),
                'New Lows': market_data.get('new_lows', 0)
            }
            
            fig = px.bar(
                x=list(hl_data.keys()),
                y=list(hl_data.values()),
                title="52-Week New Highs/Lows"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_technical_indicators(self, market_data):
        """Render technical indicators"""
        st.subheader("Technical Indicators")
        
        indicators = {
            'RSI (14)': market_data.get('rsi', 0),
            'MACD': market_data.get('macd', 0),
            'MACD Signal': market_data.get('macd_signal', 0),
            'Stochastic': market_data.get('stochastic', 0)
        }
        
        # Create indicator cards
        cols = st.columns(4)
        for idx, (name, value) in enumerate(indicators.items()):
            with cols[idx % 4]:
                # Determine color based on value
                if name == 'RSI (14)':
                    if value > 70:
                        color = "red"
                    elif value < 30:
                        color = "green"
                    else:
                        color = "orange"
                elif name == 'MACD':
                    color = "green" if value > 0 else "red"
                else:
                    color = "blue"
                
                st.markdown(f"""
                <div class="indicator-card">
                    <h4 style="color: {color};">{name}</h4>
                    <h3>{value:.2f}</h3>
                </div>
                """, unsafe_allow_html=True)
    
    def _render_market_summary(self, market_data):
        """Render market summary table"""
        st.subheader("Market Data Summary")
        
        summary_data = [
            ("MASI Close", format_number(market_data.get('close', 0))),
            ("MASI High", format_number(market_data.get('high', 0))),
            ("MASI Low", format_number(market_data.get('low', 0))),
            ("MASI Open", format_number(market_data.get('open', 0))),
            ("Volume", f"{market_data.get('volume', 0):,.0f}M"),
            ("Advances", market_data.get('advances', 0)),
            ("Declines", market_data.get('declines', 0)),
            ("Unchanged", market_data.get('unchanged', 0)),
            ("Total Issues", market_data.get('total_issues', 0)),
            ("New 52W Highs", market_data.get('new_highs', 0)),
            ("New 52W Lows", market_data.get('new_lows', 0)),
            ("RSI 14", f"{market_data.get('rsi', 0):.1f}"),
            ("MACD", f"{market_data.get('macd', 0):.2f}"),
            ("MACD Signal", f"{market_data.get('macd_signal', 0):.2f}"),
            ("Stochastic", f"{market_data.get('stochastic', 0):.1f}")
        ]
        
        # Create DataFrame for display
        df = pd.DataFrame(summary_data, columns=["Metric", "Value"])
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    
    def run(self):
        """Main application runner"""
        # Load CSS
        load_css()
        
        # Setup sidebar
        self.setup_sidebar()
        
        # Render selected tab
        if st.session_state.current_tab == "📈 Dashboard":
            self.render_dashboard_tab()
        elif st.session_state.current_tab == "📊 Market Analysis":
            self.render_market_analysis_tab()
        elif st.session_state.current_tab == "📅 Historical Data":
            import pages.historical_data as historical_page
            historical_page.render()
        elif st.session_state.current_tab == "⚙️ Configuration":
            import pages.configuration as config_page
            config_page.render()
        elif st.session_state.current_tab == "🔍 Backtesting":
            import pages.backtesting as backtesting_page
            backtesting_page.render()

# Run the app
if __name__ == "__main__":
    try:
        app = MASIDashboard()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.write("Please ensure all dependencies are installed and Bloomberg is configured.")