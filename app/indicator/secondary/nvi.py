import pandas as pd
import pandas_ta as ta

from app.indicator.base import Indicator


class NVI(Indicator):
    def __init__(self, signal):
        """
        初始化 NVI 对象。

        参数:
        - signal: 指示信号类型，1代表买入信号，其他值代表卖出信号。
        """
        self.signal = signal
        self.label = 'NVI'
        self.weight = 1

    def match(self, stock, df: pd.DataFrame, trending, direction):
        """
        根据给定的数据判断是否满足 NVI 买入或卖出信号。

        参数:
        - stock: 股票信息，未在本函数中使用。
        - df: 包含股票数据的DataFrame，包括['close'（收盘价）和 'volume'（成交量）]列。
        - trending: 股票的整体趋势（例如：强势上涨或下跌）。
        - direction: 预期交易方向，'UP'代表看涨，'DOWN'代表看跌。

        返回:
        - 如果满足买入或卖出信号则返回True，否则返回False。
        """
        # 确保数据完整性
        if not all(col in df for col in ['close', 'volume']):
            return False

        # 计算 NVI 指标，这里只使用 NVI 序列本身
        # pandas-ta 的 nvi() 函数返回一个包含 NVI 和 NVI_SMA 的 DataFrame
        nvi_series = ta.nvi(close=df['close'], volume=df['volume'])
        nvi_sma_series = ta.sma(nvi_series, length=10)

        if nvi_series is None or nvi_series.empty:
            return False

        if nvi_sma_series is None or nvi_sma_series.empty:
            return False

        last_nvi = nvi_series.iloc[-1]
        prev_nvi = nvi_series.iloc[-2]
        last_nvi_sma = nvi_sma_series.iloc[-1]
        if self.signal == 1:
            return last_nvi > prev_nvi > last_nvi_sma
        elif self.signal == -1:
            return last_nvi < prev_nvi < last_nvi_sma

        return False
