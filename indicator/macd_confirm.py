import pandas as pd
import pandas_ta as ta

from indicator.base import Indicator


class MACD(Indicator):
    def __init__(self, signal=1, fast=12, slow=26, signal_period=9):
        """
        MACD 确认指标

        参数:
        - signal: 1 表示确认多头，-1 表示确认空头
        - fast: 快速 EMA 周期
        - slow: 慢速 EMA 周期
        - signal_period: 信号线 EMA 周期
        """
        self.signal = signal
        self.fast = fast
        self.slow = slow
        self.signal_period = signal_period
        self.label = "MACD_D"
        self.weight = 1

    def match(self, stock, df: pd.DataFrame, trending, direction):
        """
        确认主指标有效性
        返回 True 代表主指标有效，False 代表无效
        """
        # 计算 MACD
        macd_df = ta.macd(
            close=df["close"],
            fast=self.fast,
            slow=self.slow,
            signal=self.signal_period
        )

        if macd_df is None or macd_df.empty:
            return False

        # 拆分 MACD 主线、信号线和直方图
        macd_line = macd_df.iloc[:, 0]  # MACD_12_26_9
        macd_signal = macd_df.iloc[:, 1]  # MACDs_12_26_9
        macd_hist = macd_df.iloc[:, 2]  # MACDh_12_26_9

        # 最近数据点
        last_macd = macd_line.iloc[-1]
        last_signal = macd_signal.iloc[-1]
        last_hist = macd_hist.iloc[-1]

        # 多头确认条件
        if self.signal == 1:
            # 条件1: MACD 主线在零轴上方
            # 条件2: MACD 主线在信号线上方（金叉）
            # 条件3: 直方图为正值，表示多头动量增强
            return last_macd > 0 and last_macd > last_signal and last_hist > 0

        # 空头确认条件
        if self.signal == -1:
            # 条件1: MACD 主线在零轴下方
            # 条件2: MACD 主线在信号线下方（死叉）
            # 条件3: 直方图为负值，表示空头动量增强
            return last_macd < 0 and last_macd < last_signal and last_hist < 0

        return False
