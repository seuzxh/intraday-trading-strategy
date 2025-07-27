"""
Tick数据处理器 - SuperMind直接替换版本
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict, deque

class TickDataProcessor:
    """Tick数据处理器"""
    
    def __init__(self, aggregation_seconds=3, max_cache_size=10000):
        """
        初始化Tick数据处理器
        
        Args:
            aggregation_seconds: 聚合秒数
            max_cache_size: 最大缓存大小
        """
        self.aggregation_seconds = aggregation_seconds
        self.max_cache_size = max_cache_size
        
        # 缓存结构
        self.tick_cache = defaultdict(deque)
        self.aggregated_cache = defaultdict(deque)
        self.last_update_time = {}
        
    def get_tick_data(self, stock, context, lookback_minutes=10):
        """
        获取tick数据 - 直接使用SuperMind API
        
        Args:
            stock: 股票代码
            context: 策略上下文
            lookback_minutes: 回看分钟数
            
        Returns:
            list: tick数据列表
        """
        try:
            # 计算开始时间
            end_time = context.now
            start_time = end_time - timedelta(minutes=lookback_minutes)
            
            # 直接使用替换后的get_ticks函数
            ticks = get_ticks(stock, start_time, end_time)
            
            if not ticks:
                return []
            
            # 更新缓存
            self._update_tick_cache(stock, ticks)
            
            return ticks
            
        except Exception as e:
            print(f"获取tick数据失败: {stock}, 错误: {e}")
            return []
    
    def aggregate_ticks_to_seconds(self, stock, context, length=100):
        """
        将tick数据聚合为秒级数据
        
        Args:
            stock: 股票代码
            context: 策略上下文
            length: 需要的数据长度
            
        Returns:
            dict: 包含OHLCV的秒级数据
        """
        try:
            # 检查缓存
            cache_key = f"{stock}_{self.aggregation_seconds}s"
            if (cache_key in self.last_update_time and 
                (context.now - self.last_update_time[cache_key]).total_seconds() < 1):
                return self._get_cached_aggregated_data(stock, length)
            
            # 获取tick数据
            ticks = self.get_tick_data(stock, context, lookback_minutes=15)
            if not ticks:
                return self._empty_ohlcv_data()
            
            # 聚合tick数据
            aggregated_data = self._aggregate_ticks(ticks)
            
            # 更新聚合缓存
            self._update_aggregated_cache(stock, aggregated_data)
            self.last_update_time[cache_key] = context.now
            
            # 返回指定长度的数据
            return self._get_cached_aggregated_data(stock, length)
            
        except Exception as e:
            print(f"聚合tick数据失败: {stock}, 错误: {e}")
            return self._empty_ohlcv_data()
    
    def _aggregate_ticks(self, ticks):
        """
        聚合tick数据为秒级OHLCV
        
        Args:
            ticks: tick数据列表
            
        Returns:
            list: 聚合后的秒级数据
        """
        if not ticks:
            return []
        
        # 按时间分组
        time_groups = defaultdict(list)
        
        for tick in ticks:
            # 计算聚合时间戳（向下取整到聚合秒数）
            timestamp = tick.datetime
            aggregated_timestamp = timestamp.replace(
                second=(timestamp.second // self.aggregation_seconds) * self.aggregation_seconds,
                microsecond=0
            )
            time_groups[aggregated_timestamp].append(tick)
        
        # 聚合每个时间段的数据
        aggregated_data = []
        for timestamp in sorted(time_groups.keys()):
            group_ticks = time_groups[timestamp]
            
            if not group_ticks:
                continue
            
            # 计算OHLCV
            prices = [tick.last for tick in group_ticks]
            volumes = [tick.volume for tick in group_ticks]
            
            ohlcv = {
                'datetime': timestamp,
                'open': prices[0],
                'high': max(prices),
                'low': min(prices),
                'close': prices[-1],
                'volume': sum(volumes),
                'tick_count': len(group_ticks),
                'avg_price': np.mean(prices),
                'price_std': np.std(prices) if len(prices) > 1 else 0,
                'volume_weighted_price': self._calculate_vwap(group_ticks)
            }
            
            aggregated_data.append(ohlcv)
        
        return aggregated_data
    
    def _calculate_vwap(self, ticks):
        """计算成交量加权平均价格"""
        if not ticks:
            return 0
        
        total_value = sum(tick.last * tick.volume for tick in ticks)
        total_volume = sum(tick.volume for tick in ticks)
        
        return total_value / total_volume if total_volume > 0 else ticks[-1].last
    
    def _update_tick_cache(self, stock, ticks):
        """更新tick缓存"""
        cache = self.tick_cache[stock]
        
        for tick in ticks:
            cache.append(tick)
        
        # 限制缓存大小
        while len(cache) > self.max_cache_size:
            cache.popleft()
    
    def _update_aggregated_cache(self, stock, aggregated_data):
        """更新聚合数据缓存"""
        cache = self.aggregated_cache[stock]
        
        for data in aggregated_data:
            # 避免重复添加相同时间戳的数据
            if not cache or cache[-1]['datetime'] != data['datetime']:
                cache.append(data)
        
        # 限制缓存大小
        while len(cache) > 500:  # 保留最近500个数据点
            cache.popleft()
    
    def _get_cached_aggregated_data(self, stock, length):
        """从缓存获取聚合数据"""
        cache = self.aggregated_cache[stock]
        
        if not cache:
            return self._empty_ohlcv_data()
        
        # 获取最近的数据
        recent_data = list(cache)[-length:] if len(cache) >= length else list(cache)
        
        if not recent_data:
            return self._empty_ohlcv_data()
        
        # 转换为numpy数组格式
        return {
            'datetime': [d['datetime'] for d in recent_data],
            'open': np.array([d['open'] for d in recent_data]),
            'high': np.array([d['high'] for d in recent_data]),
            'low': np.array([d['low'] for d in recent_data]),
            'close': np.array([d['close'] for d in recent_data]),
            'volume': np.array([d['volume'] for d in recent_data]),
            'tick_count': np.array([d['tick_count'] for d in recent_data]),
            'avg_price': np.array([d['avg_price'] for d in recent_data]),
            'price_std': np.array([d['price_std'] for d in recent_data]),
            'vwap': np.array([d['volume_weighted_price'] for d in recent_data])
        }
    
    def _empty_ohlcv_data(self):
        """返回空的OHLCV数据"""
        return {
            'datetime': [],
            'open': np.array([]),
            'high': np.array([]),
            'low': np.array([]),
            'close': np.array([]),
            'volume': np.array([]),
            'tick_count': np.array([]),
            'avg_price': np.array([]),
            'price_std': np.array([]),
            'vwap': np.array([])
        }
    
    def get_real_time_metrics(self, stock, context):
        """
        获取实时市场微观结构指标
        
        Args:
            stock: 股票代码
            context: 策略上下文
            
        Returns:
            dict: 实时指标
        """
        try:
            # 获取最近的tick数据
            recent_ticks = self.get_tick_data(stock, context, lookback_minutes=2)
            
            if len(recent_ticks) < 10:
                return self._empty_metrics()
            
            # 计算实时指标
            prices = [tick.last for tick in recent_ticks[-20:]]  # 最近20个tick
            volumes = [tick.volume for tick in recent_ticks[-20:]]
            
            metrics = {
                'price_momentum': self._calculate_price_momentum(prices),
                'volume_intensity': self._calculate_volume_intensity(volumes),
                'price_volatility': np.std(prices) if len(prices) > 1 else 0,
                'tick_frequency': len(recent_ticks) / 2.0,  # 每分钟tick数
                'avg_tick_size': np.mean(volumes) if volumes else 0,
                'price_trend': self._calculate_price_trend(prices),
                'volume_trend': self._calculate_volume_trend(volumes)
            }
            
            return metrics
            
        except Exception as e:
            print(f"计算实时指标失败: {stock}, 错误: {e}")
            return self._empty_metrics()
    
    def _calculate_price_momentum(self, prices):
        """计算价格动量"""
        if len(prices) < 5:
            return 0
        
        recent_change = (prices[-1] - prices[-5]) / prices[-5]
        return recent_change
    
    def _calculate_volume_intensity(self, volumes):
        """计算成交量强度"""
        if len(volumes) < 5:
            return 1.0
        
        recent_avg = np.mean(volumes[-5:])
        historical_avg = np.mean(volumes[:-5]) if len(volumes) > 5 else recent_avg
        
        return recent_avg / historical_avg if historical_avg > 0 else 1.0
    
    def _calculate_price_trend(self, prices):
        """计算价格趋势"""
        if len(prices) < 3:
            return 0
        
        # 简单线性回归斜率
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        return slope / prices[-1] if prices[-1] > 0 else 0
    
    def _calculate_volume_trend(self, volumes):
        """计算成交量趋势"""
        if len(volumes) < 3:
            return 0
        
        x = np.arange(len(volumes))
        slope = np.polyfit(x, volumes, 1)[0]
        avg_volume = np.mean(volumes)
        return slope / avg_volume if avg_volume > 0 else 0
    
    def _empty_metrics(self):
        """返回空的指标"""
        return {
            'price_momentum': 0,
            'volume_intensity': 1.0,
            'price_volatility': 0,
            'tick_frequency': 0,
            'avg_tick_size': 0,
            'price_trend': 0,
            'volume_trend': 0
        }
