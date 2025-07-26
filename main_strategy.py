"""
分时顶底交易主策略
Author: Your Name
Date: 2024-01-01
"""

from rqalpha_plus.apis import *
from indicators.peak_valley_detector import PeakValleyDetector
from indicators.second_level_detector import SecondLevelDetector
from indicators.multi_timeframe_fusion import MultiTimeframeFusion
from utils.risk_manager import RiskManager
from utils.data_manager import DataManager
from config import STRATEGY_CONFIG
import numpy as np

# 策略配置
__config__ = {
    "base": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "frequency": "1m",
        "accounts": {
            "stock": 1000000
        }
    },
    "mod": {
        "sys_simulation": {
            "enabled": True,
            "matching_type": "current_bar"
        },
        "sys_analyser": {
            "enabled": True,
            "plot": True,
            "benchmark": "000300.XSHG"
        }
    }
}

def init(context):
    """策略初始化"""
    # 股票池
    context.stocks = STRATEGY_CONFIG['STOCK_POOL']
    update_universe(context.stocks)
    
    # 初始化组件
    peak_config = STRATEGY_CONFIG['PEAK_VALLEY_CONFIG']
    context.peak_valley_detector = PeakValleyDetector(
        window_size=peak_config['window_size'],
        min_peak_height=peak_config['min_peak_height'],
        min_valley_depth=peak_config['min_valley_depth']
    )
    
    # 初始化秒级检测器
    second_config = STRATEGY_CONFIG['SECOND_LEVEL_CONFIG']
    if second_config['enabled']:
        context.second_detector = SecondLevelDetector(
            window_size=second_config['window_size'],
            min_peak_height=second_config['min_peak_height'],
            min_valley_depth=second_config['min_valley_depth']
        )
        
        # 初始化多时间框架融合器
        fusion_config = STRATEGY_CONFIG['MULTI_TIMEFRAME_CONFIG']
        context.signal_fusion = MultiTimeframeFusion(
            minute_weight=fusion_config['minute_signal_weight'],
            second_weight=fusion_config['second_signal_weight'],
            threshold=fusion_config['cross_timeframe_threshold']
        )
        
        # 秒级数据缓存
        context.second_data_cache = {}
    
    risk_config = STRATEGY_CONFIG['RISK_CONFIG']
    context.risk_manager = RiskManager(
        max_position_ratio=risk_config['max_position_ratio'],
        stop_loss_ratio=risk_config['stop_loss_ratio'],
        take_profit_ratio=risk_config['take_profit_ratio']
    )
    
    context.data_manager = DataManager()
    
    # 交易状态跟踪
    context.positions_status = {}
    context.daily_trades = 0
    context.last_signals = {}
    
    logger.info("多时间框架分时顶底交易策略初始化完成")

def before_trading(context):
    """盘前准备"""
    context.daily_trades = 0
    
    for stock in context.stocks:
        if stock not in context.positions_status:
            context.positions_status[stock] = {
                'last_peak_time': None,
                'last_valley_time': None,
                'entry_price': None,
                'signal_confirmed': False
            }

def handle_bar(context, bar_dict):
    """主要交易逻辑 - 每分钟执行"""
    current_time = context.now
    max_daily_trades = STRATEGY_CONFIG['RISK_CONFIG']['max_daily_trades']
    
    # 检查交易时间
    if not _is_trading_time(current_time):
        return
    
    # 检查日内交易次数限制
    if context.daily_trades >= max_daily_trades:
        return
    
    for stock in context.stocks:
        if stock not in bar_dict:
            continue
            
        current_bar = bar_dict[stock]
        current_price = current_bar.close
        
        # 获取分钟级历史数据
        price_data = context.data_manager.get_price_series(stock, context, 50)
        if len(price_data) < 30:
            continue
            
        # 获取分钟级信号
        minute_signals = context.peak_valley_detector.detect_signals(
            price_data, current_price, current_time
        )
        
        # 获取秒级信号（如果启用）
        final_signals = minute_signals
        if hasattr(context, 'second_detector'):
            second_signals = _get_second_level_signals(context, stock, current_price, current_time)
            if second_signals:
                final_signals = context.signal_fusion.fuse_signals(
                    minute_signals, second_signals, current_time
                )
        
        # 获取当前持仓
        position = get_position(stock)
        current_quantity = position.quantity if position else 0
        
        # 处理卖出信号（分时顶）
        if final_signals['peak_signal'] and current_quantity > 0:
            sell_amount = context.risk_manager.calculate_sell_amount(
                current_quantity, final_signals['peak_strength']
            )
            if sell_amount > 0:
                order_shares(stock, -sell_amount)
                context.daily_trades += 1
                signal_info = ""
                if 'signal_confidence' in final_signals:
                    signal_info = f", 置信度: {final_signals['signal_confidence']}"
                logger.info(f"分时顶卖出: {stock}, 数量: {sell_amount}, 价格: {current_price:.2f}, 强度: {final_signals['peak_strength']:.2f}{signal_info}")
                
        # 处理买入信号（分时底）
        elif final_signals['valley_signal'] and current_quantity == 0:
            if context.risk_manager.can_open_position(context, stock, current_price):
                buy_amount = context.risk_manager.calculate_buy_amount(
                    context, current_price, final_signals['valley_strength']
                )
                if buy_amount > 0:
                    order_shares(stock, buy_amount)
                    context.positions_status[stock]['entry_price'] = current_price
                    context.daily_trades += 1
                    signal_info = ""
                    if 'signal_confidence' in final_signals:
                        signal_info = f", 置信度: {final_signals['signal_confidence']}"
                    logger.info(f"分时底买入: {stock}, 数量: {buy_amount}, 价格: {current_price:.2f}, 强度: {final_signals['valley_strength']:.2f}{signal_info}")
        
        # 止损止盈检查
        if current_quantity > 0:
            entry_price = context.positions_status[stock]['entry_price']
            if entry_price:
                should_close, reason = context.risk_manager.check_exit_conditions(
                    entry_price, current_price
                )
                if should_close:
                    order_target_shares(stock, 0)
                    context.daily_trades += 1
                    logger.info(f"{reason}: {stock}, 入场价: {entry_price:.2f}, 当前价: {current_price:.2f}")
        
        # 更新信号记录
        context.last_signals[stock] = final_signals

def _get_second_level_signals(context, stock, current_price, current_time):
    """获取基于tick数据的秒级信号"""
    try:
        # 获取tick聚合的OHLCV数据
        tick_ohlcv = context.data_manager.get_tick_ohlcv_data(stock, context, 100)
        
        if len(tick_ohlcv['close']) < 60:
            return None
        
        # 获取实时市场微观结构指标
        real_time_metrics = context.data_manager.get_real_time_market_metrics(stock, context)
        
        # 使用tick数据进行秒级信号检测
        return context.second_detector.detect_second_signals(
            tick_ohlcv['close'], 
            current_price, 
            current_time,
            volume_series=tick_ohlcv['volume'],
            tick_ohlcv=tick_ohlcv,
            real_time_metrics=real_time_metrics
        )
        
    except Exception as e:
        logger.warning(f"获取tick级秒级信号失败: {stock}, 错误: {e}")
        return None

def after_trading(context):
    """盘后处理"""
    total_value = context.portfolio.total_value
    cash_ratio = context.portfolio.cash / total_value
    
    # 统计持仓信息
    positions_count = len([pos for pos in context.portfolio.positions if context.portfolio.positions[pos].quantity > 0])
    
    logger.info(f"收盘统计 - 总资产: {total_value:.2f}, 现金比例: {cash_ratio:.2%}, 持仓数: {positions_count}, 当日交易: {context.daily_trades}")

def _is_trading_time(current_time):
    """检查是否在交易时间内"""
    time_str = current_time.strftime('%H:%M')
    trading_config = STRATEGY_CONFIG['TRADING_TIME']
    
    # 上午交易时间
    if trading_config['start_time'] <= time_str <= trading_config['lunch_break_start']:
        return True
    
    # 下午交易时间
    if trading_config['lunch_break_end'] <= time_str <= trading_config['end_time']:
        return True
    
    return False

