import pandas_ta as ta


class Chaikin:
    def __init__(self, signal=1, fast=3, slow=10):
        """
        Chaikin Oscillator 策略

        参数:
        - signal: 1 表示买入信号（Chaikin 上升），-1 表示卖出信号（Chaikin 下降）
        - fast: 快速 EMA 周期
        - slow: 慢速 EMA 周期
        """
        self.signal = signal
        self.fast = fast
        self.slow = slow
        self.label = 'Chaikin'
        self.weight = 1

    def match(self, stock, prices, df):
        """
        确认主指标有效性
        返回 True 代表主指标有效，False 代表无效
        """
        if 'high' not in df or 'low' not in df or 'close' not in df or 'volume' not in df:
            return False

        # 计算 Chaikin Oscillator
        df[self.label] = ta.volume.adosc(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            volume=df['volume'],
            fast=self.fast,
            slow=self.slow
        )

        chaikin_value = df[self.label].iloc[-1]

        if self.signal == 1:
            return chaikin_value > 0
        elif self.signal == -1:
            return chaikin_value < 0
        return False
