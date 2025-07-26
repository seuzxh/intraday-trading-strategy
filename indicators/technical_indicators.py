"""
技术指标计算模块
包含常用的技术分析指标
"""

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def sma(prices, period):
        """简单移动平均线"""
        if len(prices) < period:
            return np.array([])
        return pd.Series(prices).rolling(window=period).mean().values
    
    @staticmethod
    def ema(prices, period):
        """指数移动平均线"""
        if len(prices) < period:
            return np.array([])
        return pd.Series(prices).ewm(span=period).mean().values
    
    @staticmethod
    def rsi(prices, period=14):
        """相对强弱指标"""
        if len(prices) < period + 1:
            return np.array([])
            
        price_series = pd.Series(prices)
        delta = price_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50).values
    
    @staticmethod
    def macd(prices, fast=12, slow=26, signal=9):
        """MACD指标"""
        if len(prices) < slow:
            return np.array([]), np.array([]), np.array([])
            
        price_series = pd.Series(prices)
        ema_fast = price_series.ewm(span=fast).mean()
        ema_slow = price_series.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line.values, signal_line.values, histogram.values
    
    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """布林带"""
        if len(prices) < period:
            return np.array([]), np.array([]), np.array([])
            
        price_series = pd.Series(prices)
        sma = price_series.rolling(window=period).mean()
        std = price_series.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band.values, sma.values, lower_band.values
    
    @staticmethod
    def stochastic(high_prices, low_prices, close_prices, k_period=14, d_period=3):
        """随机指标KDJ"""
        if len(close_prices) < k_period:
            return np.array([]), np.array([])
            
        high_series = pd.Series(high_prices)
        low_series = pd.Series(low_prices)
        close_series = pd.Series(close_prices)
        
        lowest_low = low_series.rolling(window=k_period).min()
        highest_high = high_series.rolling(window=k_period).max()
        
        k_percent = 100 * ((close_series - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent.values, d_percent.values
    
    @staticmethod
    def atr(high_prices, low_prices, close_prices, period=14):
        """平均真实波幅"""
        if len(close_prices) < period + 1:
            return np.array([])
            
        high_series = pd.Series(high_prices)
        low_series = pd.Series(low_prices)
        close_series = pd.Series(close_prices)
        
        tr1 = high_series - low_series
        tr2 = abs(high_series - close_series.shift(1))
        tr3 = abs(low_series - close_series.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr.values
    
    @staticmethod
    def volume_sma(volumes, period):
        """成交量移动平均"""
        if len(volumes) < period:
            return np.array([])
        return pd.Series(volumes).rolling(window=period).mean().values
    
    @staticmethod
    def find_peaks_valleys(prices, distance=5, prominence=0.01):
        """寻找价格的峰值和谷值"""
        if len(prices) < distance * 2:
            return np.array([]), np.array([])
            
        # 寻找峰值
        peaks, _ = find_peaks(prices, distance=distance, prominence=prominence)
        
        # 寻找谷值（通过反转价格序列）
        inverted_prices = -np.array(prices)
        valleys, _ = find_peaks(inverted_prices, distance=distance, prominence=prominence)
        
        return peaks, valleys