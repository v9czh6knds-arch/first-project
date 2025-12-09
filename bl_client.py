"""
Enhanced Bloomberg Client with caching and error handling
Inspired by demo-stockpeers financial data handling
"""

import blpapi
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
import threading
import time
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BloombergClient:
    """Professional Bloomberg API client with advanced features"""
    
    def __init__(self, host: str = "localhost", port: int = 8194):
        self.host = host
        self.port = port
        self.session = None
        self.connected = False
        self.lock = threading.Lock()
        
        # MASI configuration
        self.masi_ticker = "MASI Index"
        
        # Field mappings (complete set for MASI)
        self.field_mappings = {
            'close': 'PX_LAST',
            'high': 'PX_HIGH',
            'low': 'PX_LOW', 
            'open': 'PX_OPEN',
            'volume': 'VOLUME',
            'advances': 'ADVANCING_ISSUES',
            'declines': 'DECLINING_ISSUES',
            'unchanged': 'UNCHANGED_ISSUES',
            'total_issues': 'TOT_TRADED_ISSUES',
            'new_highs': 'NEW_HIGH_52W',
            'new_lows': 'NEW_LOW_52W',
            'rsi': 'RSI_14D',
            'macd': 'MACD',
            'macd_signal': 'MACD_SIGNAL',
            'stochastic': 'STOCHASTIC_OSCILLATOR',
            'vwap': 'EQY_WEIGHTED_AVG_PX',
            'pe_ratio': 'PE_RATIO',
            'dividend_yield': 'DVD_YLD'
        }
        
        # Additional Moroccan market tickers
        self.moroccan_tickers = {
            'MASI': 'MASI Index',
            'MADEX': 'MADEX Index',
            'MSI20': 'MSI20 Index',
            'Banks': 'CBI Index',
            'Insurance': 'IAI Index'
        }
        
        self.connect()
    
    def connect(self, retries: int = 3) -> bool:
        """Connect to Bloomberg with retry logic"""
        for attempt in range(retries):
            try:
                with self.lock:
                    session_options = blpapi.SessionOptions()
                    session_options.setServerHost(self.host)
                    session_options.setServerPort(self.port)
                    
                    self.session = blpapi.Session(session_options)
                    
                    if not self.session.start():
                        logger.warning(f"Bloomberg session start failed (attempt {attempt + 1})")
                        time.sleep(2)
                        continue
                    
                    if not self.session.openService("//blp/refdata"):
                        logger.warning(f"Bloomberg service open failed (attempt {attempt + 1})")
                        self.session.stop()
                        time.sleep(2)
                        continue
                    
                    self.connected = True
                    logger.info("Bloomberg connected successfully")
                    return True
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)
        
        self.connected = False
        logger.error("Failed to connect to Bloomberg after all retries")
        return False
    
    @lru_cache(maxsize=128)
    def get_reference_data_cached(self, ticker: str, fields: tuple, date_str: str) -> Dict:
        """Cached version of get_reference_data"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return self.get_reference_data(ticker, list(fields), date)
    
    def get_reference_data(self, ticker: str, fields: List[str], date: datetime = None) -> Dict[str, Any]:
        """Get reference data with improved error handling"""
        if not self.connected or not self.session:
            logger.error("Not connected to Bloomberg")
            return {}
        
        try:
            ref_data_service = self.session.getService("//blp/refdata")
            request = ref_data_service.createRequest("ReferenceDataRequest")
            
            # Add security
            request.getElement("securities").appendValue(ticker)
            
            # Add fields
            for field in fields:
                request.getElement("fields").appendValue(field)
            
            # Add date override if provided
            if date:
                overrides = request.getElement("overrides")
                override = overrides.appendElement()
                override.setElement("fieldId", "END_DATE_OVERRIDE")
                override.setElement("value", date.strftime("%Y%m%d"))
            
            # Add request ID for tracking
            request_id = f"{ticker}_{datetime.now().timestamp()}"
            
            # Send request
            self.session.sendRequest(request, correlationId=blpapi.CorrelationId(request_id))
            
            # Process response with timeout
            data = {}
            start_time = time.time()
            timeout = 10  # seconds
            
            while time.time() - start_time < timeout:
                event = self.session.nextEvent(500)  # 500ms timeout
                
                if event.eventType() == blpapi.Event.RESPONSE:
                    for msg in event:
                        if msg.correlationIds()[0].value() == request_id:
                            security_data_array = msg.getElement("securityData")
                            
                            for i in range(security_data_array.numValues()):
                                security_data = security_data_array.getValue(i)
                                
                                if security_data.hasElement("fieldExceptions"):
                                    # Handle field exceptions
                                    field_exceptions = security_data.getElement("fieldExceptions")
                                    for j in range(field_exceptions.numValues()):
                                        field_exception = field_exceptions.getValue(j)
                                        field_id = field_exception.getElement("fieldId").getValue()
                                        error_info = field_exception.getElement("errorInfo")
                                        error_message = error_info.getElement("message").getValue()
                                        logger.warning(f"Field {field_id} error: {error_message}")
                                
                                if security_data.hasElement("fieldData"):
                                    field_data = security_data.getElement("fieldData")
                                    
                                    for field in fields:
                                        if field_data.hasElement(field):
                                            element = field_data.getElement(field)
                                            if element.isNull():
                                                data[field] = None
                                            elif element.isArray():
                                                # Handle array values
                                                values = []
                                                for k in range(element.numValues()):
                                                    values.append(element.getValue(k))
                                                data[field] = values
                                            else:
                                                value = element.getValue()
                                                # Convert numeric values
                                                if isinstance(value, (int, float)):
                                                    data[field] = float(value)
                                                else:
                                                    data[field] = value
                                    
                                    break
                    break
                
                elif event.eventType() == blpapi.Event.TIMEOUT:
                    logger.warning(f"Request timeout for {ticker}")
                    break
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting reference data for {ticker}: {str(e)}")
            return {}
    
    def get_historical_data_bulk(self, tickers: List[str], fields: List[str],
                                start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical data for multiple tickers (demo-stockpeers style)"""
        if not self.connected:
            return pd.DataFrame()
        
        try:
            ref_data_service = self.session.getService("//blp/refdata")
            request = ref_data_service.createRequest("HistoricalDataRequest")
            
            # Add securities
            for ticker in tickers:
                request.getElement("securities").appendValue(ticker)
            
            # Add fields
            for field in fields:
                request.getElement("fields").appendValue(field)
            
            # Set date range
            request.set("startDate", start_date.strftime("%Y%m%d"))
            request.set("endDate", end_date.strftime("%Y%m%d"))
            request.set("periodicityAdjustment", "ACTUAL")
            request.set("periodicitySelection", "DAILY")
            
            # Send request
            self.session.sendRequest(request)
            
            # Process response
            all_data = []
            timeout_ms = 60000  # 60 seconds
            
            while True:
                event = self.session.nextEvent(timeout_ms)
                
                if event.eventType() == blpapi.Event.RESPONSE:
                    for msg in event:
                        security_data = msg.getElement("securityData")
                        security_name = security_data.getElement("security").getValue()
                        field_data_array = security_data.getElement("fieldData")
                        
                        for i in range(field_data_array.numValues()):
                            field_data = field_data_array.getValue(i)
                            record = {
                                'ticker': security_name,
                                'date': field_data.getElement("date").getValue()
                            }
                            
                            for field in fields:
                                if field_data.hasElement(field):
                                    value = field_data.getElement(field).getValue()
                                    record[field] = float(value) if isinstance(value, (int, float)) else value
                            
                            all_data.append(record)
                    break
                
                elif event.eventType() == blpapi.Event.TIMEOUT:
                    logger.error("Bulk historical data request timeout")
                    break
            
            return pd.DataFrame(all_data) if all_data else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting bulk historical data: {str(e)}")
            return pd.DataFrame()
    
    def get_masi_data(self, date: datetime = None) -> Optional[Dict[str, Any]]:
        """Get comprehensive MASI data"""
        if date is None:
            date = datetime.now()
        
        # Get all fields
        fields = list(self.field_mappings.values())
        
        # Get data from Bloomberg
        bloomberg_data = self.get_reference_data_cached(
            self.masi_ticker,
            tuple(fields),
            date.strftime("%Y-%m-%d")
        )
        
        if not bloomberg_data:
            # Try without cache
            bloomberg_data = self.get_reference_data(self.masi_ticker, fields, date)
        
        if not bloomberg_data:
            return None
        
        # Map to internal format
        data = {}
        for internal_name, bloomberg_field in self.field_mappings.items():
            if bloomberg_field in bloomberg_data:
                data[internal_name] = bloomberg_data[bloomberg_field]
        
        # Calculate additional metrics
        if data.get('close') and data.get('open'):
            data['change'] = data['close'] - data['open']
            data['change_pct'] = (data['change'] / data['open']) * 100 if data['open'] != 0 else 0
        
        # Add date
        data['date'] = date
        data['ticker'] = self.masi_ticker
        
        return data
    
    def get_moroccan_sector_data(self, date: datetime = None) -> pd.DataFrame:
        """Get data for Moroccan market sectors (demo-stockpeers style)"""
        if date is None:
            date = datetime.now()
        
        sectors_data = []
        fields = ['PX_LAST', 'PX_OPEN', 'PX_HIGH', 'PX_LOW', 'VOLUME']
        
        for sector_name, ticker in self.moroccan_tickers.items():
            sector_data = self.get_reference_data(ticker, fields, date)
            
            if sector_data:
                record = {
                    'Sector': sector_name,
                    'Ticker': ticker,
                    'Close': sector_data.get('PX_LAST', 0),
                    'Open': sector_data.get('PX_OPEN', 0),
                    'High': sector_data.get('PX_HIGH', 0),
                    'Low': sector_data.get('PX_LOW', 0),
                    'Volume': sector_data.get('VOLUME', 0)
                }
                
                if record['Open'] != 0:
                    record['Change %'] = ((record['Close'] - record['Open']) / record['Open']) * 100
                else:
                    record['Change %'] = 0
                
                sectors_data.append(record)
        
        return pd.DataFrame(sectors_data)
    
    def get_moving_averages(self, date: datetime, periods: List[int] = None) -> Dict[str, float]:
        """Calculate moving averages with Bloomberg data"""
        if periods is None:
            periods = [20, 50, 100, 200]
        
        end_date = date
        start_date = end_date - timedelta(days=max(periods) * 3)  # Extra buffer
        
        # Get historical data
        historical_data = self.get_historical_data_bulk(
            [self.masi_ticker],
            ['PX_LAST'],
            start_date,
            end_date
        )
        
        if historical_data.empty:
            return {}
        
        # Calculate moving averages
        ma_data = {}
        close_prices = historical_data[historical_data['ticker'] == self.masi_ticker]['PX_LAST']
        
        for period in periods:
            if len(close_prices) >= period:
                ma = close_prices.tail(period).mean()
                ma_data[f'ma_{period}'] = ma
        
        return ma_data
    
    def disconnect(self):
        """Disconnect from Bloomberg"""
        with self.lock:
            if self.session:
                self.session.stop()
                self.connected = False
                logger.info("Disconnected from Bloomberg")