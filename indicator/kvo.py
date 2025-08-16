import pandas as pd
import pandas_ta as ta

from indicator.base import Indicator


class KVO(Indicator):
    def __init__(self, signal=1, fast=34, slow=55, confirm_period=3):
        """
        KVO 确认指标

        参数:
        - signal: 1 表示确认多头，-1 表示确认空头
        - fast: 快速 EMA 周期
        - slow: 慢速 EMA 周期
        - confirm_period: 最近多少周期用于趋势确认
        """
        self.signal = signal
        self.fast = fast
        self.slow = slow
        self.confirm_period = confirm_period
        self.label = "KVO"
        self.weight = 1

    def match(self, stock, df: pd.DataFrame, trending, direction):
        """
        确认主指标有效性
        返回 True 代表主指标有效，False 代表无效
        """
        # 数据列检查
        required_cols = ["high", "low", "close", "volume"]
        if not all(col in df.columns for col in required_cols):
            return False

        # 计算 KVO 和信号线
        kvo_df = ta.kvo(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            volume=df["volume"],
            fast=self.fast,
            slow=self.slow
        )

        if kvo_df is None or kvo_df.empty:
            return False

        # 拆分主线和信号线
        kvo_line = kvo_df.iloc[:, 0]  # KVO_34_55_13
        kvo_signal = kvo_df.iloc[:, 1]  # KVOs_34_55_13
        kvo_val = kvo_line.iloc[-1]

        # 最近 confirm_period 根KVO趋势
        recent_kvo = kvo_line.tail(self.confirm_period)
        recent_signal = kvo_signal.tail(self.confirm_period)

        # 多头确认：KVO 在线上方并上升
        if self.signal == 1:
            return kvo_val > 0 and all(
                k > s for k, s in zip(recent_kvo, recent_signal)) and recent_kvo.is_monotonic_increasing

        # 空头确认：KVO 在线下方并下降
        if self.signal == -1:
            return kvo_val < 0 and all(
                k < s for k, s in zip(recent_kvo, recent_signal)) and recent_kvo.is_monotonic_decreasing

        return False
