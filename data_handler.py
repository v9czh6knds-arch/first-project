"""
Data Handler for MASI Sentiment Dashboard
Manages market data fetching, caching, and synthetic data generation
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from pathlib import Path
from config import DEFAULT_VALUES, MOROCCAN_MARKET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataHandler:
    """Handle all data operations for the dashboard"""
    
    def __init__(self):
        """Initialize data handler"""
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        
        self.historical_dir = self.data_dir / 'historical'
        self.historical_dir.mkdir(exist_ok=True)
        
        self.cache_dir = self.data_dir / 'cache'
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_historical_data(self, analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get historical or synthetic market data for given date
        Falls back to synthetic data if historical unavailable
        """
        try:
            if analysis_date is None:
                analysis_date = datetime.now().date()
            
            # Try to load from historical file first
            historical_data = self._load_historical_data(analysis_date)
            if historical_data:
                return historical_data
            
            # Fall back to synthetic data
            return self._generate_synthetic_data(analysis_date)
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return self._generate_synthetic_data(analysis_date or datetime.now().date())
    
    def get_latest_sentiment(self) -> Optional[Dict[str, Any]]:
        """Get the latest sentiment from cache"""
        try:
            cache_files = list(self.cache_dir.glob('sentiment_*.pkl'))
            if not cache_files:
                return None
            
            # Get most recent file
            latest_file = max(cache_files, key=lambda p: p.stat().st_mtime)
            
            import pickle
            with open(latest_file, 'rb') as f:
                data = pickle.load(f)
                return {
                    'score': data.get('overall_score', 0),
                    'trend': data.get('sentiment_label', 'Neutral')
                }
        except Exception as e:
            logger.warning(f"Error getting latest sentiment: {str(e)}")
            return None
    
    def _load_historical_data(self, analysis_date: date) -> Optional[Dict[str, Any]]:
        """Load historical data from CSV if available"""
        try:
            historical_file = self.historical_dir / f'masi_{analysis_date.strftime("%Y-%m-%d")}.csv'
            
            if not historical_file.exists():
                return None
            
            df = pd.read_csv(historical_file)
            
            if df.empty:
                return None
            
            # Convert DataFrame row to dictionary
            row = df.iloc[0].to_dict()
            
            # Ensure all required fields exist
            market_data = {
                'date': analysis_date,
                'close': float(row.get('close', 0)),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'volume': float(row.get('volume', 0)),
                'advances': int(row.get('advances', 0)),
                'declines': int(row.get('declines', 0)),
                'unchanged': int(row.get('unchanged', 0)),
                'total_issues': int(row.get('total_issues', 0)),
                'new_highs': int(row.get('new_highs', 0)),
                'new_lows': int(row.get('new_lows', 0)),
                'rsi': float(row.get('rsi', 50)),
                'macd': float(row.get('macd', 0)),
                'macd_signal': float(row.get('macd_signal', 0)),
                'stochastic': float(row.get('stochastic', 50)),
                'ma_20': float(row.get('ma_20', 0)),
                'ma_50': float(row.get('ma_50', 0)),
                'ma_200': float(row.get('ma_200', 0)),
                'volume_avg_20d': float(row.get('volume_avg_20d', 0))
            }
            
            # Calculate additional fields
            if market_data['open'] != 0:
                market_data['change_pct'] = ((market_data['close'] - market_data['open']) / market_data['open']) * 100
            else:
                market_data['change_pct'] = 0
            
            market_data['change'] = market_data['close'] - market_data['open']
            
            return market_data
        except Exception as e:
            logger.warning(f"Error loading historical data for {analysis_date}: {str(e)}")
            return None
    
    def _generate_synthetic_data(self, analysis_date: date) -> Dict[str, Any]:
        """Generate realistic synthetic market data for testing"""
        try:
            # Set random seed based on date for reproducibility
            date_seed = int(analysis_date.strftime('%Y%m%d'))
            np.random.seed(date_seed)
            
            # Base price around 13,000 (typical MASI range)
            base_price = 13000 + np.random.randn() * 500
            
            # Generate OHLC data
            open_price = base_price + np.random.randn() * 50
            close_price = open_price + np.random.randn() * 100
            high_price = max(open_price, close_price) + abs(np.random.randn() * 75)
            low_price = min(open_price, close_price) - abs(np.random.randn() * 75)
            
            # Generate breadth data (total issues ~700 on MASI)
            total_issues = int(700 + np.random.randn() * 50)
            advances = int(total_issues * (0.5 + np.random.randn() * 0.15))
            declines = int(total_issues * (0.4 + np.random.randn() * 0.15))
            unchanged = total_issues - advances - declines
            
            # Normalize if needed
            if advances + declines + unchanged != total_issues:
                unchanged = total_issues - advances - declines
            
            # Generate volume (typical MASI volume)
            volume = 2000 + abs(np.random.randn() * 800)
            volume_avg_20d = 1800 + abs(np.random.randn() * 600)
            
            # Generate technical indicators
            rsi = 30 + np.random.randn() * 20
            rsi = max(0, min(100, rsi))
            
            macd = np.random.randn() * 10
            macd_signal = macd + np.random.randn() * 5
            
            stochastic = 30 + np.random.randn() * 20
            stochastic = max(0, min(100, stochastic))
            
            # Moving averages (slightly correlated with close)
            ma_20 = close_price + np.random.randn() * 50
            ma_50 = close_price + np.random.randn() * 100
            ma_200 = close_price + np.random.randn() * 150
            
            # New highs/lows
            new_highs = int(10 + abs(np.random.randn() * 5))
            new_lows = int(8 + abs(np.random.randn() * 4))
            
            change = close_price - open_price
            change_pct = (change / open_price * 100) if open_price != 0 else 0
            
            return {
                'date': analysis_date,
                'close': float(close_price),
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'volume': float(volume),
                'volume_avg_20d': float(volume_avg_20d),
                'advances': advances,
                'declines': declines,
                'unchanged': unchanged,
                'total_issues': total_issues,
                'new_highs': new_highs,
                'new_lows': new_lows,
                'change': float(change),
                'change_pct': float(change_pct),
                'rsi': float(rsi),
                'macd': float(macd),
                'macd_signal': float(macd_signal),
                'stochastic': float(stochastic),
                'ma_20': float(ma_20),
                'ma_50': float(ma_50),
                'ma_200': float(ma_200),
                'pe_ratio': 15.5,
                'dividend_yield': 2.8,
                'ticker': MOROCCAN_MARKET['main_index']
            }
        except Exception as e:
            logger.error(f"Error generating synthetic data: {str(e)}")
            # Return minimal default data
            return {
                'date': analysis_date,
                'close': 13000,
                'open': 12950,
                'high': 13100,
                'low': 12900,
                'volume': 2000,
                'volume_avg_20d': 1800,
                'advances': 350,
                'declines': 280,
                'unchanged': 70,
                'total_issues': 700,
                'new_highs': 10,
                'new_lows': 8,
                'change': 50,
                'change_pct': 0.4,
                'rsi': 50,
                'macd': 0,
                'macd_signal': 0,
                'stochastic': 50,
                'ma_20': 12980,
                'ma_50': 12950,
                'ma_200': 12900,
                'ticker': MOROCCAN_MARKET['main_index']
            }
    
    def save_market_data(self, market_data: Dict[str, Any], analysis_date: date) -> bool:
        """Save market data to historical file"""
        try:
            historical_file = self.historical_dir / f'masi_{analysis_date.strftime("%Y-%m-%d")}.csv'
            
            df = pd.DataFrame([market_data])
            df.to_csv(historical_file, index=False)
            logger.info(f"Saved market data for {analysis_date}")
            return True
        except Exception as e:
            logger.error(f"Error saving market data: {str(e)}")
            return False
    
    def get_sentiment_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical sentiment data for past N days"""
        try:
            history = []
            current_date = datetime.now().date()
            
            for i in range(days):
                analysis_date = current_date - timedelta(days=i)
                
                # Try to load from cache first
                cache_file = self.cache_dir / f'sentiment_{analysis_date.strftime("%Y-%m-%d")}.pkl'
                
                if cache_file.exists():
                    import pickle
                    with open(cache_file, 'rb') as f:
                        sentiment = pickle.load(f)
                        sentiment['date'] = analysis_date
                        history.append(sentiment)
            
            return history
        except Exception as e:
            logger.warning(f"Error getting sentiment history: {str(e)}")
            return []
    
    def clear_old_cache(self, days: int = 7) -> int:
        """Clear cache files older than N days"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 86400)
            removed_count = 0
            
            for cache_file in self.cache_dir.glob('*.pkl'):
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    removed_count += 1
            
            logger.info(f"Cleared {removed_count} old cache files")
            return removed_count
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return 0
