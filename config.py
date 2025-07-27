"""
策略配置文件
包含所有可调参数和设置
"""

# 策略基本配置
STRATEGY_CONFIG = {
    # 股票池配置 - 选择流动性好的大盘股
    'STOCK_POOL': [
        # 银行股
        '000001.XSHE',  # 平安银行
        '600036.XSHG',  # 招商银行
        '600000.XSHG',  # 浦发银行
        
        # 白酒股
        '600519.XSHG',  # 贵州茅台
        '000858.XSHE',  # 五粮液
        '000568.XSHE',  # 泸州老窖
        
        # 科技股
        '002415.XSHE',  # 海康威视
        '000002.XSHE',  # 万科A
        '600276.XSHG',  # 恒瑞医药
        
        # 新能源
        '300750.XSHE',  # 宁德时代
    ],
    
    # 分时顶底识别参数
    'PEAK_VALLEY_CONFIG': {
        'window_size': 20,              # 识别窗口大小
        'min_peak_height': 0.02,        # 最小顶部涨幅2%
        'min_valley_depth': 0.02,       # 最小底部跌幅2%
        'rsi_overbought': 70,           # RSI超买阈值
        'rsi_oversold': 30,             # RSI超卖阈值
        'ma_periods': [5, 10, 20],      # 移动平均线周期
        'price_deviation_threshold': 0.015,  # 价格偏离均线阈值1.5%
    },
    
    # 风险管理参数
    'RISK_CONFIG': {
        'max_position_ratio': 0.25,     # 单股最大仓位25%
        'stop_loss_ratio': 0.05,        # 止损5%
        'take_profit_ratio': 0.08,      # 止盈8%
        'trailing_stop_ratio': 0.02,    # 移动止损2%
        'max_daily_trades': 8,          # 每日最大交易次数
        'max_positions': 5,             # 最大持仓数量
        'min_cash_ratio': 0.1,          # 最小现金比例10%
        'max_drawdown_ratio': 0.15,     # 最大回撤15%
    },
    
    # 交易时间配置
    'TRADING_TIME': {
        'start_time': '09:35',          # 开始交易时间（避开开盘5分钟）
        'end_time': '14:50',            # 结束交易时间（避开收盘10分钟）
        'lunch_break_start': '11:25',   # 午休开始时间
        'lunch_break_end': '13:05',     # 午休结束时间
        'avoid_first_minutes': 5,       # 避开开盘前N分钟
        'avoid_last_minutes': 10,       # 避开收盘前N分钟
    },
    
    # 数据配置
    'DATA_CONFIG': {
        'price_history_length': 50,     # 价格历史数据长度
        'volume_history_length': 30,    # 成交量历史数据长度
        'cache_size': 1000,             # 数据缓存大小
        'data_frequency': '1m',         # 数据频率
        'min_data_quality': 0.8,       # 最小数据质量要求
    },
    
    # 信号过滤配置
    'SIGNAL_FILTER': {
        'min_signal_strength': 0.6,     # 最小信号强度
        'signal_cooldown_minutes': 5,   # 信号冷却时间（分钟）
        'volume_confirmation': True,    # 是否需要成交量确认
        'trend_confirmation': True,     # 是否需要趋势确认
        'market_filter': True,          # 是否启用市场过滤
    },
    
    # 仓位管理配置
    'POSITION_CONFIG': {
        'base_position_ratio': 0.15,    # 基础仓位比例15%
        'signal_strength_multiplier': 0.5,  # 信号强度乘数
        'volatility_adjustment': True,  # 是否根据波动率调整仓位
        'correlation_limit': 0.7,       # 相关性限制
        'sector_concentration_limit': 0.4,  # 行业集中度限制
    },
    
    # 回测配置
    'BACKTEST_CONFIG': {
        'initial_capital': 1000000,     # 初始资金100万
        'commission_rate': 0.0003,      # 手续费率0.03%
        'slippage_rate': 0.001,         # 滑点率0.1%
        'benchmark': '000300.XSHG',     # 基准指数（沪深300）
    },
    
    # 日志配置
    'LOG_CONFIG': {
        'log_level': 'INFO',            # 日志级别
        'log_trades': True,             # 是否记录交易日志
        'log_signals': True,            # 是否记录信号日志
        'log_risk_metrics': True,       # 是否记录风险指标
        'detailed_logging': False,      # 是否启用详细日志
    },
    
    # 性能优化配置
    'PERFORMANCE_CONFIG': {
        'enable_cache': True,           # 是否启用缓存
        'parallel_processing': False,   # 是否启用并行处理
        'batch_size': 10,               # 批处理大小
        'memory_limit_mb': 512,         # 内存限制（MB）
    },
    
    # 秒级监控配置
    'SECOND_LEVEL_CONFIG': {
        'enabled': True,                    # 是否启用秒级监控
        'frequency': '3s',                  # 秒级频率改为3秒
        'use_tick_data': True,              # 是否使用tick数据
        'tick_aggregation_seconds': 3,      # tick数据聚合秒数
        'window_size': 100,                 # 秒级窗口大小（相当于5分钟数据）
        'sensitivity_multiplier': 1.5,     # 敏感度倍数
        'min_peak_height': 0.003,          # 秒级最小顶部涨幅0.3%（更敏感）
        'min_valley_depth': 0.003,         # 秒级最小底部跌幅0.3%
        'rsi_period': 30,                  # 秒级RSI周期
        'ma_periods': [10, 20, 30],        # 秒级均线周期
        'signal_confirmation_seconds': 9,   # 信号确认时间（3个周期）
        'max_false_signals_per_minute': 5, # 每分钟最大假信号数（提高容忍度）
        'tick_volume_threshold': 1000,     # tick成交量阈值
        'price_change_threshold': 0.001,   # 价格变化阈值0.1%
    },
    
    # 多时间框架融合配置
    'MULTI_TIMEFRAME_CONFIG': {
        'require_minute_confirmation': True,    # 是否需要分钟级确认
        'second_signal_weight': 0.3,          # 秒级信号权重
        'minute_signal_weight': 0.7,          # 分钟级信号权重
        'signal_decay_seconds': 30,           # 信号衰减时间
        'cross_timeframe_threshold': 0.6,     # 跨时间框架信号阈值
    }
}

# 市场状态配置
MARKET_CONDITIONS = {
    'BULL_MARKET': {
        'description': '牛市',
        'peak_valley_config': {
            'min_peak_height': 0.025,    # 牛市中提高顶部识别阈值
            'min_valley_depth': 0.015,   # 降低底部识别阈值
        },
        'risk_config': {
            'max_position_ratio': 0.3,   # 牛市中可以提高仓位
            'stop_loss_ratio': 0.06,     # 适当放宽止损
        }
    },
    
    'BEAR_MARKET': {
        'description': '熊市',
        'peak_valley_config': {
            'min_peak_height': 0.015,    # 熊市中降低顶部识别阈值
            'min_valley_depth': 0.025,   # 提高底部识别阈值
        },
        'risk_config': {
            'max_position_ratio': 0.2,   # 熊市中降低仓位
            'stop_loss_ratio': 0.04,     # 收紧止损
        }
    },
    
    'SIDEWAYS_MARKET': {
        'description': '震荡市',
        'peak_valley_config': {
            'min_peak_height': 0.02,     # 使用默认参数
            'min_valley_depth': 0.02,
        },
        'risk_config': {
            'max_position_ratio': 0.25,  # 中等仓位
            'stop_loss_ratio': 0.05,     # 标准止损
        }
    }
}

# 股票分类配置
STOCK_CATEGORIES = {
    'LARGE_CAP': {
        'description': '大盘股',
        'market_cap_threshold': 100000000000,  # 1000亿市值
        'volatility_threshold': 0.3,
        'liquidity_threshold': 100000000,      # 1亿成交额
    },
    
    'GROWTH': {
        'description': '成长股',
        'pe_threshold': 30,
        'revenue_growth_threshold': 0.2,       # 20%营收增长
        'volatility_threshold': 0.4,
    },
    
    'VALUE': {
        'description': '价值股',
        'pe_threshold': 15,
        'pb_threshold': 2,
        'dividend_yield_threshold': 0.03,      # 3%股息率
    }
}

# 技术指标默认参数
TECHNICAL_INDICATORS = {
    'RSI': {
        'period': 14,
        'overbought': 70,
        'oversold': 30,
    },
    
    'MACD': {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9,
    },
    
    'BOLLINGER_BANDS': {
        'period': 20,
        'std_dev': 2,
    },
    
    'STOCHASTIC': {
        'k_period': 14,
        'd_period': 3,
        'overbought': 80,
        'oversold': 20,
    },
    
    'ATR': {
        'period': 14,
    }
}


