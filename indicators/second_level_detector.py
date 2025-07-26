"""
秒级分时顶底识别算法
高敏感度实时监控
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .peak_valley_detector import PeakValleyDetector

class SecondLevelDetector(PeakValleyDetector):
    """秒级分时顶底识别器"""
    
    def __init__(self, window_size=60, min_peak_height=0.005, min_valley_depth=0.005):
        super().__init__(window_size, min_peak_height, min_valley_depth)
        
        # 秒级特有参数
        self.sensitivity_multiplier = 1.5
        self.signal_history = {}
        self.false_signal_count = {}
        self.last_signal_time = {}
        
    def detect_second_signals(self, price_series, current_price, current_time, volume_series=None, tick_ohlcv=None, real_time_metrics=None):
        """
        检测秒级分时顶底信号 - 增强版支持tick数据
        
        Args:
            price_series: 秒级价格序列
            current_price: 当前价格
            current_time: 当前时间
            volume_series: 成交量序列（可选）
            tick_ohlcv: tick聚合的OHLCV数据（可选）
            real_time_metrics: 实时市场指标（可选）
            
        Returns:
            dict: 秒级信号结果
        """
        if len(price_series) < self.window_size:
            return self._empty_second_signal()
        
        # 使用tick数据增强分析
        if tick_ohlcv and len(tick_ohlcv['close']) > 0:
            # 使用tick聚合数据
            prices = tick_ohlcv['close']
            volumes = tick_ohlcv['volume']
            highs = tick_ohlcv['high']
            lows = tick_ohlcv['low']
            vwap = tick_ohlcv['vwap']
        else:
            # 回退到普通价格序列
            prices = price_series
            volumes = volume_series if volume_series is not None else np.array([])
            highs = prices  # 简化处理
            lows = prices
            vwap = prices
        
        # 计算增强的技术指标
        ma_short = self._calculate_ma(prices, 10)
        ma_medium = self._calculate_ma(prices, 20)
        ma_long = self._calculate_ma(prices, 30)
        rsi = self._calculate_rsi(prices, 30)
        
        # 计算tick级别的动量指标
        momentum = self._calculate_momentum(prices, 10)
        price_volatility = self._calculate_volatility(prices, 20)
        
        # 计算VWAP偏离度
        vwap_deviation = self._calculate_vwap_deviation(prices, vwap) if len(vwap) > 0 else 0
        
        # 成交量分析
        volume_confirmation = True
        volume_intensity = 1.0
        if len(volumes) >= 10:
            volume_confirmation = self._check_enhanced_volume_confirmation(volumes, prices)
            volume_intensity = self._calculate_volume_intensity(volumes)
        
        # 实时市场微观结构分析
        microstructure_score = 0
        if real_time_metrics:
            microstructure_score = self._analyze_microstructure(real_time_metrics)
        
        # 检测增强的秒级顶部信号
        peak_signal, peak_strength = self._detect_enhanced_peak(
            prices, current_price, ma_short, ma_medium, ma_long,
            rsi, momentum, price_volatility, vwap_deviation,
            volume_confirmation, volume_intensity, microstructure_score,
            highs, lows
        )
        
        # 检测增强的秒级底部信号
        valley_signal, valley_strength = self._detect_enhanced_valley(
            prices, current_price, ma_short, ma_medium, ma_long,
            rsi, momentum, price_volatility, vwap_deviation,
            volume_confirmation, volume_intensity, microstructure_score,
            highs, lows
        )
        
        # 信号过滤和确认
        peak_signal, peak_strength = self._filter_signal(
            'peak', peak_signal, peak_strength, current_time
        )
        valley_signal, valley_strength = self._filter_signal(
            'valley', valley_signal, valley_strength, current_time
        )
        
        return {
            'peak_signal': peak_signal,
            'peak_strength': peak_strength,
            'valley_signal': valley_signal,
            'valley_strength': valley_strength,
            'momentum': momentum[-1] if len(momentum) > 0 else 0,
            'volume_confirmation': volume_confirmation,
            'volume_intensity': volume_intensity,
            'price_volatility': price_volatility,
            'vwap_deviation': vwap_deviation,
            'microstructure_score': microstructure_score,
            'ma_short': ma_short[-1] if len(ma_short) > 0 else current_price,
            'ma_medium': ma_medium[-1] if len(ma_medium) > 0 else current_price,
            'rsi': rsi[-1] if len(rsi) > 0 else 50,
            'signal_quality': self._calculate_enhanced_signal_quality(
                peak_strength, valley_strength, microstructure_score
            )
        }
    
    def _detect_enhanced_peak(self, prices, current_price, ma_short, ma_medium, ma_long,
                             rsi, momentum, volatility, vwap_deviation,
                             volume_conf, volume_intensity, microstructure_score,
                             highs, lows):
        """检测增强的秒级顶部信号"""
        if len(prices) < 20 or len(rsi) == 0:
            return False, 0
        
        conditions = []
        weights = []
        
        # 1. 价格创短期新高（权重：0.2）
        recent_high = np.max(highs[-15:]) if len(highs) >= 15 else np.max(prices[-15:])
        is_new_high = current_price >= recent_high * 0.999
        conditions.append(is_new_high)
        weights.append(0.2)
        
        # 2. RSI超买（权重：0.15）
        current_rsi = rsi[-1]
        is_overbought = current_rsi > 65
        conditions.append(is_overbought)
        weights.append(0.15)
        
        # 3. 价格偏离VWAP（权重：0.15）
        vwap_overextended = vwap_deviation > 0.005  # 0.5%偏离
        conditions.append(vwap_overextended)
        weights.append(0.15)
        
        # 4. 动量转弱（权重：0.1）
        if len(momentum) >= 3:
            momentum_weakening = momentum[-1] < momentum[-2] < momentum[-3]
            conditions.append(momentum_weakening)
            weights.append(0.1)
        else:
            conditions.append(False)
            weights.append(0.1)
        
        # 5. 成交量确认（权重：0.1）
        conditions.append(volume_conf)
        weights.append(0.1)
        
        # 6. 成交量强度（权重：0.1）
        high_volume_intensity = volume_intensity > 1.5
        conditions.append(high_volume_intensity)
        weights.append(0.1)
        
        # 7. 微观结构信号（权重：0.1）
        positive_microstructure = microstructure_score > 0.6
        conditions.append(positive_microstructure)
        weights.append(0.1)
        
        # 8. 波动率确认（权重：0.1）
        high_volatility = volatility > np.mean([volatility, 0.02])  # 动态阈值
        conditions.append(high_volatility)
        weights.append(0.1)
        
        # 计算加权得分
        weighted_score = sum(w for c, w in zip(conditions, weights) if c)
        peak_signal = weighted_score >= 0.6  # 60%阈值
        peak_strength = weighted_score
        
        return peak_signal, peak_strength
    
    def _detect_enhanced_valley(self, prices, current_price, ma_short, ma_medium, ma_long,
                               rsi, momentum, volatility, vwap_deviation,
                               volume_conf, volume_intensity, microstructure_score,
                               highs, lows):
        """检测增强的秒级底部信号"""
        if len(prices) < 20 or len(rsi) == 0:
            return False, 0
        
        conditions = []
        weights = []
        
        # 1. 价格创短期新低（权重：0.2）
        recent_low = np.min(lows[-15:]) if len(lows) >= 15 else np.min(prices[-15:])
        is_new_low = current_price <= recent_low * 1.001
        conditions.append(is_new_low)
        weights.append(0.2)
        
        # 2. RSI超卖（权重：0.15）
        current_rsi = rsi[-1]
        is_oversold = current_rsi < 35
        conditions.append(is_oversold)
        weights.append(0.15)
        
        # 3. 价格偏离VWAP（权重：0.15）
        vwap_oversold = vwap_deviation < -0.005  # -0.5%偏离
        conditions.append(vwap_oversold)
        weights.append(0.15)
        
        # 4. 动量转强（权重：0.1）
        if len(momentum) >= 3:
            momentum_strengthening = momentum[-1] > momentum[-2] > momentum[-3]
            conditions.append(momentum_strengthening)
            weights.append(0.1)
        else:
            conditions.append(False)
            weights.append(0.1)
        
        # 5. 成交量确认（权重：0.1）
        conditions.append(volume_conf)
        weights.append(0.1)
        
        # 6. 成交量强度（权重：0.1）
        high_volume_intensity = volume_intensity > 1.5
        conditions.append(high_volume_intensity)
        weights.append(0.1)
        
        # 7. 微观结构信号（权重：0.1）
        negative_microstructure = microstructure_score < -0.6
        conditions.append(negative_microstructure)
        weights.append(0.1)
        
        # 8. 波动率确认（权重：0.1）
        high_volatility = volatility > np.mean([volatility, 0.02])
        conditions.append(high_volatility)
        weights.append(0.1)
        
        # 计算加权得分
        weighted_score = sum(w for c, w in zip(conditions, weights) if c)
        valley_signal = weighted_score >= 0.6
        valley_strength = weighted_score
        
        return valley_signal, valley_strength
    
    def _calculate_momentum(self, prices, period=10):
        """计算价格动量"""
        if len(prices) < period + 1:
            return np.array([])
        
        momentum = []
        for i in range(period, len(prices)):
            mom = (prices[i] - prices[i-period]) / prices[i-period]
            momentum.append(mom)
        
        return np.array(momentum)
    
    def _check_volume_confirmation(self, volumes, prices):
        """检查成交量确认"""
        if len(volumes) < 10:
            return True
        
        # 计算成交量均值
        vol_ma = np.mean(volumes[-10:])
        current_vol = volumes[-1]
        
        # 成交量放大确认
        return current_vol > vol_ma * 1.2
    
    def _filter_signal(self, signal_type, signal, strength, current_time):
        """信号过滤和确认"""
        signal_key = f"{signal_type}_signal"
        
        # 检查信号冷却时间
        if signal_key in self.last_signal_time:
            time_diff = (current_time - self.last_signal_time[signal_key]).total_seconds()
            if time_diff < 15:  # 15秒冷却时间
                return False, 0
        
        # 检查假信号频率
        minute_key = current_time.strftime('%Y%m%d%H%M')
        if minute_key not in self.false_signal_count:
            self.false_signal_count[minute_key] = 0
        
        if self.false_signal_count[minute_key] >= 3:  # 每分钟最多3个信号
            return False, 0
        
        if signal:
            self.last_signal_time[signal_key] = current_time
            self.false_signal_count[minute_key] += 1
        
        return signal, strength
    
    def _calculate_signal_quality(self, peak_strength, valley_strength):
        """计算信号质量"""
        max_strength = max(peak_strength, valley_strength)
        if max_strength > 0.8:
            return 'high'
        elif max_strength > 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _empty_second_signal(self):
        """返回空的秒级信号"""
        return {
            'peak_signal': False,
            'peak_strength': 0,
            'valley_signal': False,
            'valley_strength': 0,
            'momentum': 0,
            'volume_confirmation': True,
            'ma_short': 0,
            'ma_medium': 0,
            'rsi': 50,
            'signal_quality': 'low'
        }

    def _calculate_vwap_deviation(self, prices, vwap):
        """计算价格相对VWAP的偏离度"""
        if len(prices) == 0 or len(vwap) == 0:
            return 0
        
        current_price = prices[-1]
        current_vwap = vwap[-1]
        
        if current_vwap == 0:
            return 0
        
        return (current_price - current_vwap) / current_vwap

    def _calculate_volatility(self, prices, window=20):
        """计算价格波动率"""
        if len(prices) < window:
            return 0
        
        returns = np.diff(prices[-window:]) / prices[-window:-1]
        return np.std(returns) if len(returns) > 0 else 0

    def _calculate_volume_intensity(self, volumes):
        """计算成交量强度"""
        if len(volumes) < 10:
            return 1.0
        
        recent_avg = np.mean(volumes[-5:])
        historical_avg = np.mean(volumes[-20:-5]) if len(volumes) >= 20 else np.mean(volumes[:-5])
        
        return recent_avg / historical_avg if historical_avg > 0 else 1.0

    def _check_enhanced_volume_confirmation(self, volumes, prices):
        """增强的成交量确认"""
        if len(volumes) < 10 or len(prices) < 10:
            return True
        
        # 成交量放大
        vol_ma = np.mean(volumes[-10:])
        current_vol = volumes[-1]
        volume_surge = current_vol > vol_ma * 1.3
        
        # 价量配合
        price_change = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        volume_change = (volumes[-1] - np.mean(volumes[-5:-1])) / np.mean(volumes[-5:-1]) if len(volumes) >= 5 else 0
        
        price_volume_sync = (price_change > 0 and volume_change > 0) or (price_change < 0 and volume_change > 0)
        
        return volume_surge and price_volume_sync

    def _analyze_microstructure(self, metrics):
        """分析市场微观结构"""
        score = 0
        
        # 价格动量
        if abs(metrics['price_momentum']) > 0.002:  # 0.2%动量
            score += 0.3 if metrics['price_momentum'] > 0 else -0.3
        
        # 成交量强度
        if metrics['volume_intensity'] > 1.5:
            score += 0.2
        elif metrics['volume_intensity'] < 0.7:
            score -= 0.2
        
        # 价格趋势
        if abs(metrics['price_trend']) > 0.001:
            score += 0.3 if metrics['price_trend'] > 0 else -0.3
        
        # tick频率
        if metrics['tick_frequency'] > 30:  # 高频交易
            score += 0.2
        
        return max(-1.0, min(1.0, score))  # 限制在[-1, 1]范围

    def _calculate_enhanced_signal_quality(self, peak_strength, valley_strength, microstructure_score):
        """计算增强的信号质量"""
        max_strength = max(peak_strength, valley_strength)
        microstructure_bonus = abs(microstructure_score) * 0.2
        
        total_score = max_strength + microstructure_bonus
        
        if total_score > 0.8:
            return 'high'
        elif total_score > 0.6:
            return 'medium'
        else:
            return 'low'
