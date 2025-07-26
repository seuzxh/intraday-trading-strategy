"""
多时间框架信号融合
结合分钟级和秒级信号
"""

from datetime import datetime, timedelta

class MultiTimeframeFusion:
    """多时间框架信号融合器"""
    
    def __init__(self, minute_weight=0.7, second_weight=0.3, threshold=0.6):
        self.minute_weight = minute_weight
        self.second_weight = second_weight
        self.threshold = threshold
        self.signal_history = []
        
    def fuse_signals(self, minute_signals, second_signals, current_time):
        """
        融合分钟级和秒级信号
        
        Args:
            minute_signals: 分钟级信号
            second_signals: 秒级信号
            current_time: 当前时间
            
        Returns:
            dict: 融合后的信号
        """
        # 计算融合强度
        peak_fused_strength = (
            minute_signals['peak_strength'] * self.minute_weight +
            second_signals['peak_strength'] * self.second_weight
        )
        
        valley_fused_strength = (
            minute_signals['valley_strength'] * self.minute_weight +
            second_signals['valley_strength'] * self.second_weight
        )
        
        # 信号确认逻辑
        peak_confirmed = self._confirm_signal(
            minute_signals['peak_signal'],
            second_signals['peak_signal'],
            peak_fused_strength
        )
        
        valley_confirmed = self._confirm_signal(
            minute_signals['valley_signal'],
            second_signals['valley_signal'],
            valley_fused_strength
        )
        
        # 记录信号历史
        self._update_signal_history(
            peak_confirmed, valley_confirmed, current_time
        )
        
        return {
            'peak_signal': peak_confirmed,
            'peak_strength': peak_fused_strength,
            'valley_signal': valley_confirmed,
            'valley_strength': valley_fused_strength,
            'minute_signals': minute_signals,
            'second_signals': second_signals,
            'signal_confidence': self._calculate_confidence(
                minute_signals, second_signals
            )
        }
    
    def _confirm_signal(self, minute_signal, second_signal, fused_strength):
        """确认信号"""
        # 需要分钟级信号确认
        if not minute_signal:
            return False
        
        # 融合强度需要超过阈值
        if fused_strength < self.threshold:
            return False
        
        # 秒级信号提供额外确认
        return True
    
    def _calculate_confidence(self, minute_signals, second_signals):
        """计算信号置信度"""
        # 两个时间框架信号一致性
        peak_consistency = (
            minute_signals['peak_signal'] == second_signals['peak_signal']
        )
        valley_consistency = (
            minute_signals['valley_signal'] == second_signals['valley_signal']
        )
        
        if peak_consistency and valley_consistency:
            return 'high'
        elif peak_consistency or valley_consistency:
            return 'medium'
        else:
            return 'low'
    
    def _update_signal_history(self, peak_signal, valley_signal, current_time):
        """更新信号历史"""
        self.signal_history.append({
            'time': current_time,
            'peak_signal': peak_signal,
            'valley_signal': valley_signal
        })
        
        # 保留最近5分钟的历史
        cutoff_time = current_time - timedelta(minutes=5)
        self.signal_history = [
            s for s in self.signal_history if s['time'] > cutoff_time
        ]