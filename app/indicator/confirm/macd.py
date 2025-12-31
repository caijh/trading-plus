import pandas as pd
import pandas_ta as ta

from app.indicator.base import Indicator


class MACD(Indicator):
    def __init__(self, signal=1, fast=12, slow=26, signal_period=9, mode="trend"):
        """
        MACD 指标，可用于趋势确认或反转识别

        参数:
        - signal: 1 表示多头，-1 表示空头
        - fast: 快速 EMA 周期
        - slow: 慢速 EMA 周期
        - signal_period: 信号线 EMA 周期
        - mode: 模式
            - "trend"    用于趋势确认（跟随策略）
            - "reversal" 用于趋势反转识别（抄底/逃顶）
        """
        self.signal = signal
        self.fast = fast
        self.slow = slow
        self.signal_period = signal_period
        self.mode = mode
        self.label = f"MACD_{mode}"
        self.weight = 1

    def match(self, stock, df: pd.DataFrame, trending, direction):
        """
        返回 True 表示信号成立
        """
        # 计算 MACD
        macd_df = ta.macd(
            close=df["close"],
            fast=self.fast,
            slow=self.slow,
            signal=self.signal_period
        )

        if macd_df is None or macd_df.empty or len(macd_df) < 3:
            return False

        macd_line = macd_df.iloc[:, 0]  # DIF
        macd_signal = macd_df.iloc[:, 1]  # DEA
        macd_hist = macd_df.iloc[:, 2]  # MACD柱

        last_macd, prev_macd = macd_line.iloc[-1], macd_line.iloc[-2]
        last_signal = macd_signal.iloc[-1]
        last_hist, prev_hist = macd_hist.iloc[-1], macd_hist.iloc[-2]

        # -------- 趋势确认模式 --------
        if self.mode == "trend":
            if self.signal == 1:  # 多头确认
                return last_macd > 0 and last_macd > last_signal and last_hist > prev_hist
            if self.signal == -1:  # 空头确认
                return last_macd < 0 and last_macd < last_signal and last_hist < prev_hist

        # -------- 反转模式 --------
        if self.mode == "reversal":
            if self.signal == 1:
                # 从负转正（反转向上），或直方图由负逐步缩短
                return (prev_macd < 0 < last_macd) or (prev_hist < last_hist < 0)
            if self.signal == -1:
                # 从正转负（反转向下），或直方图由正逐步缩短
                return (prev_macd > 0 > last_macd) or (prev_hist > last_hist > 0)

        return False
