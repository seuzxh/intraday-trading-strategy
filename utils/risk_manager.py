"""
风险管理模块
负责仓位管理、止损止盈、风险控制等
"""

import numpy as np
from datetime import datetime

class RiskManager:
    """风险管理器"""
    
    def __init__(self, max_position_ratio=0.3, stop_loss_ratio=0.05, take_profit_ratio=0.08):
        """
        初始化风险管理器
        
        Args:
            max_position_ratio: 单股最大仓位比例
            stop_loss_ratio: 止损比例
            take_profit_ratio: 止盈比例
        """
        self.max_position_ratio = max_position_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.take_profit_ratio = take_profit_ratio
        
        # 风险控制参数
        self.max_drawdown_ratio = 0.15  # 最大回撤15%
        self.min_cash_ratio = 0.1       # 最小现金比例10%
        
    def can_open_position(self, context, stock, price):
        """
        检查是否可以开仓
        
        Args:
            context: 策略上下文
            stock: 股票代码
            price: 当前价格
            
        Returns:
            bool: 是否可以开仓
        """
        # 检查现金是否充足
        available_cash = context.portfolio.cash
        total_value = context.portfolio.total_value
        cash_ratio = available_cash / total_value
        
        if cash_ratio < self.min_cash_ratio:
            return False
        
        # 检查是否超过最大仓位限制
        max_investment = total_value * self.max_position_ratio
        min_investment = max_investment * 0.1  # 最小投资金额
        
        if available_cash < min_investment:
            return False
        
        # 检查总体风险敞口
        current_positions = len([pos for pos in context.portfolio.positions 
                               if context.portfolio.positions[pos].quantity > 0])
        max_positions = 5  # 最多持有5只股票
        
        if current_positions >= max_positions:
            return False
        
        # 检查股票流动性（简化处理）
        if price <= 0:
            return False
            
        return True
    
    def calculate_buy_amount(self, context, price, signal_strength):
        """
        计算买入数量
        
        Args:
            context: 策略上下文
            price: 当前价格
            signal_strength: 信号强度(0-1)
            
        Returns:
            int: 买入股数
        """
        total_value = context.portfolio.total_value
        max_investment = total_value * self.max_position_ratio
        
        # 根据信号强度调整投资金额
        # 信号强度越高，投资金额越大
        base_ratio = 0.5  # 基础投资比例50%
        strength_bonus = 0.5 * signal_strength  # 信号强度奖励
        investment_ratio = min(base_ratio + strength_bonus, 1.0)
        
        actual_investment = max_investment * investment_ratio
        
        # 确保不超过可用现金
        available_cash = context.portfolio.cash
        actual_investment = min(actual_investment, available_cash * 0.9)
        
        # 计算股数（整手买入）
        shares = int(actual_investment / price / 100) * 100
        
        return max(shares, 0)
    
    def calculate_sell_amount(self, current_quantity, signal_strength):
        """
        计算卖出数量
        
        Args:
            current_quantity: 当前持仓数量
            signal_strength: 信号强度(0-1)
            
        Returns:
            int: 卖出股数
        """
        # 根据信号强度决定卖出比例
        base_ratio = 0.5  # 基础卖出比例50%
        strength_bonus = 0.5 * signal_strength  # 信号强度奖励
        sell_ratio = min(base_ratio + strength_bonus, 1.0)
        
        sell_amount = int(current_quantity * sell_ratio / 100) * 100
        return min(sell_amount, current_quantity)
    
    def check_exit_conditions(self, entry_price, current_price):
        """
        检查止损止盈条件
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            
        Returns:
            tuple: (是否需要平仓, 平仓原因)
        """
        if entry_price <= 0:
            return False, ""
            
        pnl_ratio = (current_price - entry_price) / entry_price
        
        # 止损检查
        if pnl_ratio <= -self.stop_loss_ratio:
            return True, f"止损平仓(亏损{pnl_ratio:.2%})"
        
        # 止盈检查
        if pnl_ratio >= self.take_profit_ratio:
            return True, f"止盈平仓(盈利{pnl_ratio:.2%})"
        
        # 移动止损（盈利超过4%后，回撤2%就止损）
        if pnl_ratio > 0.04:
            trailing_stop = pnl_ratio - 0.02
            if pnl_ratio <= trailing_stop:
                return True, f"移动止损(回撤至{pnl_ratio:.2%})"
        
        return False, ""
    
    def check_portfolio_risk(self, context):
        """
        检查组合整体风险
        
        Args:
            context: 策略上下文
            
        Returns:
            dict: 风险检查结果
        """
        portfolio = context.portfolio
        
        # 计算当前回撤
        total_value = portfolio.total_value
        starting_cash = portfolio.starting_cash
        max_value = max(total_value, starting_cash)
        current_drawdown = (max_value - total_value) / max_value
        
        # 计算仓位集中度
        positions = portfolio.positions
        position_values = [positions[stock].market_value for stock in positions 
                          if positions[stock].quantity > 0]
        
        concentration_risk = max(position_values) / total_value if position_values else 0
        
        # 计算现金比例
        cash_ratio = portfolio.cash / total_value
        
        risk_metrics = {
            'current_drawdown': current_drawdown,
            'max_drawdown_exceeded': current_drawdown > self.max_drawdown_ratio,
            'concentration_risk': concentration_risk,
            'concentration_exceeded': concentration_risk > self.max_position_ratio,
            'cash_ratio': cash_ratio,
            'cash_insufficient': cash_ratio < self.min_cash_ratio,
            'total_positions': len(position_values)
        }
        
        return risk_metrics
    
    def get_position_size_recommendation(self, context, stock, signal_strength, volatility=None):
        """
        获取仓位大小建议（基于凯利公式的改进版本）
        
        Args:
            context: 策略上下文
            stock: 股票代码
            signal_strength: 信号强度
            volatility: 股票波动率（可选）
            
        Returns:
            float: 建议仓位比例
        """
        # 基础仓位比例
        base_position = self.max_position_ratio
        
        # 根据信号强度调整
        signal_adjustment = signal_strength * 0.5
        
        # 根据波动率调整（如果提供）
        volatility_adjustment = 0
        if volatility is not None:
            # 波动率越高，仓位越小
            volatility_adjustment = -min(volatility * 2, 0.2)
        
        # 根据组合风险调整
        risk_metrics = self.check_portfolio_risk(context)
        risk_adjustment = 0
        
        if risk_metrics['current_drawdown'] > 0.05:  # 回撤超过5%
            risk_adjustment -= 0.1
        
        if risk_metrics['cash_ratio'] < 0.2:  # 现金比例低于20%
            risk_adjustment -= 0.1
        
        # 计算最终仓位比例
        recommended_position = base_position + signal_adjustment + volatility_adjustment + risk_adjustment
        
        # 确保在合理范围内
        recommended_position = max(0.05, min(recommended_position, self.max_position_ratio))
        
        return recommended_position