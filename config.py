"""
Configuration module for MASI Sentiment Dashboard
Centralized settings for sentiment calculation, thresholds, and constants
"""

from typing import Dict

# Sentiment Component Weights (must sum to 1.0)
SENTIMENT_WEIGHTS: Dict[str, float] = {
    'breadth': 0.30,      # Market breadth (advances/declines)
    'momentum': 0.25,     # Price momentum indicators
    'trend': 0.25,        # Trend analysis (moving averages)
    'volume': 0.20        # Volume analysis
}

# Sentiment Score Thresholds
THRESHOLDS: Dict[str, float] = {
    'very_bullish': 60,
    'bullish': 30,
    'neutral': -30,
    'bearish': -60,
    'very_bearish': -100
}

# Sentiment Labels
SENTIMENT_LABELS: Dict[str, str] = {
    'very_bullish': 'Very Bullish 🚀',
    'bullish': 'Bullish ↗️',
    'neutral': 'Neutral ➡️',
    'bearish': 'Bearish ↘️',
    'very_bearish': 'Very Bearish 📉'
}

# Technical Indicators Configuration
TECHNICAL_CONFIG: Dict[str, int] = {
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'stochastic_period': 14,
    'ma_short': 20,
    'ma_medium': 50,
    'ma_long': 200
}

# Breadth Analysis Thresholds
BREADTH_THRESHOLDS: Dict[str, float] = {
    'extremely_positive': 0.75,    # 75%+ advances
    'very_positive': 0.60,         # 60-75% advances
    'positive': 0.55,              # 55-60% advances
    'neutral': 0.45,               # 45-55% advances
    'negative': 0.40,              # 40-45% advances
    'very_negative': 0.25,         # 25-40% advances
    'extremely_negative': 0.0      # 0-25% advances
}

# Cache Configuration
CACHE_CONFIG: Dict[str, int] = {
    'default_ttl': 3600,           # 1 hour
    'market_data_ttl': 1800,       # 30 minutes
    'sentiment_ttl': 3600,         # 1 hour
    'historical_ttl': 86400        # 1 day
}

# Data Source Configuration
DATA_SOURCE_CONFIG: Dict[str, str] = {
    'bloomberg_host': 'localhost',
    'bloomberg_port': '8194',
    'default_source': 'synthetic'   # 'bloomberg' or 'synthetic'
}

# Moroccan Market Configuration
MOROCCAN_MARKET: Dict[str, str] = {
    'main_index': 'MASI Index',
    'secondary_index': 'MADEX Index',
    'blue_chip_index': 'MSI20 Index',
    'bank_sector': 'CBI Index',
    'insurance_sector': 'IAI Index'
}

# Market Hours (Morocco - GMT+1, but may vary with DST)
MARKET_HOURS: Dict[str, str] = {
    'open': '09:00',
    'close': '15:30',
    'timezone': 'Africa/Casablanca'
}

# Color Scheme
COLORS: Dict[str, str] = {
    'very_bullish': '#27ae60',      # Dark Green
    'bullish': '#2ecc71',           # Green
    'neutral': '#f1c40f',           # Yellow
    'bearish': '#e67e22',           # Orange
    'very_bearish': '#e74c3c',      # Red
    'primary': '#1f77b4',           # Blue
    'secondary': '#ff7f0e',         # Orange
    'success': '#2ecc71',           # Green
    'danger': '#e74c3c'             # Red
}

# Logging Configuration
LOGGING_CONFIG: Dict[str, str] = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Default values for missing data
DEFAULT_VALUES: Dict[str, float] = {
    'rsi': 50.0,
    'macd': 0.0,
    'volume': 0.0,
    'change_pct': 0.0
}
