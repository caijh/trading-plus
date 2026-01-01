import pandas_ta as ta

from app.indicator.base import Indicator


class ADL(Indicator):

    def __init__(self, signal, window=5):
        """
        初始化 ADL 对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，-1代表卖出信号。
        - window: 用于计算趋势的周期。
        """
        self.signal = signal
        self.label = 'ADL'
        self.weight = 1
        self.window = window

    def match(self, stock, df, trending, direction):
        """
        根据给定的数据判断是否满足 ADL 买入或卖出信号。

        参数:
        - stock: 股票信息。
        - df: 包含股票数据的 DataFrame。
        - trending: 股票价格趋势。
        - direction: 指示需要检测的信号方向，'UP'或'DOWN'。

        返回:
        - 如果满足信号则返回True，否则返回False。
        """
        # 检查数据是否足够计算 ADL
        if df is None or len(df) < self.window + 1:
            return False

        # 检查最新成交量
        latest_volume = float(df.iloc[-1]['volume'])
        if not latest_volume > 0:
            return False
        adl_series = ta.ad(df['high'], df['low'], df['close'], df['volume'])
        latest_adl = adl_series.iloc[-1]
        prev_adl = adl_series.iloc[-2]
        # 判断买入信号 (signal == 1)
        if self.signal == 1:
            return latest_adl > prev_adl

        # 判断卖出信号 (signal == -1)
        elif self.signal == -1:
            return latest_adl < prev_adl

        return False
