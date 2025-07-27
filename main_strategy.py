"""
分时顶底交易主策略 - SuperMind直接替换版本
"""

# SuperMind交易API导入
try
    from supermind.api import *
    from supermind.api import buy, sell, get_positions, get_account
    TRADING_AVAILABLE = True
except ImportError:
    TRADING_AVAILABLE = False
    print("SuperMind交易API不可用，使用模拟模式")

from indicators.peak_valley_detector import PeakValleyDetector
from indicators.second_level_detector import SecondLevelDetector
from indicators.multi_timeframe_fusion import MultiTimeframeFusion
from utils.risk_manager import RiskManager
from utils.data_manager import DataManager
from config import STRATEGY_CONFIG
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 直接替换米筐交易API
def order_shares(stock, amount):
    """下单买卖股票 - SuperMind版本"""
    if not TRADING_AVAILABLE:
        logger.info(f"模拟下单: {stock}, 数量: {amount}")
        return
    
    try:
        # 转换股票代码格式
        symbol = stock.replace('.XSHE', '.SZ').replace('.XSHG', '.SH')
        
        if amount > 0:
            # 买入
            result = buy(symbol, amount)
            logger.info(f"买入下单: {symbol}, 数量: {amount}")
        else:
            # 卖出
            result = sell(symbol, abs(amount))
            logger.info(f"卖出下单: {symbol}, 数量: {abs(amount)}")
        
        return result
        
    except Exception as e:
        logger.error(f"下单失败: {stock}, 数量: {amount}, 错误: {e}")

def get_position(stock):
    """获取持仓信息 - SuperMind版本"""
    if not TRADING_AVAILABLE:
        return type('Position', (), {'quantity': 0, 'avg_price': 0})()
    
    try:
        symbol = stock.replace('.XSHE', '.SZ').replace('.XSHG', '.SH')
        positions = get_positions()
        
        for pos in positions:
            if pos.get('symbol') == symbol:
                return type('Position', (), {
                    'quantity': pos.get('quantity', 0),
                    'avg_price': pos.get('avg_price', 0)
                })()
        
        return type('Position', (), {'quantity': 0, 'avg_price': 0})()
        
    except Exception as e:
        logger.error(f"获取持仓失败: {stock}, 错误: {e}")
        return type('Position', (), {'quantity': 0, 'avg_price': 0})()

def get_portfolio():
    """获取组合信息 - SuperMind版本"""
    if not TRADING_AVAILABLE:
        return type('Portfolio', (), {
            'total_value': 1000000,
            'cash': 500000,
            'positions': {}
        })()
    
    try:
        account = get_account()
        return type('Portfolio', (), {
            'total_value': account.get('total_value', 1000000),
            'cash': account.get('cash', 500000),
            'positions': {}
        })()
        
    except Exception as e:
        logger.error(f"获取组合信息失败: {e}")
        return type('Portfolio', (), {
            'total_value': 1000000,
            'cash': 500000,
            'positions': {}
        })()

def init(context):
    """策略初始化"""
    try:
        logger.info("开始初始化SuperMind分时顶底交易策略...")
        
        # 股票池 - 转换为SuperMind格式
        context.stocks = [stock.replace('.XSHE', '.SZ').replace('.XSHG', '.SH') 
                         for stock in STRATEGY_CONFIG['STOCK_POOL']]
        
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
            
            fusion_config = STRATEGY_CONFIG['MULTI_TIMEFRAME_CONFIG']
            context.signal_fusion = MultiTimeframeFusion(
                minute_weight=fusion_config['minute_signal_weight'],
                second_weight=fusion_config['second_signal_weight'],
                threshold=fusion_config['cross_timeframe_threshold']
            )
        
        # 初始化风险管理器和数据管理器
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
        
        logger.info("SuperMind分时顶底交易策略初始化完成")
        
    except Exception as e:
        logger.error(f"策略初始化失败: {e}")
        raise

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
    """主要交易逻辑"""
    try:
        current_time = context.now
        
        # 检查交易时间
        if not _is_trading_time(current_time):
            return
        
        # 检查日交易次数限制
        max_daily_trades = STRATEGY_CONFIG['RISK_CONFIG']['max_daily_trades']
        if context.daily_trades >= max_daily_trades:
            return
        
        for stock in context.stocks:
            try:
                # 获取分钟级历史数据
                price_data = context.data_manager.get_price_series(stock, context, 50)
                if len(price_data) < 30:
                    continue
                
                current_price = price_data[-1] if len(price_data) > 0 else 0
                if current_price <= 0:
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
                        logger.info(f"分时顶卖出: {stock}, 数量: {sell_amount}, 价格: {current_price:.2f}")
                
                # 处理买入信号（分时底）
                elif final_signals['valley_signal'] and current_quantity == 0:
                    portfolio = get_portfolio()
                    buy_amount = context.risk_manager.calculate_buy_amount_v2(
                        portfolio, current_price, final_signals['valley_strength']
                    )
                    if buy_amount > 0:
                        order_shares(stock, buy_amount)
                        context.daily_trades += 1
                        logger.info(f"分时底买入: {stock}, 数量: {buy_amount}, 价格: {current_price:.2f}")
                
                # 检查止损止盈
                if current_quantity > 0:
                    entry_price = position.avg_price if hasattr(position, 'avg_price') else current_price
                    should_exit, reason = context.risk_manager.check_exit_conditions(entry_price, current_price)
                    if should_exit:
                        order_shares(stock, -current_quantity)
                        context.daily_trades += 1
                        logger.info(f"{reason}: {stock}, 数量: {current_quantity}, 价格: {current_price:.2f}")
                
            except Exception as e:
                logger.warning(f"处理股票{stock}时出错: {e}")
                continue
                
    except Exception as e:
        logger.error(f"主交易逻辑出错: {e}")

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



