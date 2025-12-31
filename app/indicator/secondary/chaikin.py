import pandas as pd
import pandas_ta as ta

from app.indicator.base import Indicator


class Chaikin(Indicator):
    def __init__(self, signal=1, fast=3, slow=10):
        """
        Chaikin Oscillator 策略

        参数:
        - fast: 快速 EMA 周期，通常为 3
        - slow: 慢速 EMA 周期，通常为 10
        """
        self.signal = signal
        self.fast = fast
        self.slow = slow
        self.label = 'Chaikin'
        self.weight = 1

    def match(self, stock, df: pd.DataFrame, trending, direction):
        """
        根据 Chaikin 指标判断买入/卖出信号。

        参数:
        - stock: 股票代码（此例中未使用，但保留用于扩展）
        - df: 包含 high, low, close, volume 的 Pandas DataFrame
        - signal_type: 'crossover'（零轴穿越）或 'direction'（指标方向）

        返回:
        - 1: 强买入信号
        - -1: 强卖出信号
        - 0: 无明确信号
        """
        if not all(col in df for col in ['high', 'low', 'close', 'volume']):
            return 0  # 缺少必要数据，返回无信号

        # 确保数据量足够计算 Chaikin 指标
        if len(df) < self.slow:
            return 0

        # 计算 Chaikin Oscillator
        df[self.label] = ta.volume.adosc(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            volume=df['volume'],
            fast=self.fast,
            slow=self.slow
        )

        # 移除 NaN 值，确保后续判断的准确性
        df.dropna(subset=[self.label], inplace=True)
        if df.empty:
            return False

        # 获取最新的两个 Chaikin 值
        last_two_chaikin = df[self.label].iloc[-2:]
        if len(last_two_chaikin) < 2:
            return False

        current_chaikin = last_two_chaikin.iloc[1]
        previous_chaikin = last_two_chaikin.iloc[0]

        # 根据 signal_type 判断信号
        if self.signal == 1:
            # 零轴向上穿越 (买入信号)
            if previous_chaikin <= 0 < current_chaikin:
                return True
            # Chaikin 持续上升，且在零轴之上 (强买入信号)
            if current_chaikin > 0 and current_chaikin > previous_chaikin:
                return True


        elif self.signal == -1:
            # 零轴向下穿越 (卖出信号)
            if previous_chaikin >= 0 > current_chaikin:
                return True
            # Chaikin 持续下降，且在零轴之下 (强卖出信号)
            elif current_chaikin < 0 and current_chaikin < previous_chaikin:
                return True

        return False
