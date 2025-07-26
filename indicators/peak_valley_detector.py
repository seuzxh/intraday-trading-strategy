"""
分时顶底识别算法
基于价格行为、技术指标和成交量的综合判断
"""

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from datetime import datetime, timedelta

class PeakValleyDetector:
    """分时顶底识别器"""
    
    def __init__(self, window_size=20, min_peak_height=0.02, min_valley_depth=0.02):
        """
        初始化分时顶底识别器
        
        Args:
            window_size: 识别窗口大小
            min_peak_height: 最小顶部涨幅阈值
            min_valley_depth: 最小底部跌幅阈值
        """
        self.window_size = window_size
        self.min_peak_height = min_peak_height
        self.min_valley_depth = min_valley_depth
        self.price_history = {}
        
    def detect_signals(self, price_series, current_price, current_time):
        """
        检测分时顶底信号
        
        Args:
            price_series: 历史价格序列
            current_price: 当前价格
            current_time: 当前时间
            
        Returns:
            dict: 包含顶底信号的字典
        """
        if len(price_series) < self.window_size:
            return self._empty_signal()
            
        # 计算技术指标
        ma5 = self._calculate_ma(price_series, 5)
        ma10 = self._calculate_ma(price_series, 10)
        ma20 = self._calculate_ma(price_series, 20)
        rsi = self._calculate_rsi(price_series, 14)
        
        # 识别分时顶
        peak_signal, peak_strength = self._detect_peak(
            price_series, current_price, ma5, ma10, ma20, rsi
        )
        
        # 识别分时底
        valley_signal, valley_strength = self._detect_valley(
            price_series, current_price, ma5, ma10, ma20, rsi
        )
        
        return {
            'peak_signal': peak_signal,
            'peak_strength': peak_strength,
            'valley_signal': valley_signal,
            'valley_strength': valley_strength,
            'ma5': ma5[-1] if len(ma5) > 0 else current_price,
            'ma10': ma10[-1] if len(ma10) > 0 else current_price,
            'ma20': ma20[-1] if len(ma20) > 0 else current_price,
            'rsi': rsi[-1] if len(rsi) > 0 else 50,
            'price_position': self._get_price_position(current_price, ma5, ma10, ma20)
        }
    
    def _detect_peak(self, prices, current_price, ma5, ma10, ma20, rsi):
        """
        检测分时顶信号
        
        分时顶特征:
        1. 价格创近期新高
        2. RSI超买(>70)
        3. 价格大幅偏离均线
        4. 出现顶部形态
        """
        if len(prices) < 10 or len(rsi) == 0:
            return False, 0
            
        conditions = []
        
        # 条件1: 价格创近期新高
        recent_high = np.max(prices[-15:])
        is_new_high = current_price >= recent_high * 0.995
        conditions.append(is_new_high)
        
        # 条件2: RSI超买
        current_rsi = rsi[-1]
        is_overbought = current_rsi > 70
        conditions.append(is_overbought)
        
        # 条件3: 价格偏离5日均线过多
        if len(ma5) > 0:
            ma5_deviation = (current_price - ma5[-1]) / ma5[-1]
            is_overextended = ma5_deviation > self.min_peak_height
            conditions.append(is_overextended)
        
        # 条件4: 价格在均线上方且均线多头排列
        if len(ma5) > 0 and len(ma10) > 0:
            above_ma = current_price > ma5[-1] > ma10[-1]
            conditions.append(above_ma)
        
        # 条件5: 出现价格滞涨
        if len(prices) >= 5:
            price_stagnation = self._check_price_stagnation(prices[-5:], 'peak')
            conditions.append(price_stagnation)
        
        # 计算信号强度
        peak_score = sum(conditions)
        peak_signal = peak_score >= 3  # 至少满足3个条件
        peak_strength = peak_score / len(conditions) if conditions else 0
        
        return peak_signal, peak_strength
    
    def _detect_valley(self, prices, current_price, ma5, ma10, ma20, rsi):
        """
        检测分时底信号
        
        分时底特征:
        1. 价格创近期新低
        2. RSI超卖(<30)
        3. 价格大幅偏离均线
        4. 出现底部形态
        """
        if len(prices) < 10 or len(rsi) == 0:
            return False, 0
            
        conditions = []
        
        # 条件1: 价格创近期新低
        recent_low = np.min(prices[-15:])
        is_new_low = current_price <= recent_low * 1.005
        conditions.append(is_new_low)
        
        # 条件2: RSI超卖
        current_rsi = rsi[-1]
        is_oversold = current_rsi < 30
        conditions.append(is_oversold)
        
        # 条件3: 价格偏离5日均线过多
        if len(ma5) > 0:
            ma5_deviation = (ma5[-1] - current_price) / ma5[-1]
            is_oversold_price = ma5_deviation > self.min_valley_depth
            conditions.append(is_oversold_price)
        
        # 条件4: 价格在均线下方
        if len(ma5) > 0 and len(ma10) > 0:
            below_ma = current_price < ma5[-1]
            conditions.append(below_ma)
        
        # 条件5: 出现止跌信号
        if len(prices) >= 5:
            price_stabilizing = self._check_price_stagnation(prices[-5:], 'valley')
            conditions.append(price_stabilizing)
        
        # 计算信号强度
        valley_score = sum(conditions)
        valley_signal = valley_score >= 3  # 至少满足3个条件
        valley_strength = valley_score / len(conditions) if conditions else 0
        
        return valley_signal, valley_strength
    
    def _check_price_stagnation(self, recent_prices, signal_type):
        """检查价格滞涨或止跌"""
        if len(recent_prices) < 3:
            return False
            
        if signal_type == 'peak':
            # 检查是否出现滞涨（价格不再创新高）
            return recent_prices[-1] < max(recent_prices[:-1])
        else:  # valley
            # 检查是否出现止跌（价格不再创新低）
            return recent_prices[-1] > min(recent_prices[:-1])
    
    def _get_price_position(self, current_price, ma5, ma10, ma20):
        """获取价格相对均线位置"""
        if len(ma5) == 0:
            return 'unknown'
            
        if current_price > ma5[-1]:
            if len(ma10) > 0 and current_price > ma10[-1]:
                if len(ma20) > 0 and current_price > ma20[-1]:
                    return 'strong_bullish'  # 强势多头
                return 'bullish'  # 多头
            return 'weak_bullish'  # 弱势多头
        else:
            if len(ma10) > 0 and current_price < ma10[-1]:
                if len(ma20) > 0 and current_price < ma20[-1]:
                    return 'strong_bearish'  # 强势空头
                return 'bearish'  # 空头
            return 'weak_bearish'  # 弱势空头
    
    def _calculate_ma(self, prices, period):
        """计算移动平均线"""
        if len(prices) < period:
            return np.array([])
        return pd.Series(prices).rolling(window=period).mean().values
    
    def _calculate_rsi(self, prices, period=14):
        """计算RSI相对强弱指标"""
        if len(prices) < period + 1:
            return np.array([])
            
        price_series = pd.Series(prices)
        delta = price_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50).values  # 填充NaN为中性值50
    
    def _empty_signal(self):
        """返回空信号"""
        return {
            'peak_signal': False,
            'peak_strength': 0,
            'valley_signal': False,
            'valley_strength': 0,
            'ma5': 0,
            'ma10': 0,
            'ma20': 0,
            'rsi': 50,
            'price_position': 'unknown'
        }