"""
数据管理模块 - SuperMind平台直接替换版本
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .tick_data_processor import TickDataProcessor

# SuperMind API导入
try:
    import ths_udata as ts
    from ths_udata import get_kline_data, get_tick_data, get_realtime_quotes
    ts.init()  # 初始化SuperMind数据接口
    SUPERMIND_AVAILABLE = True
except ImportError:
    SUPERMIND_AVAILABLE = False
    print("SuperMind API不可用，请检查安装")

def history_bars(stock, length, frequency, field):
    """
    SuperMind版本的history_bars - 直接替换米筐API
    """
    if not SUPERMIND_AVAILABLE:
        return np.array([])
    
    try:
        # 转换股票代码格式
        symbol = stock.replace('.XSHE', '.SZ').replace('.XSHG', '.SH')
        
        # 转换频率格式
        period_map = {
            '1m': '1min', '5m': '5min', '15m': '15min', 
            '30m': '30min', '1h': '60min', '1d': 'day'
        }
        period = period_map.get(frequency, '1min')
        
        # 获取K线数据
        end_date = datetime.now().strftime('%Y%m%d')
        df = get_kline_data(
            symbol=symbol,
            period=period,
            count=length,
            end_date=end_date
        )
        
        if df is None or df.empty:
            return np.array([])
        
        # 字段映射
        field_map = {
            'open': 'open', 'high': 'high', 'low': 'low',
            'close': 'close', 'volume': 'volume'
        }
        
        if field in field_map and field_map[field] in df.columns:
            return df[field_map[field]].values
        
        return np.array([])
        
    except Exception as e:
        print(f"获取历史数据失败: {stock}, {field}, 错误: {e}")
        return np.array([])

def get_ticks(stock, start_time, end_time):
    """
    SuperMind版本的get_ticks - 直接替换米筐API
    """
    if not SUPERMIND_AVAILABLE:
        return []
    
    try:
        symbol = stock.replace('.XSHE', '.SZ').replace('.XSHG', '.SH')
        
        df = get_tick_data(
            symbol=symbol,
            start_date=start_time.strftime('%Y%m%d %H:%M:%S'),
            end_date=end_time.strftime('%Y%m%d %H:%M:%S')
        )
        
        if df is None or df.empty:
            return []
        
        # 转换为tick对象
        ticks = []
        for _, row in df.iterrows():
            tick = type('Tick', (), {
                'datetime': pd.to_datetime(row['time']),
                'last': row['price'],
                'volume': row['volume']
            })()
            ticks.append(tick)
        
        return ticks
        
    except Exception as e:
        print(f"获取tick数据失败: {stock}, 错误: {e}")
        return []

class DataManager:
    """数据管理器 - SuperMind直接替换版本"""
    
    def __init__(self, cache_size=1000):
        self.cache_size = cache_size
        self.price_cache = {}
        self.volume_cache = {}
        self.indicator_cache = {}
        
        # 初始化Tick数据处理器
        self.tick_processor = TickDataProcessor(aggregation_seconds=3)
        
    def get_price_series(self, stock, context, length=50, frequency='1m'):
        """获取价格序列"""
        try:
            cache_key = f"{stock}_{frequency}_{length}"
            cache_timeout = 5 if 's' in frequency else 60
            
            if cache_key in self.price_cache:
                cached_data, cache_time = self.price_cache[cache_key]
                if (context.now - cache_time).total_seconds() < cache_timeout:
                    return cached_data
            
            # 直接使用替换后的history_bars
            prices = history_bars(stock, length, frequency, 'close')
            
            if prices is not None and len(prices) > 0:
                self.price_cache[cache_key] = (prices, context.now)
                self._clean_cache()
                return prices
            else:
                return np.array([])
                
        except Exception as e:
            print(f"获取价格数据失败: {stock}, 频率: {frequency}, 错误: {e}")
            return np.array([])
    
    def get_volume_series(self, stock, context, length=50, frequency='1m'):
        """获取成交量序列"""
        try:
            cache_key = f"{stock}_volume_{frequency}_{length}"
            cache_timeout = 5 if 's' in frequency else 60
            
            if cache_key in self.volume_cache:
                cached_data, cache_time = self.volume_cache[cache_key]
                if (context.now - cache_time).total_seconds() < cache_timeout:
                    return cached_data
            
            # 直接使用替换后的history_bars
            volumes = history_bars(stock, length, frequency, 'volume')
            
            if volumes is not None and len(volumes) > 0:
                self.volume_cache[cache_key] = (volumes, context.now)
                self._clean_cache()
                return volumes
            else:
                return np.array([])
                
        except Exception as e:
            print(f"获取成交量数据失败: {stock}, 频率: {frequency}, 错误: {e}")
            return np.array([])
    
    def get_ohlc_data(self, stock, context, length=50, frequency='1m'):
        """获取OHLC数据 - 直接替换API版本"""
        try:
            cache_key = f"{stock}_ohlc_{frequency}_{length}"
            if cache_key in self.indicator_cache:
                cached_data, cache_time = self.indicator_cache[cache_key]
                if (context.now - cache_time).total_seconds() < 60:
                    return cached_data
            
            # 直接使用替换后的history_bars获取OHLC数据
            open_prices = history_bars(stock, length, frequency, 'open')
            high_prices = history_bars(stock, length, frequency, 'high')
            low_prices = history_bars(stock, length, frequency, 'low')
            close_prices = history_bars(stock, length, frequency, 'close')
            volumes = history_bars(stock, length, frequency, 'volume')
            
            ohlc_data = {
                'open': open_prices if open_prices is not None else np.array([]),
                'high': high_prices if high_prices is not None else np.array([]),
                'low': low_prices if low_prices is not None else np.array([]),
                'close': close_prices if close_prices is not None else np.array([]),
                'volume': volumes if volumes is not None else np.array([])
            }
            
            # 检查数据完整性
            min_length = min([len(data) for data in ohlc_data.values() if len(data) > 0])
            if min_length > 0:
                for key in ohlc_data:
                    if len(ohlc_data[key]) > min_length:
                        ohlc_data[key] = ohlc_data[key][-min_length:]
                
                self.indicator_cache[cache_key] = (ohlc_data, context.now)
                self._clean_cache()
                
            return ohlc_data
            
        except Exception as e:
            print(f"获取OHLC数据失败: {stock}, 错误: {e}")
            return {
                'open': np.array([]),
                'high': np.array([]),
                'low': np.array([]),
                'close': np.array([]),
                'volume': np.array([])
            }
    
    def get_market_data(self, stocks, context, length=50):
        """
        批量获取多只股票的市场数据
        
        Args:
            stocks: 股票代码列表
            context: 策略上下文
            length: 数据长度
            
        Returns:
            dict: 股票代码为key的数据字典
        """
        market_data = {}
        
        for stock in stocks:
            try:
                ohlc_data = self.get_ohlc_data(stock, context, length)
                if len(ohlc_data['close']) > 0:
                    market_data[stock] = ohlc_data
            except Exception as e:
                print(f"获取{stock}市场数据失败: {e}")
                continue
        
        return market_data
    
    def calculate_returns(self, prices, periods=1):
        """
        计算收益率
        
        Args:
            prices: 价格序列
            periods: 计算周期
            
        Returns:
            np.array: 收益率序列
        """
        if len(prices) < periods + 1:
            return np.array([])
        
        price_series = pd.Series(prices)
        returns = price_series.pct_change(periods=periods).dropna()
        return returns.values
    
    def calculate_volatility(self, prices, window=20):
        """
        计算波动率
        
        Args:
            prices: 价格序列
            window: 计算窗口
            
        Returns:
            float: 波动率
        """
        if len(prices) < window + 1:
            return 0.0
        
        returns = self.calculate_returns(prices)
        if len(returns) < window:
            return 0.0
        
        return np.std(returns[-window:]) * np.sqrt(240)  # 年化波动率
    
    def get_relative_strength(self, stock_prices, market_prices):
        """
        计算相对强度
        
        Args:
            stock_prices: 个股价格序列
            market_prices: 市场价格序列
            
        Returns:
            float: 相对强度
        """
        if len(stock_prices) < 2 or len(market_prices) < 2:
            return 1.0
        
        stock_return = (stock_prices[-1] - stock_prices[0]) / stock_prices[0]
        market_return = (market_prices[-1] - market_prices[0]) / market_prices[0]
        
        if market_return == 0:
            return 1.0
        
        return (1 + stock_return) / (1 + market_return)
    
    def _clean_cache(self):
        """清理缓存"""
        # 简单的LRU缓存清理
        for cache in [self.price_cache, self.volume_cache, self.indicator_cache]:
            if len(cache) > self.cache_size:
                # 删除最旧的缓存项
                oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                del cache[oldest_key]
    
    def get_data_quality_score(self, data):
        """
        评估数据质量
        
        Args:
            data: 数据序列
            
        Returns:
            float: 数据质量分数(0-1)
        """
        if len(data) == 0:
            return 0.0
        
        # 检查数据完整性
        completeness = 1.0 - (np.isnan(data).sum() / len(data))
        
        # 检查数据连续性（简化处理）
        continuity = 1.0 if len(data) > 1 else 0.5
        
        # 检查数据合理性（价格应该大于0）
        validity = 1.0 if np.all(data > 0) else 0.5
        
        return (completeness + continuity + validity) / 3.0

    def get_tick_ohlcv_data(self, stock, context, length=100):
        """获取基于tick聚合的OHLCV数据 - 直接替换版本"""
        try:
            return self.tick_processor.aggregate_ticks_to_seconds(stock, context, length)
        except Exception as e:
            print(f"获取tick OHLCV数据失败: {stock}, 错误: {e}")
            return self.tick_processor._empty_ohlcv_data()
    
    def get_real_time_market_metrics(self, stock, context):
        """
        获取实时市场微观结构指标
        
        Args:
            stock: 股票代码
            context: 策略上下文
            
        Returns:
            dict: 实时市场指标
        """
        try:
            return self.tick_processor.get_real_time_metrics(stock, context)
        except Exception as e:
            print(f"获取实时市场指标失败: {stock}, 错误: {e}")
            return self.tick_processor._empty_metrics()



