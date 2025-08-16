import pandas as pd
import pandas_ta as ta

from indicator.base import Indicator


class RSI(Indicator):
    def __init__(self, signal=1, length=14, confirm_period=3):
        """
        RSI 确认指标

        参数:
        - signal: 1 表示确认多头，-1 表示确认空头
        - length: RSI 计算周期
        - confirm_period: 用于趋势确认的最近周期数
        """
        self.signal = signal
        self.length = length
        self.confirm_period = confirm_period
        self.label = "RSI_D"
        self.weight = 1

    def match(self, stock, df: pd.DataFrame, trending, direction):
        """
        确认主指标有效性
        返回 True 代表主指标有效，False 代表无效
        """
        # 数据列检查
        if "close" not in df.columns:
            return False

        # 计算 RSI
        rsi_line = ta.rsi(
            close=df["close"],
            length=self.length
        )

        if rsi_line is None or rsi_line.empty:
            return False

        # 获取最近的数据
        last_rsi = rsi_line.iloc[-1]

        # 获取最近 N 个周期的 RSI 趋势
        recent_rsi = rsi_line.tail(self.confirm_period)

        # 多头确认条件
        if self.signal == 1:
            # 条件1: RSI 不处于超买区（低于70），仍有上涨空间
            # 条件2: RSI 处于上升趋势，表明多头动量增强
            return last_rsi < 70 and recent_rsi.is_monotonic_increasing

        # 空头确认条件
        if self.signal == -1:
            # 条件1: RSI 不处于超卖区（高于30），仍有下跌空间
            # 条件2: RSI 处于下降趋势，表明空头动量增强
            return last_rsi > 30 and recent_rsi.is_monotonic_decreasing

        return False
