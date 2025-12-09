"""
Sentiment Calculator for MASI Market
Calculates overall market sentiment based on multiple technical indicators
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, date
import numpy as np
from config import SENTIMENT_WEIGHTS, THRESHOLDS, SENTIMENT_LABELS, TECHNICAL_CONFIG, BREADTH_THRESHOLDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MASISentimentCalculator:
    """Calculate market sentiment based on breadth, momentum, trend, and volume"""
    
    def __init__(self):
        """Initialize the sentiment calculator"""
        self.weights = SENTIMENT_WEIGHTS
        self.thresholds = THRESHOLDS
        
    def calculate_sentiment(self, market_data: Dict[str, Any], analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculate overall market sentiment
        
        Args:
            market_data: Dictionary containing market data
            analysis_date: Date for analysis (for context)
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            # Calculate component scores
            breadth_score = self._calculate_breadth_sentiment(market_data)
            momentum_score = self._calculate_momentum_sentiment(market_data)
            trend_score = self._calculate_trend_sentiment(market_data)
            volume_score = self._calculate_volume_sentiment(market_data)
            
            # Calculate weighted overall score
            overall_score = (
                breadth_score * self.weights['breadth'] +
                momentum_score * self.weights['momentum'] +
                trend_score * self.weights['trend'] +
                volume_score * self.weights['volume']
            )
            
            # Clamp score to [-100, 100]
            overall_score = max(-100, min(100, overall_score))
            
            # Get sentiment label
            sentiment_label = self._get_sentiment_label(overall_score)
            
            # Calculate technical levels
            technical_levels = self._calculate_technical_levels(market_data)
            
            return {
                'overall_score': overall_score,
                'sentiment_label': sentiment_label,
                'components': {
                    'breadth_score': breadth_score,
                    'momentum_score': momentum_score,
                    'trend_score': trend_score,
                    'volume_score': volume_score
                },
                'technical_levels': technical_levels,
                'timestamp': datetime.now(),
                'analysis_date': analysis_date or datetime.now().date(),
                'confidence': self._calculate_confidence(market_data)
            }
        except Exception as e:
            logger.error(f"Error calculating sentiment: {str(e)}")
            return self._default_sentiment()
    
    def _calculate_breadth_sentiment(self, market_data: Dict[str, Any]) -> float:
        """
        Calculate sentiment based on market breadth (advances/declines)
        Range: -100 to 100
        """
        try:
            advances = market_data.get('advances', 0)
            declines = market_data.get('declines', 0)
            unchanged = market_data.get('unchanged', 0)
            
            total = advances + declines + unchanged
            
            if total == 0:
                return 0
            
            # Calculate advance/decline ratio
            ad_ratio = advances / (declines + 1)  # +1 to avoid division by zero
            advance_pct = advances / total
            
            # Score based on advance percentage
            if advance_pct >= BREADTH_THRESHOLDS['extremely_positive']:
                score = 80 + (advance_pct - BREADTH_THRESHOLDS['extremely_positive']) * 200
            elif advance_pct >= BREADTH_THRESHOLDS['very_positive']:
                score = 60 + (advance_pct - BREADTH_THRESHOLDS['very_positive']) * 400
            elif advance_pct >= BREADTH_THRESHOLDS['positive']:
                score = 30 + (advance_pct - BREADTH_THRESHOLDS['positive']) * 200
            elif advance_pct >= BREADTH_THRESHOLDS['neutral']:
                score = (advance_pct - BREADTH_THRESHOLDS['neutral']) * 150
            elif advance_pct >= BREADTH_THRESHOLDS['negative']:
                score = -30 + (advance_pct - BREADTH_THRESHOLDS['negative']) * 200
            elif advance_pct >= BREADTH_THRESHOLDS['very_negative']:
                score = -60 + (advance_pct - BREADTH_THRESHOLDS['very_negative']) * 400
            else:
                score = -100 + advance_pct * 500
            
            return max(-100, min(100, score))
        except Exception as e:
            logger.warning(f"Error calculating breadth sentiment: {str(e)}")
            return 0
    
    def _calculate_momentum_sentiment(self, market_data: Dict[str, Any]) -> float:
        """
        Calculate sentiment based on price momentum
        Range: -100 to 100
        """
        try:
            change_pct = market_data.get('change_pct', 0)
            
            # New highs vs new lows
            new_highs = market_data.get('new_highs', 0)
            new_lows = market_data.get('new_lows', 0)
            
            # Price change component (weight: 60%)
            if abs(change_pct) < 0.5:
                price_score = change_pct * 200
            else:
                price_score = max(-100, min(100, change_pct * 20))
            
            # New highs/lows component (weight: 40%)
            total_extremes = new_highs + new_lows + 1  # +1 to avoid division by zero
            highs_ratio = new_highs / total_extremes
            
            if highs_ratio > 0.7:
                extremes_score = 80
            elif highs_ratio > 0.5:
                extremes_score = 30
            elif highs_ratio > 0.3:
                extremes_score = -30
            else:
                extremes_score = -80
            
            # Combine scores
            momentum_score = (price_score * 0.6) + (extremes_score * 0.4)
            
            return max(-100, min(100, momentum_score))
        except Exception as e:
            logger.warning(f"Error calculating momentum sentiment: {str(e)}")
            return 0
    
    def _calculate_trend_sentiment(self, market_data: Dict[str, Any]) -> float:
        """
        Calculate sentiment based on trend (moving averages, RSI)
        Range: -100 to 100
        """
        try:
            close = market_data.get('close', 0)
            rsi = market_data.get('rsi', 50)
            
            # MA comparison (if available)
            ma_20 = market_data.get('ma_20', close)
            ma_50 = market_data.get('ma_50', close)
            ma_200 = market_data.get('ma_200', close)
            
            ma_score = 0
            ma_count = 0
            
            # Price vs moving averages
            if close > ma_20:
                ma_score += 30
                ma_count += 1
            if close > ma_50:
                ma_score += 30
                ma_count += 1
            if close > ma_200:
                ma_score += 30
                ma_count += 1
            
            if ma_count > 0:
                ma_score = (ma_score / (ma_count * 30)) * 100
            
            # RSI component (0-100 scale)
            # RSI > 70 = overbought (bearish), < 30 = oversold (bullish)
            if rsi > 70:
                rsi_score = -30 + (100 - rsi) * 3  # -30 to -90 as RSI goes from 70-100
            elif rsi < 30:
                rsi_score = 30 + rsi * 2.7          # 0 to 80 as RSI goes from 0-30
            else:
                rsi_score = (rsi - 50) * 1.2        # -60 to 60 for normal range
            
            trend_score = (ma_score * 0.6) + (rsi_score * 0.4)
            
            return max(-100, min(100, trend_score))
        except Exception as e:
            logger.warning(f"Error calculating trend sentiment: {str(e)}")
            return 0
    
    def _calculate_volume_sentiment(self, market_data: Dict[str, Any]) -> float:
        """
        Calculate sentiment based on volume analysis
        Range: -100 to 100
        """
        try:
            volume = market_data.get('volume', 0)
            volume_avg = market_data.get('volume_avg_20d', volume)
            
            if volume_avg == 0:
                return 0
            
            # Volume ratio
            volume_ratio = volume / volume_avg if volume_avg != 0 else 1
            
            # Interpret volume in context of price action
            change_pct = market_data.get('change_pct', 0)
            
            # High volume on up day = bullish
            # High volume on down day = bearish
            # Low volume = weak sentiment
            
            if volume_ratio > 1.5:
                if change_pct > 0:
                    volume_score = 70  # Strong bullish
                elif change_pct < 0:
                    volume_score = -70  # Strong bearish
                else:
                    volume_score = 30
            elif volume_ratio > 1.0:
                if change_pct > 0:
                    volume_score = 40
                elif change_pct < 0:
                    volume_score = -40
                else:
                    volume_score = 0
            elif volume_ratio > 0.7:
                if change_pct > 0:
                    volume_score = 20
                elif change_pct < 0:
                    volume_score = -20
                else:
                    volume_score = -10
            else:
                volume_score = -40  # Low volume = weak
            
            return max(-100, min(100, volume_score))
        except Exception as e:
            logger.warning(f"Error calculating volume sentiment: {str(e)}")
            return 0
    
    def _calculate_technical_levels(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate key technical support and resistance levels"""
        try:
            close = market_data.get('close', 0)
            high = market_data.get('high', 0)
            low = market_data.get('low', 0)
            open_price = market_data.get('open', 0)
            
            # Pivot Point calculations
            if close > 0 and high > 0 and low > 0:
                pivot = (high + low + close) / 3
                resistance_1 = (2 * pivot) - low
                support_1 = (2 * pivot) - high
                resistance_2 = pivot + (high - low)
                support_2 = pivot - (high - low)
            else:
                pivot = close
                resistance_1 = close
                support_1 = close
                resistance_2 = close
                support_2 = close
            
            return {
                'pivot_point': float(pivot),
                'resistance_r1': float(resistance_1),
                'resistance_r2': float(resistance_2),
                'support_s1': float(support_1),
                'support_s2': float(support_2),
                'ma_20': float(market_data.get('ma_20', close)),
                'ma_50': float(market_data.get('ma_50', close)),
                'ma_200': float(market_data.get('ma_200', close))
            }
        except Exception as e:
            logger.warning(f"Error calculating technical levels: {str(e)}")
            return {
                'pivot_point': 0,
                'resistance_r1': 0,
                'resistance_r2': 0,
                'support_s1': 0,
                'support_s2': 0,
                'ma_20': 0,
                'ma_50': 0,
                'ma_200': 0
            }
    
    def _get_sentiment_label(self, score: float) -> str:
        """Get sentiment label based on score"""
        if score >= self.thresholds['very_bullish']:
            return SENTIMENT_LABELS['very_bullish']
        elif score >= self.thresholds['bullish']:
            return SENTIMENT_LABELS['bullish']
        elif score >= self.thresholds['neutral']:
            return SENTIMENT_LABELS['neutral']
        elif score >= self.thresholds['bearish']:
            return SENTIMENT_LABELS['bearish']
        else:
            return SENTIMENT_LABELS['very_bearish']
    
    def _calculate_confidence(self, market_data: Dict[str, Any]) -> float:
        """Calculate confidence level of sentiment (0.0 to 1.0)"""
        try:
            # Confidence based on number of signals present
            signals_present = 0
            total_signals = 8
            
            if market_data.get('advances', 0) > 0:
                signals_present += 1
            if market_data.get('change_pct', 0) != 0:
                signals_present += 1
            if market_data.get('rsi', 0) != 0:
                signals_present += 1
            if market_data.get('macd', 0) != 0:
                signals_present += 1
            if market_data.get('volume', 0) > 0:
                signals_present += 1
            if market_data.get('ma_20', 0) != 0:
                signals_present += 1
            if market_data.get('ma_50', 0) != 0:
                signals_present += 1
            if market_data.get('ma_200', 0) != 0:
                signals_present += 1
            
            confidence = signals_present / total_signals
            return max(0.0, min(1.0, confidence))
        except:
            return 0.5
    
    def _default_sentiment(self) -> Dict[str, Any]:
        """Return default sentiment when calculation fails"""
        return {
            'overall_score': 0,
            'sentiment_label': SENTIMENT_LABELS['neutral'],
            'components': {
                'breadth_score': 0,
                'momentum_score': 0,
                'trend_score': 0,
                'volume_score': 0
            },
            'technical_levels': {
                'pivot_point': 0,
                'resistance_r1': 0,
                'resistance_r2': 0,
                'support_s1': 0,
                'support_s2': 0,
                'ma_20': 0,
                'ma_50': 0,
                'ma_200': 0
            },
            'timestamp': datetime.now(),
            'analysis_date': datetime.now().date(),
            'confidence': 0.0
        }
